# reverSync: ⚡ Asynchronous Python Reverse Shell

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Rich Output](https://img.shields.io/badge/Output-Rich-6e4aff)](https://github.com/Textualize/rich)

**reverSync** is an asynchronous Python reverse shell framework for secure, authenticated, and encrypted remote command execution and system information retrieval. It features a modern, styled server console interface, multi-target management, HMAC authentication, SSL encryption, and robust communication between server and client via asyncio.

---

## 🚀 Features

- ⚡ **Asynchronous Reverse Shell:** Both server and client use Python's `asyncio` for high-performance, non-blocking communication.
- 🔒 **SSL Encryption:** All communication is secured with SSL/TLS to prevent eavesdropping.
- 🛂 **HMAC Authentication:** Implements HMAC-based challenge-response authentication for client validation.
- 💻 **Interactive Server Console:** The server features a rich terminal UI (using `rich` and `blessed`) for managing multiple targets interactively.
- 🖥️ **Multi-client Management:** Easily connect, select, and manage multiple reverse shell clients from a single console.
- 📝 **Command Execution:** Remotely execute shell commands on connected clients and view real-time output/errors.
- 📁 **File Transfer (Pull):** Securely fetch files from remote clients using the `pull` command, with base64 encoding for safe transmission.
- 🖲️ **Target System Info:** Retrieve and display system information from each connected client.
- 🛰️ **Session Management:** Easily select, view, disconnect, and stop client sessions with intuitive commands.
- ⬆️ **Persistent Command History:** Use arrow keys to navigate command history in the interactive console.
- 📂 **Directory Navigation:** Use `cd` commands to change directories on the remote client.
- 🧹 **Graceful Shutdown:** Cleanly disconnect clients and shut down the server with proper resource cleanup.
- 🛡️ **Error Handling:** Robust error messages and feedback for all commands and connection states.
- 🧩 **Extensible:** Easy to add more commands or functionality.

---

## 📦 Requirements

- 🐍 **Python 3.7+**
- **Server-side dependencies:**
  - [rich](https://pypi.org/project/rich/)
  - [blessed](https://pypi.org/project/blessed/)
  - [pyfiglet](https://pypi.org/project/pyfiglet/)
- **Client:**
  - The `client.py` file on the target/victim machine has **no external dependencies** beyond the Python standard library.

> **Note:**
> SSL certificate and key files (`cert.pem`, `key.pem`) and a password file (`pswd`) are required for the server to start.


---

## 🛠️ Setup

### 1. Clone the repository:
    ```bash
    git clone https://github.com/outisdz/reversync.git
    cd reversync
    ```
2. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3. Generate SSL certificates (if not already present):
    ```bash
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    ```
4. Create a password file named `pswd` in the root directory with your shared secret (one line, no spaces).

---

### 2. Start the Server

```bash
python server.py
```

- The server listens for incoming connections on `127.0.0.1:1234` by default.
- You will see an ASCII-art logo and an interactive shell prompt.

### 3. Start the Client(s)

On the target machine (or another terminal):

```bash
python client.py
```

- The client will attempt to connect to the server at `127.0.0.1:1234`
  (edit `SERVER_HOST` and `SERVER_PORT` in `client.py` to adjust).
- When prompted, enter the shared secret (password) used by the server.

---

## 🖥️ Server Console Commands

| 🏷️ Command                                | 📝 Description                                             |
|--------------------------------------------|------------------------------------------------------------|
| `help`                                     | Show the help menu.                                        |
| `targets`                                  | List all connected client machines.                        |
| `select <int>`                             | Switch to a different client by its index (see `targets`). |
| `stop <int>`                               | Disconnect a target by its index.                          |
| `sysinfo`                                  | Retrieve detailed system info from the target.             |
| `exit`                                     | Exit the current target session (not the server itself).   |
| `clear`                                    | Clear the console output.                                  |
| `shutdown`                                 | Disconnect all clients and shutdown the server.            |
| `pull -s <target file> -d <destination storage>` | Fetch a file from the selected client                      |
| _Any other command_                        | Will be executed remotely in the client's shell.           |

---

## 📁 File Overview

- **server.py**: Main server logic, connection management, authentication, and interactive command loop.
- **client.py**: Client logic that connects to the server, authenticates, and executes commands.
- **interactiveconsole.py**: Terminal UI and input/output handling for the server using blessed and rich.
- **targetsInfo.py**: Management and data structure for connected targets.
- **sysInfo.py**: Utility to gather system information on the client.

---

## ⚠️ Security Warning

> **Never expose this server to the public internet unless you understand the security implications.**
>
> - 🔒 **All data is sent over SSL/TLS encryption, but authentication relies on a shared secret file.**
> - 🧑‍💻 **Anyone who has your certificate and password can connect and execute commands on the client.**
> - **Always use strong, unique secrets and protect your key/password files.**

---

## 🛠️ Customization

- Change the server IP/port in both `server.py` and `client.py`.
- Add or modify commands in `server.py` and `client.py` for custom tasks.
- Adjust the ASCII logo and UI in `interactiveconsole.py` to suit your needs.

---

## 📄 License

MIT License. See `LICENSE` file for details.

---

## 👏 Credits

- [rich](https://github.com/Textualize/rich) for styled terminal output
- [blessed](https://github.com/jquast/blessed) for terminal handling
- [pyfiglet](https://github.com/pwaller/pyfiglet) for ASCII art

---

## 💻 Example Session

Server:
```
$ python server.py

 .S_sSSs      sSSs   .S    S.     sSSs   .S_sSSs
.SS~YS%%b    d%%SP  .SS    SS.   d%%SP  .SS~YS%%b
S%S   `S%b  d%S'    S%S    S%S  d%S'    S%S   `S%b
S%S    S%S  S%S     S%S    S%S  S%S     S%S    S%S
S%S    d*S  S&S     S&S    S%S  S&S     S%S    d*S
S&S   .S*S  S&S_Ss  S&S    S&S  S&S_Ss  S&S   .S*S
S&S_sdSSS   S&S~SP  S&S    S&S  S&S~SP  S&S_sdSSS
S&S~YSY%b   S&S     S&S    S&S  S&S     S&S~YSY%b
S*S   `S%b  S*b     S*b    S*S  S*b     S*S   `S%b
S*S    S%S  S*S.    S*S.   S*S  S*S.    S*S    S%S
S*S    S&S   SSSbs   SSSbs_S*S   SSSbs  S*S    S&S
S*S    SSS    YSSP    YSSP~SSS    YSSP  S*S    SSS
SP                                      SP
Y                                       Y

        sSSs   .S S.    .S_sSSs      sSSs
       d%%SP  .SS SS.  .SS~YS%%b    d%%SP
      d%S'    S%S S%S  S%S   `S%b  d%S'
      S%|     S%S S%S  S%S    S%S  S%S
      S&S     S%S S%S  S%S    S&S  S&S
      Y&Ss     SS SS   S&S    S&S  S&S
      `S&&S     S S    S&S    S&S  S&S
        `S*S    SSS    S&S    S&S  S&S
         l*S    S*S    S*S    S*S  S*b
        .S*P    S*S    S*S    S*S  S*S.
      sSS*S     S*S    S*S    S*S   SSSbs
      YSS'      S*S    S*S    SSS    YSSP
                SP     SP
                Y      Y


reversync
...

╭─ Server Output @remote-shell >  ─────────────────────────────────────────────────────╮
│ [+] Listening for incoming connections on 127.0.0.1:1234                             │
╰──────────────────────────────────────────────────────────────────────────────────────╯
╭─ Server Output @remote-shell >  ─────────────────────────────────────────────────────╮
│ Available Commands:                                                                  │
│  [+] exit                     - Exit from the current target session                 │
│  [+] sysinfo                  - Retrieve system information from the target machine  │
│  [+] targets                  - List all connected machines                          │
│  [+] select <int>             - Select a target machine by its index                 │
│  [+] clear                    - Clear the console output                             │
│  [+] help                     - Show this help menu                                  │
│  [+] shutdown                 - Shut down the server and disconnect all targets      │
│  ...                                                                                 │
╰──────────────────────────────────────────────────────────────────────────────────────╯
╭─ Server Output @remote-shell >  ─────────────────────────────────────────────────────╮
│ 1 - ('127.0.0.1', 35656)                                                             │
╰──────────────────────────────────────────────────────────────────────────────────────╯
╭─ Server Output ('127.0.0.1', 35656)@remote-shell >  ─────────────────────────────────╮
│ Current Working Directory: /home/user/reversync                                      │
│ Hostname: target-machine                                                             │
│ System Name: Linux                                                                   │
│ Release: 5.15.0-50-generic                                                           │
│ ...                                                                                  │
╰──────────────────────────────────────────────────────────────────────────────────────╯
...
```

---

## 🤝 Contributing & Feedback

> **Feel free to modify and improve this project as you like—I will read every comment and suggestion!**

---

**Enjoy hacking (ethically)!** 🚀