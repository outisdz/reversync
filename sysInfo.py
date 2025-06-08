import os
import platform
import sys


class TargetSysInfo:
    def __init__(self):
        uname = platform.uname()
        #self.cwd = os.getcwd()
        self.hostname = uname.node or platform.node()
        self.sysname = uname.system
        self.release = uname.release
        self.version = uname.version
        self.machine = uname.machine
        self.architecture = platform.architecture()[0]
        self.python_version = sys.version.split()[0]
        self.cpu_count = os.cpu_count()
        self.environ = dict(os.environ)

    @property
    def cwd(self):
        return os.getcwd()

    def __str__(self):
        return (
            f"Current Working Directory: {self.cwd}\n"
            f"Hostname: {self.hostname}\n"
            f"System Name: {self.sysname}\n"
            f"Release: {self.release}\n"
            f"Version: {self.version}\n"
            f"Machine: {self.machine}\n"
            f"Architecture: {self.architecture}\n"
            f"Python Version: {self.python_version}\n"
            f"Logical CPU Cores: {self.cpu_count}\n"
            f"Environment Variables: {len(self.environ)} entries"
        ).encode()


if __name__ == '__main__':
    info = TargetSysInfo()
    print(info)
