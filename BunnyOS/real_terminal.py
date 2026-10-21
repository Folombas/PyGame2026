"""Real terminal — настоящий bash через pty + bwrap sandbox."""
import os
import pty
import select
import shutil
import re


SANDBOX_DIR = os.path.expanduser("~/bunny_sandbox")

BLACKLIST = [
    "rm -rf /", "rm -rf /*", "rm -rf ~", "rm -rf $HOME",
    "mkfs", "dd if=/dev", "dd of=/dev",
    "sudo rm -rf", "sudo mkfs", "sudo dd",
    "chmod -R 777 /", "chown -R /",
    "shutdown", "reboot", "halt", "poweroff",
    "kill -9 -1",
]

ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def is_safe_command(cmd):
    low = cmd.lower().strip()
    for b in BLACKLIST:
        if b.lower() in low:
            return False, f"Заблокировано: '{b}'"
    return True, ""


def ensure_sandbox():
    os.makedirs(SANDBOX_DIR, exist_ok=True)
    readme = os.path.join(SANDBOX_DIR, "README.txt")
    if not os.path.exists(readme):
        try:
            with open(readme, "w") as f:
                f.write("BunnyOS Sandbox\nОстальная система read-only\n")
        except Exception:
            pass


def strip_ansi(text):
    return ANSI_RE.sub('', text)


class RealTerminal:
    def __init__(self, sandbox=True):
        self.sandbox = sandbox
        self.fd = None
        self.pid = None
        self.running = False
        self.used_bwrap = False

    def _has_bwrap(self):
        return shutil.which("bwrap") is not None

    def start(self):
        if self.running:
            return False
        ensure_sandbox()

        if self.sandbox and self._has_bwrap():
            cmd = [
                "bwrap",
                "--ro-bind", "/", "/",
                "--bind", SANDBOX_DIR, SANDBOX_DIR,
                "--proc", "/proc",
                "--dev-bind", "/dev", "/dev",
                "--tmpfs", "/tmp",
                "--unshare-pid",
                "--chdir", SANDBOX_DIR,
                "--clearenv",
                "--setenv", "PATH", "/usr/local/bin:/usr/bin:/bin",
                "--setenv", "HOME", SANDBOX_DIR,
                "--setenv", "TERM", "xterm-256color",
                "--setenv", "LANG", "C.UTF-8",
                "bash", "--norc", "--noprofile", "-i",
            ]
            self.used_bwrap = True
        else:
            cmd = ["bash", "--norc", "--noprofile", "-i"]
            self.used_bwrap = False

        try:
            pid, fd = pty.fork()
            if pid == 0:
                if not self.used_bwrap:
                    os.chdir(SANDBOX_DIR)
                env = os.environ.copy()
                if not self.used_bwrap:
                    env["PS1"] = "bunny@real:\\w$ "
                    env["HOME"] = SANDBOX_DIR
                os.execvpe(cmd[0], cmd, env)
            else:
                self.pid = pid
                self.fd = fd
                self.running = True
                try:
                    import fcntl, struct, termios
                    ws = struct.pack("HHHH", 30, 100, 0, 0)
                    fcntl.ioctl(fd, termios.TIOCSWINSZ, ws)
                except Exception:
                    pass
                return True
        except Exception as e:
            print(f"[real_term] ошибка: {e}")
            return False

    def read_output(self, timeout=0.05):
        if not self.running:
            return ""
        try:
            r, _, _ = select.select([self.fd], [], [], timeout)
            if r:
                data = os.read(self.fd, 4096)
                if not data:
                    self.running = False
                    return ""
                return data.decode("utf-8", errors="replace")
        except (OSError, IOError):
            self.running = False
        return ""

    def write(self, text):
        if not self.running:
            return False
        try:
            os.write(self.fd, text.encode("utf-8"))
            return True
        except (OSError, IOError):
            self.running = False
            return False

    def execute(self, command):
        ok, reason = is_safe_command(command)
        if not ok:
            return False, reason
        return self.write(command + "\n"), ""

    def send_ctrl_c(self):
        self.write("\x03")

    def send_ctrl_d(self):
        self.write("\x04")

    def stop(self):
        if self.pid:
            try:
                os.kill(self.pid, 15)
            except Exception:
                pass
        if self.fd is not None:
            try:
                os.close(self.fd)
            except Exception:
                pass
        self.running = False
        self.fd = None
        self.pid = None


if __name__ == "__main__":
    import time
    print("Запуск bash в pty + bwrap...")
    rt = RealTerminal(sandbox=True)
    if not rt.start():
        print("FAIL")
        exit(1)
    print(f"bwrap: {'yes' if rt.used_bwrap else 'NO'}")
    time.sleep(0.4)
    for _ in range(10):
        out = rt.read_output(0.1)
        if out:
            print(out, end="")
    print("\n--- pwd ---")
    rt.write("pwd\n")
    time.sleep(0.3)
    for _ in range(5):
        print(rt.read_output(0.1), end="")
    print("\n--- uname -a ---")
    rt.write("uname -a\n")
    time.sleep(0.3)
    for _ in range(5):
        print(rt.read_output(0.1), end="")
    print("\n--- touch test ---")
    rt.write("touch test.txt && ls\n")
    time.sleep(0.3)
    for _ in range(5):
        print(rt.read_output(0.1), end="")
    print("\n--- rm -rf / (блокируется) ---")
    ok, reason = rt.execute("rm -rf /")
    print(f"ok={ok}, reason={reason}")
    rt.stop()
