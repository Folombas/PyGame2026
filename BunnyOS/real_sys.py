"""Реальные данные системы — для Фейнмановского заражения."""
import os
import platform
import socket
import time
import shutil
import sys


def whoami():
    try:
        return os.getlogin()
    except Exception:
        return os.environ.get("USER", "zayka")


def hostname():
    try:
        return socket.gethostname()
    except Exception:
        return "bunnyos"


def uname_kernel():
    return platform.release()


def uname_all():
    return f"{platform.system()} {platform.node()} {platform.release()} {platform.version()} {platform.machine()}"


def date_now():
    return time.strftime("%a %b %d %H:%M:%S %Y")


def uptime_seconds():
    try:
        with open("/proc/uptime") as f:
            return float(f.read().split()[0])
    except Exception:
        return time.time() - 1700000000


def uptime_str():
    s = int(uptime_seconds())
    days = s // 86400
    hours = (s % 86400) // 3600
    mins = (s % 3600) // 60
    try:
        load1, load5, load15 = os.getloadavg()
    except Exception:
        load1 = load5 = load15 = 0.0
    return f"up {days} days, {hours:2d}:{mins:02d},  1 user,  load average: {load1:.2f}, {load5:.2f}, {load15:.2f}"


def disk_usage(path="/"):
    u = shutil.disk_usage(path)
    gb = 1024 ** 3
    return u.total / gb, u.used / gb, u.free / gb


def meminfo():
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":", 1)
                info[k.strip()] = int(v.strip().split()[0])
        total = info.get("MemTotal", 0)
        free = info.get("MemFree", 0)
        avail = info.get("MemAvailable", 0)
        return total / 1024 / 1024, free / 1024 / 1024, avail / 1024 / 1024
    except Exception:
        return 0.0, 0.0, 0.0


def cpu_model():
    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or "Unknown CPU"


def cpu_count():
    return os.cpu_count() or 1


def ip_address():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def real_cwd():
    return os.getcwd()


def ls_root():
    """Реальный список /."""
    import os
    try:
        return sorted(os.listdir("/"))
    except Exception:
        return ["bin", "boot", "dev", "etc", "home", "proc", "usr", "var"]


def ls_home():
    """Реальный список /home."""
    import os
    try:
        return sorted(os.listdir("/home"))
    except Exception:
        return ["zayka"]


def os_release():
    """Реальный /etc/os-release."""
    try:
        with open("/etc/os-release") as f:
            return f.read().strip().split("\n")
    except Exception:
        return ['PRETTY_NAME="BunnyOS 1.0 LTS"']


def real_users():
    """Реальные пользователи /etc/passwd."""
    try:
        with open("/etc/passwd") as f:
            users = []
            for line in f:
                parts = line.split(":")
                if len(parts) >= 7 and int(parts[2]) >= 1000 and int(parts[2]) < 60000:
                    users.append(parts[0])
            return users or ["zayka"]
    except Exception:
        return ["zayka"]


def who_logged_in():
    """Реальные залогиненные пользователи."""
    import subprocess
    try:
        r = subprocess.run(["who"], capture_output=True, text=True, timeout=2)
        lines = [l for l in r.stdout.strip().split("\n") if l]
        return lines or ["sasha    tty7         2026-10-17 10:00 (:0)"]
    except Exception:
        return ["sasha    tty7         2026-10-17 10:00 (:0)"]


def routing_table():
    """Реальная таблица маршрутизации."""
    import subprocess
    try:
        r = subprocess.run(["ip", "route"], capture_output=True, text=True, timeout=2)
        return r.stdout.strip().split("\n")
    except Exception:
        return ["default via 192.168.1.1 dev eth0", "192.168.1.0/24 dev eth0"]


def pci_devices():
    """Реальные PCI устройства."""
    import subprocess
    try:
        r = subprocess.run(["lspci"], capture_output=True, text=True, timeout=2)
        return r.stdout.strip().split("\n")
    except Exception:
        return ["00:00.0 Host bridge: Intel Corporation", "01:00.0 VGA: NVIDIA GTX 1060"]


def usb_devices():
    """Реальные USB устройства."""
    import subprocess
    try:
        r = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=2)
        return r.stdout.strip().split("\n")
    except Exception:
        return ["Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub"]


def real_htop():
    """Реальная нагрузка и память."""
    import os
    try:
        load = os.getloadavg()
        with open("/proc/meminfo") as f:
            info = {}
            for line in f:
                k, v = line.split(":", 1)
                info[k.strip()] = int(v.strip().split()[0])
        total = info["MemTotal"] / 1024 / 1024
        avail = info.get("MemAvailable", 0) / 1024 / 1024
        used = total - avail
        return load, total, used
    except Exception:
        return (0.0, 0.0, 0.0), 16.0, 8.0
