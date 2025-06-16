# reverSync: ⚡ Asynchronous Python Reverse Shell

![Reverse Shell Icon](https://img.icons8.com/ios-filled/50/000000/console.png)
**reverSync** is an asynchronous Python reverse shell framework for secure, authenticated, and encrypted remote command execution and system information retrieval. It features a modern, styled server console interface, multi-target management, HMAC authentication, SSL encryption, and robust communication between server and client via asyncio.

---

## ✨ Features

- 🐚 **Reverse Shell:** Remotely execute shell commands on connected targets.
- 🖥️ **Multi-Target Management:** Handle multiple clients, switch between them, and monitor their connection status.
- 🔒 **Encrypted Connections:** All traffic between client and server uses SSL/TLS encryption.
- 🛡️ **HMAC Authentication:** Challenge-response password authentication before accepting a client.
- 🖲️ **Interactive Server Console:** Beautiful and user-friendly terminal UI with command history, help menu, and real-time status updates using [blessed](https://pypi.org/project/blessed/) and [rich](https://pypi.org/project/rich/).
- 📝 **System Information:** On connection and upon request, the client sends detailed system info (OS, hostname, CPU, Python version, environment, etc.).
- 🧹 **Graceful Shutdown:** Cleanly disconnects all clients and shuts down with proper notifications.
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

Install requirements for the server:

```bash
pip install rich blessed pyfiglet
```

---

## 🛠️ Usage

### 1. Generate SSL Certificates and Password File

Generate a self-signed certificate and key (if you don't have them):

```bash
openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem
```

Create a password file (containing a single line with your shared secret; e.g. `pswd`):

```bash
echo -n "yourpassword" > pswd
```

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

| 🏷️ Command                 | 📝 Description                                               |
|----------------------------|-------------------------------------------------------------|
| `help`                     | Show the help menu.                                         |
| `targets`                  | List all connected client machines.                         |
| `select target <int>`      | Switch to a different client by its index (see `targets`).  |
| `stop <int>`               | Disconnect a target by its index.                           |
| `sysinfo`                  | Retrieve detailed system info from the target.              |
| `exit`                     | Exit the current target session (not the server itself).    |
| `clear`                    | Clear the console output.                                   |
| `shutdown`                 | Disconnect all clients and shutdown the server.             |
| _Any other command_        | Will be executed remotely in the client's shell.            |

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
│  [+] select target <int>      - Select a target machine by its index                 │
│  [+] clear                    - Clear the console output                             │
│  [+] help                     - Show this help menu                                  │
│  [+] shutdown                 - Shut down the server and disconnect all targets      │
│                                                                                      │
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
