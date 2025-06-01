# 🌀 ReverseSync

A simple, asynchronous reverse shell implemented in Python using `asyncio`. This project consists of a server (`server.py`) and a client (`client.py`) that allow for remote command execution over a TCP connection.

> **⚠️ Disclaimer:**  
> This tool is developed strictly for educational purposes, security research, and authorized penetration testing. **Do not use it on any system or network without explicit permission.** Unauthorized use may be illegal.

---

## ✨ Features

- **Asynchronous I/O** for efficient and responsive communication.
- Interactive shell: Send commands from the server to the client and receive output in real time.
- Handles `cd` (change directory), permission errors, and command execution feedback.
- Clean shutdown on `exit` or interruption.
- Easy to configure and run.

---

## 📦 Requirements

- Python 3.7+
- The `client.py` file on the **target/victim** machine has no external dependencies and uses only the Python standard library.

---

## 🚀 Usage

### 1. Clone the repository

```bash
git clone https://github.com/outisdz/reversync.git
cd reversync
```

### 2. Start the Server

On the **attacker/controller** machine:

```bash
python3 server.py
```

- The server listens by default on `127.0.0.1:1234`.
- To use a different address or port, modify the `SERVER_HOST` and `SERVER_PORT` variables at the top of `server.py`.

### 3. Start the Client

On the **target/victim** machine (or another terminal):

```bash
python3 client.py
```

- By default, the client connects to `127.0.0.1:1234`.
- To connect to a different server, modify `SERVER_HOST` and `SERVER_PORT` in `client.py`.

### 4. Interact

- Once the client connects, the server prompt appears:
  ```
  ('127.0.0.1', 55555)@remote-shell >
  ```
- Type shell commands (e.g., `ls`, `pwd`, `cat file.txt`) and see the output.
- Use `cd <path>` to change directories on the client.
- Type `clear` to clear your server terminal.
- Type `exit` to terminate the session and shut down the server.

---

## 🖥️ Example

**Server:**
```
$ python3 server.py
[+] Listening for incoming connections on 127.0.0.1:1234
[+] Connection established from ('127.0.0.1', 54321). Type 'exit' to terminate session.
('127.0.0.1', 54321)@remote-shell > pwd
/home/user
('127.0.0.1', 54321)@remote-shell > ls
client.py
server.py
README.md
('127.0.0.1', 54321)@remote-shell > exit
[-] Closing connection and shutting down server...
[-] Shutdown signal received. Closing server...
```

**Client:**
```
$ python3 client.py
[+] Connected to reverse shell server at 127.0.0.1:1234
[>] Executing command: pwd (Current directory: /home/user)
[>] Executing command: ls (Current directory: /home/user)
[-] Connection closed by 127.0.0.1:1234
```

---

## 🔒 Security Warning

- **Never expose this server to the public internet unless you understand the security implications.**
- All data is sent in plaintext (no encryption).
- Anyone who can connect to the server can execute commands on the client.

---

> **📝 Note:**  
> In the future, I plan to add a security layer so that communication between the server and the target is encrypted, as well as to implement an additional protocol for safer and more flexible usage.  
> **Feel free to modify and improve this project as you like—I will read every comment and suggestion!**

---

## 📄 License

[MIT](LICENSE)

---

## 🎓 Educational Purposes Only

This tool is provided as-is for learning and authorized testing. The author is **not responsible for any misuse or damage** caused by this software.
