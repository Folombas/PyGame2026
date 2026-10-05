"""Симулятор Linux: файловая система + shell-команды."""
import time


class LinuxSim:
    def __init__(self, user="zayka", host="bunnyos"):
        self.user = user
        self.host = host
        self.cwd = "/home/zayka"
        self.history = []
        # Виртуальная файловая система: пути → содержимое (str для файла, dict для папки)
        self.fs = {
            "/": {"type": "dir", "children": ["home", "etc", "var", "usr", "bin", "tmp"]},
            "/home": {"type": "dir", "children": ["zayka"]},
            "/home/zayka": {"type": "dir", "children": ["Documents", "projects", "README.txt", "secret.enc", ".bashrc"]},
            "/home/zayka/Documents": {"type": "dir", "children": ["notes.txt", "diary.txt"]},
            "/home/zayka/projects": {"type": "dir", "children": ["hack.py", "morph.py"]},
            "/etc": {"type": "dir", "children": ["passwd", "hosts", "motd", "os-release"]},
            "/var": {"type": "dir", "children": ["log"]},
            "/var/log": {"type": "dir", "children": ["syslog", "auth.log"]},
            "/usr": {"type": "dir", "children": ["bin", "share"]},
            "/usr/bin": {"type": "dir", "children": []},
            "/usr/share": {"type": "dir", "children": []},
            "/bin": {"type": "dir", "children": []},
            "/tmp": {"type": "dir", "children": []},
            # файлы
            "/home/zayka/README.txt": {"type": "file", "content":
                "Зайка — Белый Хакер.\nЭтот мир — симуляция на ядре Carrot Linux.\nТы можешь всё."},
            "/home/zayka/secret.enc": {"type": "file", "content":
                "[encrypted blob]\nне читается без ключа... а ключ у тебя в сердце 💚"},
            "/home/zayka/.bashrc": {"type": "file", "content":
                "# .bashrc\nalias ll='ls -la'\nexport PS1='\\u@\\h:\\w$ '"},
            "/home/zayka/Documents/notes.txt": {"type": "file", "content":
                "Понедельник — полить морковь.\nВторник — проверить капусту.\nСреда — взломать матрицу."},
            "/home/zayka/Documents/diary.txt": {"type": "file", "content":
                "День 1. Нашёл странный сигнал из восточного озера.\nДень 2. Строю нейросеть-помощника.\nДень 3. Всё идёт по плану."},
            "/home/zayka/projects/hack.py": {"type": "file", "content":
                "import neural_net\n\ndef hack_world():\n    while True:\n        neural_net.learn()\n        world.improve()"},
            "/home/zayka/projects/morph.py": {"type": "file", "content":
                "# Проект Морфо\n# Трансформация зайки в цифровой код\nmorph(target='rabbit', ascii='0x1F407')"},
            "/etc/passwd": {"type": "file", "content":
                "root:x:0:0:root:/root:/bin/bash\nzayka:x:1000:1000:Zayka:/home/zayka:/bin/bash"},
            "/etc/hosts": {"type": "file", "content":
                "127.0.0.1   localhost\n127.0.1.1   bunnyos\n10.0.0.1    gateway.carrot"},
            "/etc/motd": {"type": "file", "content":
                "Добро пожаловать в BunnyOS!\nУдачи, Зайка-хакер."},
            "/etc/os-release": {"type": "file", "content":
                'NAME="BunnyOS"\nVERSION="1.0 LTS (White Hacker)"\nID=carrot\nID_LIKE=debian'},
            "/var/log/syslog": {"type": "file", "content":
                "10:22:01 kernel: Carrot Linux 5.15.0 boot OK\n10:22:03 bunnyos: services started"},
            "/var/log/auth.log": {"type": "file", "content":
                "10:22:15 sshd: connection from 10.0.0.42\n10:22:16 sshd: failed password for root"},
        }
        self.start_time = time.time()

    def complete(self, text):
        """Автодополнение по Tab.
        Возвращает (completed_text, options_list).
        - Если совпадение одно — подставляет его.
        - Если несколько — подставляет общий префикс + возвращает список.
        """
        if not text:
            # Пустой ввод — показываем все команды
            return text, ["help", "ls", "cd", "pwd", "cat", "htop", "neofetch",
                          "clear", "exit", "man", "history", "tree"]
        parts = text.split()
        if not parts:
            return text, []

        last = parts[-1]
        all_cmds = ["help", "ls", "cd", "pwd", "cat", "echo", "whoami",
                    "uname", "date", "uptime", "clear", "history", "neofetch",
                    "tree", "touch", "mkdir", "rm", "cp", "mv", "grep",
                    "head", "tail", "wc", "man", "ps", "top", "ip", "ifconfig",
                    "ping", "curl", "sudo", "exit", "python", "python3",
                    "neural", "htop", "df", "free", "who", "id", "hostname",
                    "lsblk", "lscpu"]

        matches = []

        if len(parts) == 1:
            # Первое слово — только команды
            matches = [c for c in all_cmds if c.startswith(last)]
        else:
            # Дополняем путь (относительный или абсолютный)
            # Если last содержит "/" — берём часть до "/" как папку
            if "/" in last:
                dir_part, prefix = last.rsplit("/", 1)
                search_dir = self._normalize(self._abs_path(dir_part + "/")) if dir_part else self.cwd
            elif last.startswith("/"):
                search_dir = "/"
                prefix = last[1:]
            else:
                search_dir = self.cwd
                prefix = last

            # Собираем детей каталога
            if self._is_dir(search_dir):
                for c in self.fs[search_dir]["children"]:
                    if c.startswith(prefix) and not c.startswith("."):
                        full = search_dir.rstrip("/") + "/" + c
                        is_dir = self._is_dir(full)
                        # Показываем только имя (или имя/ для папок)
                        display = c + ("/" if is_dir else "")
                        # Если был путь с / — добавляем обратно
                        if "/" in last:
                            display = last.rsplit("/", 1)[0] + "/" + display
                        matches.append(display)

            # Плюс опции команд (--help и т.п.)
            if not matches:
                for c in all_cmds:
                    if c.startswith(last):
                        matches.append(c)

        if not matches:
            return text, []
        if len(matches) == 1:
            prefix_str = " ".join(parts[:-1])
            completed = (prefix_str + " " + matches[0]) if prefix_str else matches[0]
            return completed, []
        # Несколько — общий префикс
        common = matches[0]
        for m in matches[1:]:
            while not m.startswith(common):
                common = common[:-1]
                if not common:
                    break
        prefix_str = " ".join(parts[:-1])
        completed = (prefix_str + " " + common) if prefix_str else common
        return completed, matches

    def prompt(self):
        # ~/ вместо /home/zayka
        cwd = self.cwd
        if cwd.startswith("/home/" + self.user):
            cwd = "~" + cwd[len("/home/" + self.user):]
        return f"{self.user}@{self.host}:{cwd}$ "

    # ============== FS HELPERS ==============
    def _abs_path(self, path):
        if not path:
            return self.cwd
        if path == "~":
            return "/home/" + self.user
        if path.startswith("~/"):
            return "/home/" + self.user + path[1:]
        if path.startswith("/"):
            return path
        # relative
        if self.cwd == "/":
            return "/" + path
        return self.cwd + "/" + path

    def _normalize(self, path):
        parts = []
        for p in path.split("/"):
            if p in ("", "."):
                continue
            if p == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(p)
        return "/" + "/".join(parts) if parts else "/"

    def _exists(self, path):
        return path in self.fs

    def _is_dir(self, path):
        return path in self.fs and self.fs[path]["type"] == "dir"

    def _is_file(self, path):
        return path in self.fs and self.fs[path]["type"] == "file"

    def _ls_path(self, path, show_all=False):
        if not self._is_dir(path):
            return []
        children = self.fs[path]["children"]
        return sorted(children)

    # ============== COMMANDS ==============
    def run(self, line):
        """Возвращает список строк вывода."""
        line = line.strip()
        self.history.append(line)
        if not line:
            return []

        # pipe support? нет, простой разбор
        parts = line.split()
        cmd = parts[0]
        args = parts[1:]

        try:
            return self._dispatch(cmd, args)
        except Exception as e:
            return [f"bash: {cmd}: ошибка: {e}"]

    def _dispatch(self, cmd, args):
        if cmd == "help":
            return [
                "BunnyOS Shell · Carrot Linux — доступные команды:",
                "",
                "  help                — эта справка",
                "  ls [-la] [путь]     — список файлов",
                "  cd <путь>           — перейти в папку",
                "  pwd                 — текущая папка",
                "  cat <файл>          — показать файл",
                "  echo <текст>        — вывести текст",
                "  whoami              — имя пользователя",
                "  uname [-a]          — сведения о системе",
                "  date                — дата и время",
                "  uptime              — время работы",
                "  clear               — очистить экран",
                "  history             — история команд",
                "  neofetch            — красивая сводка",
                "  tree [путь]         — дерево папок",
                "  touch <файл>        — создать пустой файл",
                "  mkdir <папка>       — создать папку",
                "  rm [-r] <путь>      — удалить",
                "  cp <откуда> <куда>  — копировать",
                "  mv <откуда> <куда>  — переместить/переименовать",
                "  grep <паттерн> <ф>  — поиск в файле",
                "  head/tail <файл>    — начало/конец файла",
                "  wc <файл>           — число строк/слов",
                "  man <команда>       — краткая справка",
                "  ps                  — процессы",
                "  top                 — монитор ресурсов",
                "  ip a / ifconfig     — сеть",
                "  ping <хост>         — проверка связи",
                "  curl <url>          — запрос по сети",
                "  sudo <команда>      — суперпользователь",
                "  python / python3    — Python-интерпретатор (симуляция)",
                "  neural              — нейросеть Зайки",
                "  exit                — выход из сессии",
                "",
                "💡 Подсказка: Tab — автодополнение команд и файлов.",
            ]

        if cmd == "ls":
            show_all = "-a" in args or "-la" in args or "-al" in args
            long_fmt = any(a.startswith("-") and "l" in a for a in args)
            path_args = [a for a in args if not a.startswith("-")]
            path = self._normalize(self._abs_path(path_args[0] if path_args else ""))
            if not self._exists(path):
                return [f"ls: {path}: нет такого файла или папки"]
            if self._is_file(path):
                return [path.split("/")[-1]]
            children = self._ls_path(path, show_all)
            if not show_all:
                children = [c for c in children if not c.startswith(".")]
            if long_fmt:
                out = [f"total {len(children)}"]
                for c in children:
                    full = path.rstrip("/") + "/" + c
                    if self._is_dir(full):
                        out.append(f"drwxr-xr-x 2 {self.user} {self.user} 4096  {c}/")
                    else:
                        content = self.fs.get(full, {}).get("content", "")
                        size = len(content)
                        out.append(f"-rw-r--r-- 1 {self.user} {self.user} {size:>4}  {c}")
                return out
            return ["  ".join(children)]

        if cmd == "cd":
            if not args:
                self.cwd = "/home/" + self.user
                return []
            target = self._normalize(self._abs_path(args[0]))
            if not self._exists(target):
                return [f"cd: {target}: нет такой папки"]
            if not self._is_dir(target):
                return [f"cd: {target}: это файл"]
            self.cwd = target
            return []

        if cmd == "pwd":
            return [self.cwd]

        if cmd == "cat":
            if not args:
                return ["cat: не указан файл"]
            out = []
            for fn in args:
                target = self._normalize(self._abs_path(fn))
                if not self._exists(target):
                    out.append(f"cat: {fn}: нет такого файла")
                elif self._is_dir(target):
                    out.append(f"cat: {fn}: это папка")
                else:
                    out.extend(self.fs[target]["content"].split("\n"))
            return out

        if cmd == "echo":
            return [" ".join(args)]

        if cmd == "whoami":
            return [self.user]

        if cmd == "uname":
            if "-a" in args:
                return [f"Linux {self.host} 5.15.0-carrot #1 SMP x86_64 GNU/Linux"]
            return ["Linux"]

        if cmd == "date":
            return [time.strftime("%a %b %d %H:%M:%S %Y")]

        if cmd == "uptime":
            secs = int(time.time() - self.start_time)
            m = secs // 60
            s = secs % 60
            return [f"up {m}m {s}s, 1 user, load average: 0.13, 0.20, 0.18"]

        if cmd == "clear":
            return ["__CLEAR__"]

        if cmd == "history":
            return [f"  {i+1:>3}  {h}" for i, h in enumerate(self.history)]

        if cmd == "neofetch":
            # ASCII-логотип зайца с морковкой
            logo = [
                "      /\\   /\\      ",
                "     /  \\ /  \\     ",
                "    |    \\    |    ",
                "    |  o  o  |     ",
                "    |    <   |      ",
                "    |  \\_/   |     ",
                "     \\_____/      ",
                "     /|    |\\      ",
                "    / |    | \\     ",
                "   *  |____|  *    ",
                "      /    \\      ",
                "     /      \\     ",
            ]
            info = [
                f"{self.user}@{self.host}",
                "─" * 24,
                "OS:       BunnyOS 1.0 LTS",
                "Kernel:   Carrot 5.15.0-x86_64",
                "Shell:    bash 5.2.15",
                "DE:       Luna Desktop",
                "CPU:      BunnyCore i7 (8) @ 3.4GHz",
                "GPU:      CarrotRadeon RX 666",
                "Memory:   8.2GiB / 16GiB",
                "Disk:     13.7GiB / 256GiB",
                "Uptime:   just booted",
                "Packages: 1337 (dpkg), 12 (pip)",
                "Terminal: bunny-term",
                "",
                "🖥  🖥  🖥  🖥  🖥  🖥  🖥  🖥",
            ]
            # Склеиваем логотип и информацию
            result = []
            max_lines = max(len(logo), len(info))
            for i in range(max_lines):
                left = logo[i] if i < len(logo) else " " * 22
                right = info[i] if i < len(info) else ""
                result.append(f"{left}  {right}")
            return result

        if cmd == "tree":
            path = self._normalize(self._abs_path(args[0] if args else ""))
            if not self._is_dir(path):
                return [f"tree: {path}: не папка"]
            return self._tree_lines(path)

        if cmd == "touch":
            if not args:
                return ["touch: не указано имя файла"]
            target = self._normalize(self._abs_path(args[0]))
            if not self._exists(target):
                parent = "/".join(target.split("/")[:-1]) or "/"
                name = target.split("/")[-1]
                if self._is_dir(parent):
                    self.fs[target] = {"type": "file", "content": ""}
                    self.fs[parent]["children"].append(name)
            return []

        if cmd == "mkdir":
            if not args:
                return ["mkdir: не указано имя"]
            target = self._normalize(self._abs_path(args[0]))
            parent = "/".join(target.split("/")[:-1]) or "/"
            name = target.split("/")[-1]
            if self._exists(target):
                return [f"mkdir: {name}: уже существует"]
            if not self._is_dir(parent):
                return [f"mkdir: {parent}: нет такой папки"]
            self.fs[target] = {"type": "dir", "children": []}
            self.fs[parent]["children"].append(name)
            return []

        if cmd == "rm":
            if not args:
                return ["rm: не указан файл"]
            recursive = "-r" in args or "-rf" in args
            files = [a for a in args if not a.startswith("-")]
            for fn in files:
                target = self._normalize(self._abs_path(fn))
                if not self._exists(target):
                    return [f"rm: {fn}: нет такого файла"]
                if self._is_dir(target) and not recursive:
                    return [f"rm: {fn}: это папка (используйте -r)"]
                parent = "/".join(target.split("/")[:-1]) or "/"
                name = target.split("/")[-1]
                if name in self.fs[parent]["children"]:
                    self.fs[parent]["children"].remove(name)
                self._remove_recursive(target)
            return []

        if cmd == "cp":
            if len(args) < 2:
                return ["cp: нужно указать источник и цель"]
            src = self._normalize(self._abs_path(args[0]))
            dst = self._normalize(self._abs_path(args[1]))
            if not self._is_file(src):
                return [f"cp: {args[0]}: не файл"]
            self.fs[dst] = {"type": "file", "content": self.fs[src]["content"]}
            parent = "/".join(dst.split("/")[:-1]) or "/"
            name = dst.split("/")[-1]
            if self._is_dir(parent) and name not in self.fs[parent]["children"]:
                self.fs[parent]["children"].append(name)
            return []

        if cmd == "mv":
            if len(args) < 2:
                return ["mv: нужно указать источник и цель"]
            src = self._normalize(self._abs_path(args[0]))
            dst = self._normalize(self._abs_path(args[1]))
            if not self._exists(src):
                return [f"mv: {args[0]}: нет такого файла"]
            # удаляем из старой parent
            old_parent = "/".join(src.split("/")[:-1]) or "/"
            old_name = src.split("/")[-1]
            if old_name in self.fs[old_parent]["children"]:
                self.fs[old_parent]["children"].remove(old_name)
            # перемещаем
            self.fs[dst] = self.fs[src]
            del self.fs[src]
            new_parent = "/".join(dst.split("/")[:-1]) or "/"
            new_name = dst.split("/")[-1]
            if self._is_dir(new_parent):
                self.fs[new_parent]["children"].append(new_name)
            return []

        if cmd == "grep":
            if len(args) < 2:
                return ["grep: нужно указать паттерн и файл"]
            pat = args[0]
            fn = args[1]
            target = self._normalize(self._abs_path(fn))
            if not self._is_file(target):
                return [f"grep: {fn}: нет такого файла"]
            out = []
            for line in self.fs[target]["content"].split("\n"):
                if pat.lower() in line.lower():
                    out.append(line)
            return out if out else []

        if cmd == "head":
            if not args:
                return ["head: не указан файл"]
            n = 10
            target = self._normalize(self._abs_path(args[-1]))
            if not self._is_file(target):
                return [f"head: {args[-1]}: нет файла"]
            return self.fs[target]["content"].split("\n")[:n]

        if cmd == "tail":
            if not args:
                return ["tail: не указан файл"]
            n = 10
            target = self._normalize(self._abs_path(args[-1]))
            if not self._is_file(target):
                return [f"tail: {args[-1]}: нет файла"]
            return self.fs[target]["content"].split("\n")[-n:]

        if cmd == "wc":
            if not args:
                return ["wc: не указан файл"]
            target = self._normalize(self._abs_path(args[-1]))
            if not self._is_file(target):
                return [f"wc: {args[-1]}: нет файла"]
            content = self.fs[target]["content"]
            lines = content.count("\n") + (1 if content else 0)
            words = len(content.split())
            chars = len(content)
            return [f"  {lines}  {words}  {chars}  {args[-1]}"]

        if cmd == "man":
            if not args:
                return ["Что показать? Введи 'man <команда>'"]
            cmd_name = args[0]
            m = {
                "ls": "ls [ОПЦИИ] [ПУТЬ] — список содержимого каталога.",
                "cd": "cd ПУТЬ — переход в каталог.",
                "pwd": "pwd — показать текущий каталог.",
                "cat": "cat ФАЙЛ — вывести содержимое файла.",
                "grep": "grep ПАТТЕРН ФАЙЛ — поиск строк.",
                "mkdir": "mkdir ИМЯ — создать каталог.",
                "rm": "rm [-r] ПУТЬ — удалить файл/каталог.",
                "cp": "cp ИСТОЧНИК ЦЕЛЬ — копировать.",
                "mv": "mv ИСТОЧНИК ЦЕЛЬ — переместить.",
                "neofetch": "neofetch — сводка о системе.",
            }
            return [m.get(cmd_name, f"man: раздел для '{cmd_name}' не найден.")]

        if cmd == "ps":
            return [
                "  PID TTY          TIME CMD",
                "    1 ?        00:00:02 init",
                "  102 ?        00:00:05 bunny_daemon",
                "  233 ?        00:00:01 neural_net",
                f"  {450} pts/0    00:00:00 bash",
                "  512 pts/0    00:00:00 ps",
            ]

        if cmd == "top":
            return [
                "Tasks: 5 total, 1 running",
                "Mem : 8.2G used / 16G total",
                "Swap: 0K used / 4G total",
                "",
                "  PID  USER  %CPU  %MEM  COMMAND",
                "  233  root  12.3   4.1  neural_net",
                "  102  root   2.1   1.8  bunny_daemon",
                "    1  root   0.0   0.3  init",
                f"  {450}  {self.user}   0.5   0.8  bash",
            ]

        if cmd == "ip" or cmd == "ifconfig":
            return [
                "1: lo: <LOOPBACK,UP> mtu 65536",
                "    inet 127.0.0.1/8 scope host lo",
                "2: eth0: <BROADCAST,MULTICAST,UP> mtu 1500",
                "    inet 10.0.0.42/24 brd 10.0.0.255 scope global eth0",
                "3: wlan0: <UP> mtu 1500",
                "    inet 192.168.1.77/24",
            ]

        if cmd == "ping":
            if not args:
                return ["ping: укажи хост"]
            h = args[0]
            return [
                f"PING {h} (10.0.0.1) 56(84) bytes of data.",
                f"64 bytes from {h}: icmp_seq=1 ttl=64 time=0.42 ms",
                f"64 bytes from {h}: icmp_seq=2 ttl=64 time=0.38 ms",
                f"--- {h} ping statistics ---",
                "2 packets transmitted, 2 received, 0% packet loss",
            ]

        if cmd == "curl":
            if not args:
                return ["curl: укажи URL"]
            u = args[0]
            if "bunny" in u or "carrot" in u:
                return ["<html><body>Соединение защищено. Добро пожаловать, Зайка.</body></html>"]
            return [f"curl: не удалось подключиться к {u}"]

        if cmd == "sudo":
            if not args:
                return ["usage: sudo <команда>"]
            # Просто выполняем команду от root
            return [f"[sudo] running as root: {' '.join(args)}",
                    f"(команда '{args[0]}' выполнена с правами root)"]
        if cmd == "su":
            return ["su: введите пароль root:",
                    "su: Authentication failure",
                    "(попробуй 'sudo bash' — но пароль надо найти)"]

        if cmd in ("python", "python3", "python3.12", "py"):
            return [
                "Python 3.12.3 (main, BunnyOS 1.0) [GCC 11.4.0] on carrot-linux",
                'Type "help", "copyright", "credits" for more info.',
                "",
                ">>> (интерактивный Python доступен в beta)",
                ">>> import neural_net",
                ">>> neural_net.status()",
                "'все системы работают'",
                ">>> ",
            ]
        if cmd == "neural":
            return [
                "🧠 NeuralNet v0.3 (бета)",
                "━━━━━━━━━━━━━━━━━━━━━━━━━━",
                "Модель:    CarrotGPT-1B",
                "Обучение:  62%",
                "Запросов:  1 234",
                "Статус:    ✅ онлайн",
                "Лог:       учусь понимать морковь...",
            ]
        if cmd == "htop":
            return [
                "  CPU[|||||||||||||||||||||95.3%]   Tasks: 47, 183 thr; 3 running",
                "  Mem[||||||||||||||     6.4G/16G]   Load average: 0.42 0.51 0.48",
                "  Swp[                   0K/4.00G]   Uptime: 00:00:03",
                "",
                "  PID USER      PRI  NI  VIRT   RES  S CPU%  MEM%   TIME+  Command",
                "  233 root       20   0  512M  128M  S 12.3   4.1  0:00.42 neural_net",
                "  102 root       20   0  256M   64M  S  2.1   1.8  0:00.11 bunny_daemon",
                "    1 root       20   0  128M   32M  S  0.0   0.3  0:00.02 init",
                "  450 zayka      20   0   64M   16M  R  0.5   0.8  0:00.00 htop",
                "  451 zayka      20   0   48M   12M  S  0.0   0.4  0:00.00 bash",
                "",
                "  F1Help  F2Setup  F3Search  F4Filter  F5Tree  F6SortBy  F10Quit",
            ]

        if cmd == "df":
            return [
                "Filesystem      Size  Used Avail Use% Mounted on",
                "udev            7.8G     0  7.8G   0% /dev",
                "tmpfs           1.6G  1.8M  1.6G   1% /run",
                "/dev/nvme0n1p2  256G   14G  230G   6% /",
                "tmpfs           7.8G     0  7.8G   0% /dev/shm",
                "/dev/nvme0n1p1  511M  5.3M  506M   2% /boot/efi",
            ]

        if cmd == "free":
            return [
                "               total        used        free      shared  buff/cache",
                "Mem:            15Gi       6.4Gi       1.2Gi       128Mi       7.8Gi",
                "Swap:          4.0Gi          0B       4.0Gi",
            ]

        if cmd == "who":
            return [
                f"{self.user}   pts/0        2026-10-06 09:15 (:0)",
                f"{self.user}   tty1         2026-10-06 09:00",
            ]

        if cmd == "id":
            return [f"uid=1000({self.user}) gid=1000({self.user}) groups=1000({self.user}),27(sudo),999(carrot)"]

        if cmd == "uname":
            if "-a" in args:
                return [f"Linux {self.host} 5.15.0-carrot #1 SMP PREEMPT_DYNAMIC x86_64 GNU/Linux"]
            if "-r" in args:
                return ["5.15.0-carrot"]
            if "-m" in args:
                return ["x86_64"]
            if "-n" in args:
                return [self.host]
            return ["Linux"]

        if cmd == "hostname":
            return [self.host]

        if cmd == "uptime":
            import time
            secs = int(time.time() - self.start_time)
            m = secs // 60
            s = secs % 60
            return [f" 09:15:23 up {m} min,  1 user,  load average: 0.42, 0.51, 0.48"]

        if cmd == "lsblk":
            return [
                "NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINT",
                "nvme0n1     259:0    0 238.5G  0 disk",
                "├─nvme0n1p1 259:1    0   512M  0 part /boot/efi",
                "├─nvme0n1p2 259:2    0 237.5G  0 part /",
                "└─nvme0n1p3 259:3    0   512M  0 part [SWAP]",
            ]

        if cmd == "lscpu":
            return [
                "Architecture:            x86_64",
                "  CPU op-mode(s):        32-bit, 64-bit",
                "  Byte Order:            Little Endian",
                "CPU(s):                  8",
                "  On-line CPU(s) list:   0-7",
                "Vendor ID:               BunnyCore",
                "  Model name:            BunnyCore i7 (Carrot)",
                "    CPU family:          20",
                "    Model:               6",
                "    Thread(s) per core:  2",
                "    Core(s) per socket:  4",
                "    Socket(s):           1",
                "    CPU max MHz:         3400.0000",
                "    CPU min MHz:         800.0000",
            ]

        if cmd == "sudo":
            if not args:
                return ["usage: sudo <команда>"]
            return [f"[sudo] running as root: {' '.join(args)}",
                    f"(команда '{args[0]}' выполнена с правами root)"]

        if cmd == "exit":
            return ["__EXIT__"]

        return [f"bash: {cmd}: команда не найдена"]

    def _tree_lines(self, root):
        lines = [root]
        def walk(path, prefix):
            if not self._is_dir(path):
                return
            children = sorted([c for c in self.fs[path]["children"] if not c.startswith(".")])
            for i, c in enumerate(children):
                last = (i == len(children) - 1)
                full = path.rstrip("/") + "/" + c
                marker = "└── " if last else "├── "
                lines.append(prefix + marker + c)
                if self._is_dir(full):
                    walk(full, prefix + ("    " if last else "│   "))
        walk(root, "")
        return lines

    def _remove_recursive(self, path):
        if path in self.fs:
            if self.fs[path]["type"] == "dir":
                for c in list(self.fs[path]["children"]):
                    self._remove_recursive(path.rstrip("/") + "/" + c)
            del self.fs[path]
