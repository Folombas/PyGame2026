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
