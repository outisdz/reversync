# reverSync: ⚡ Asynchronous Python Reverse Shell

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/)
[![Rich Output](https://img.shields.io/badge/Output-Rich-6e4aff)](https://github.com/Textualize/rich)

**reverSync** is a modern, asynchronous Python reverse shell framework for secure, authenticated, and encrypted remote command execution and system info retrieval. It features a styled interactive server console, multi-client management, HMAC authentication, SSL encryption, and robust asyncio-powered communication.

---

## 🚀 Features

- **Async Reverse Shell:** High-performance non-blocking I/O via Python `asyncio`.
- **SSL Encryption:** All traffic protected with SSL/TLS.
- **HMAC Authentication:** Challenge-response validation for clients.
- **Rich Server Console:** Terminal UI using `rich` and `blessed`, with command history and multi-target support.
- **Multi-client Management:** Connect, select, and control several clients at once.
- **Remote Command Execution:** Run commands on any client, view real-time output and errors.
- **File Pull:** Securely fetch files from clients (base64-encoded transfer).
- **System Info:** Query and display detailed remote system data.
- **Session Management:** Switch, view, disconnect, or stop client sessions.
- **Directory Navigation:** Use `cd` to change remote directories.
- **Graceful Shutdown:** Cleanly disconnect clients and shut down the server.
- **Robust Error Handling:** Clear error messages and feedback.
- **Extensible:** Easy to add commands and extend functionality.

---

## 📦 Requirements

- **Python 3.7+**
- **Server dependencies:**
  - [`rich`](https://pypi.org/project/rich/)
  - [`blessed`](https://pypi.org/project/blessed/)
  - [`pyfiglet`](https://pypi.org/project/pyfiglet/)
- **Client:** Only the Python standard library.

**Note:**  
You must generate `cert.pem`, `key.pem` (SSL certificate/key) and create a single-line password file named `pswd` before starting the server.

---

## 🛠️ Setup

1. **Clone the repo:**
    ```bash
    git clone https://github.com/outisdz/reversync.git
    cd reversync
    ```
2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3. **Generate SSL certificates:**
    ```bash
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
    ```
4. **Create a password file:**  
   Add your shared secret (single line, no spaces) to a file named `pswd` in the root directory.

---

## 🚦 Starting

**Start the Server:**  
```bash
python server.py
```
- Defaults: listens on `127.0.0.1:1234`.
- Shows ASCII logo and interactive shell.

**Start the Client(s):**  
On the target machine (or another terminal):
```bash
python client.py
```
- Connects to `127.0.0.1:1234` (edit `SERVER_HOST` and `SERVER_PORT` in `client.py` to change).
- Enter the shared secret when prompted.

---

## 🖥️ Server Console Commands

| Command                                        | Description                                               |
|------------------------------------------------|-----------------------------------------------------------|
| `help`                                         | Show help menu                                            |
| `targets`                                      | List all connected clients                                |
| `select <int>`                                 | Select a client by index                                  |
| `stop <int>`                                   | Disconnect a client by index                              |
| `sysinfo`                                      | Get system info from target                               |
| `exit`                                         | Exit from current target session                          |
| `clear`                                        | Clear the console output                                  |
| `shutdown`                                     | Disconnect all clients and shut down server               |
| `pull -s <target file> -d <destination>`        | Download file from client                                 |
| _(any other command)_                          | Executes remotely on the client's shell                   |

---

## 📁 File Structure

- `server.py`: Main server logic, authentication, interactive command loop.
- `client.py`: Minimal client logic, shell command execution.
- `interactiveconsole.py`: Terminal UI and input/output for server.
- `targetsInfo.py`: Target management and session data.
- `sysInfo.py`: System info gathering on client.

---

## ⚠️ Security Warning

> **Never expose this server to the public internet unless you understand the risks.**
>
> - All communication is SSL/TLS encrypted, but authentication is via a shared secret.
> - Anyone with your certificate and password can run commands on your clients.
> - Use strong, unique secrets and protect your key/password files.

---

## 🛠️ Customization

- Change server IP/port in both `server.py` and `client.py`.
- Add or modify commands in `server.py` and `client.py`.
- Customize logo/UI in `interactiveconsole.py`.

---

## 📄 License

MIT License. See `LICENSE` for details.

---

## 👏 Credits

- [`rich`](https://github.com/Textualize/rich)
- [`blessed`](https://github.com/jquast/blessed)
- [`pyfiglet`](https://github.com/pwaller/pyfiglet)

---

## 💻 Example Session

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

> Suggestions and improvements welcome—feel free to open an issue or PR!

---

**Enjoy hacking (ethically)!** 🚀