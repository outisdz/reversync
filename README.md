# reverSync: ⚡ Asynchronous Python Reverse Shell

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Rich Output](https://img.shields.io/badge/Output-Rich-6e4aff)](https://github.com/Textualize/rich)

## 🔍 Overview

**reverSync** is an asynchronous Python reverse shell framework for remote command execution and system information retrieval. It features a modern, styled server console interface, multi-target management, and robust communication between server and client via asyncio.

---

## ✨ Features

- 🐚 **Reverse Shell:** Remotely execute shell commands on connected targets.
- 🖥️ **Multi-Target Management:** Handle multiple clients, switch between them, and monitor their connection status.
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
  - The `client.py` file on the target/victim machine has **no external dependencies** and uses only the Python standard library.

Install requirements for the server:

```bash
pip install rich blessed pyfiglet
```

---

## 🛠️ Usage

### 1. Start the Server

```bash
python server.py
```

- The server listens for incoming connections on `127.0.0.1:1234` by default.
- You will see an ASCII-art logo and an interactive shell prompt.

### 2. Start the Client(s)

On the target machine (or another terminal):

```bash
python client.py
```

- The client will attempt to connect to the server at `127.0.0.1:1234`  
  (edit `SERVER_HOST` and `SERVER_PORT` in `client.py` to adjust).

---

## 🖥️ Server Console Commands

| 🏷️ Command                 | 📝 Description                                               |
|----------------------------|-------------------------------------------------------------|
| `help`                     | Show the help menu.                                         |
| `targets`                  | List all connected client machines.                         |
| `select target <int>`      | Switch to a different client by its index (see `targets`).  |
| `sysinfo`                  | Retrieve detailed system info from the target.              |
| `exit`                     | Exit the current target session (not the server itself).    |
| `clear`                    | Clear the console output.                                   |
| `shutdown`                 | Disconnect all clients and shutdown the server.             |
| _Any other command_        | Will be executed remotely in the client's shell.            |

---

## 📁 File Overview

- **server.py**: Main server logic, connection management, and interactive command loop.
- **server_console.py**: Terminal UI and input/output handling for the server using blessed and rich.
- **client.py**: Client logic that connects to the server and executes commands.
- **sysinfo.py**: Utility to gather system information on the client.

---

## 🛠️ Customization

- Change the server IP/port in both `server.py` and `client.py`.
- Add or modify commands in `server.py` and `client.py` for custom tasks.
- Adjust the ASCII logo and UI in `server_console.py` to suit your needs.

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

## ⚠️ Security Warning

> **Never expose this server to the public internet unless you understand the security implications.**
>
> - 🔓 **All data is sent in plaintext (no encryption).**
> - 🧑‍💻 **Anyone who can connect to the server can execute commands on the client.**

---

> 📝 **Note:**  
> In the future, I plan to add a security layer so that communication between the server and the target is encrypted, as well as to implement an additional protocol for safer and more flexible usage.  
> **Feel free to modify and improve this project as you like—I will read every comment and suggestion!**

---

**Enjoy hacking (ethically)!** 🚀
