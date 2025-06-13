from dataclasses import dataclass


@dataclass
class TargetInfo:
    address: str
    hostname: str = ''
    cwd: str = ''
    username: str = ''

class Targets:
    def __init__(self):
        self.connections = {}
        self.current_target = ''
        self.info = {}

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

    def get_target_address(self, i=0):
        if list(self.connections):
            return list(self.connections)[i]
        return ''

    @property
    def current_address(self):
        """Returns the currently selected client address."""
        return self.current_target

    @property
    def cwd(self):
        try:
            return self.info[self.current_address].cwd
        except KeyError:
            return ''
    @property
    def username(self):
        try:
            return self.info[self.current_address].username
        except KeyError:
            return ''
    @property
    def hostname(self):
        try:
            return self.info[self.current_address].hostname
        except KeyError:
            return ''

    @property
    def prompt(self):
        if f"{self.username}{self.hostname}".strip():
            return f"{self.username}@{self.hostname}@{self.cwd} > "
        return "@remote-shell > "