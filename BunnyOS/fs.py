"""Виртуальная Unix-ФС + оболочка BunnyOS."""
import sys
import time


class VirtualFS:
    def __init__(self):
        self.files = {}
        self.dirs = {"/"}
        self._populate()

    def _populate(self):
        for d in ["/bin", "/etc", "/home", "/home/zayka",
                  "/home/zayka/Documents", "/home/zayka/Pictures",
                  "/home/zayka/Downloads", "/tmp", "/usr", "/usr/bin",
                  "/var", "/var/log"]:
            self.dirs.add(d)

        self.files["/etc/os-release"] = (
            'NAME="BunnyOS"\n'
            'VERSION="1.0 LTS (Carrot)"\n'
            'ID=bunnyos\n'
            'PRETTY_NAME="BunnyOS 1.0 LTS"\n'
        )
        self.files["/etc/hostname"] = "bunnyos\n"
        self.files["/etc/passwd"] = (
            "root:x:0:0:root:/root:/bin/bash\n"
            "zayka:x:1000:1000:Zayka:/home/zayka:/bin/bash\n"
        )
        self.files["/home/zayka/README.txt"] = (
            "Welcome to BunnyOS!\n"
            "===================\n\n"
            "This is a Unix-like OS simulator.\n"
            "Try the terminal:\n"
            "  ls, cd, cat, help\n"
        )
        self.files["/home/zayka/Documents/note.txt"] = (
            "Notes:\n"
            "1. Water the carrots\n"
            "2. Check radio\n"
            "3. Write new program\n"
        )
        self.files["/tmp/test.txt"] = "temporary file\n"
        self.files["/usr/bin/snake"] = "# Snake game binary\n"

    def _norm(self, path, cwd="/"):
        if not path:
            return cwd
        if not path.startswith("/"):
            path = (cwd.rstrip("/") + "/" + path) if cwd != "/" else "/" + path
        parts = []
        for p in path.split("/"):
            if p in ("", "."):
                continue
            if p == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(p)
        return "/" + "/".join(parts)

    def resolve(self, path, cwd="/"):
        return self._norm(path, cwd)

    def exists(self, path):
        p = self._norm(path)
        return p in self.files or p in self.dirs

    def is_dir(self, path):
        return self._norm(path) in self.dirs

    def is_file(self, path):
        return self._norm(path) in self.files

    def ls(self, path):
        path = self._norm(path)
        if path not in self.dirs:
            return None
        prefix = "/" if path == "/" else path + "/"
        dirs, files = [], []
        for d in self.dirs:
            if d == path or not d.startswith(prefix):
                continue
            rest = d[len(prefix):]
            if "/" not in rest and rest:
                dirs.append(rest)
        for f in self.files:
            if not f.startswith(prefix):
                continue
            rest = f[len(prefix):]
            if "/" not in rest and rest:
                files.append(rest)
        return sorted(dirs), sorted(files)

    def mkdir(self, path):
        self.dirs.add(self._norm(path))

    def touch(self, path, content=""):
        self.files[self._norm(path)] = content

    def read(self, path):
        return self.files.get(self._norm(path))

    def write(self, path, content):
        self.files[self._norm(path)] = content

    def rm(self, path):
        p = self._norm(path)
        if p in self.files:
            del self.files[p]
            return True
        if p in self.dirs:
            r = self.ls(p)
            if r and (r[0] or r[1]):
                return False
            self.dirs.discard(p)
            return True
        return False


class Shell:
    def __init__(self, fs, user="zayka", host="bunnyos"):
        self.fs = fs
        self.user = user
        self.host = host
        self.cwd = f"/home/{user}"
        self.history = []

    def prompt(self):
        short = self.cwd
        home = f"/home/{self.user}"
        if short == home:
            short = "~"
        elif short.startswith(home + "/"):
            short = "~" + short[len(home):]
        return f"{self.user}@{self.host}:{short}$"

    def run(self, line):
        line = line.strip()
        self.history.append(line)
        if not line:
            return []
        try:
            return self._pipeline(line)
        except Exception as e:
            return [f"bash: error: {e}"]

    def _pipeline(self, line):
        # split pipe | (вне кавычек)
        parts, buf, q = [], [], None
        for c in line:
            if c in ('"', "'"):
                if q == c:
                    q = None
                elif q is None:
                    q = c
                buf.append(c)
            elif c == "|" and q is None:
                parts.append("".join(buf)); buf = []
            else:
                buf.append(c)
        parts.append("".join(buf))

        stdin = None
        for part in parts:
            tokens = self._tok(part.strip())
            if not tokens:
                continue
            stdin = self._dispatch(tokens[0], tokens[1:], stdin)
        return stdin or []

    def _tok(self, s):
        out, buf, q = [], [], None
        for c in s:
            if c in ('"', "'"):
                if q == c:
                    q = None
                elif q is None:
                    q = c
                else:
                    buf.append(c)
            elif c == " " and q is None:
                if buf:
                    out.append("".join(buf)); buf = []
            else:
                buf.append(c)
        if buf:
            out.append("".join(buf))
        return out

    def _res(self, p):
        return self.fs.resolve(p, self.cwd)

    def _dispatch(self, cmd, args, stdin=None):
        # Фильтры для pipe
        if stdin is not None and cmd in ("grep", "head", "tail", "wc", "sort"):
            if cmd == "grep":
                pat = args[0] if args else ""
                return [l for l in stdin if pat in l]
            if cmd == "head":
                n = 10
                if args and args[0].startswith("-"):
                    try: n = int(args[0][1:])
                    except: pass
                return stdin[:n]
            if cmd == "tail":
                n = 10
                if args and args[0].startswith("-"):
                    try: n = int(args[0][1:])
                    except: pass
                return stdin[-n:]
            if cmd == "wc":
                return [f"{len(stdin)} {sum(len(l.split()) for l in stdin)} {sum(len(l) for l in stdin)}"]
            if cmd == "sort":
                return sorted(stdin)

        # Основные команды
        if cmd == "help":
            return [
                "BunnyOS Shell — commands:",
                "  help         — this help",
                "  ls [path]    — list files",
                "  cd <path>    — change dir",
                "  pwd          — current dir",
                "  cat <file>   — show file",
                "  echo <text>  — print text",
                "  whoami       — current user",
                "  hostname     — host name",
                "  uname [-a]   — system info",
                "  date         — current date",
                "  uptime       — uptime",
                "  clear        — clear screen",
                "  history      — command history",
                "  neofetch     — system summary",
                "  tree [path]  — directory tree",
                "  mkdir <d>    — create dir",
                "  touch <f>    — create file",
                "  rm <path>    — remove",
                "  grep <p> <f> — search in file",
                "  head <f>     — first lines",
                "  tail <f>     — last lines",
                "  wc <f>       — word count",
                "  man <cmd>    — manual",
                "  ps           — processes",
                "  sudo <cmd>   — superuser",
                "  exit         — exit",
                "",
                "Pipe supported: cat file | grep x",
            ]
        if cmd == "ls":
            return self._ls(args)
        if cmd == "cd":
            return self._cd(args)
        if cmd == "pwd":
            return [self.cwd]
        if cmd == "cat":
            return self._cat(args)
        if cmd == "echo":
            return [" ".join(args)]
        if cmd == "whoami":
            return [self.user]
        if cmd == "hostname":
            return [self.host]
        if cmd == "uname":
            if "-r" in args: return ["5.15.0-carrot"]
            if "-a" in args: return ["Linux bunnyos 5.15.0-carrot #1 SMP x86_64 GNU/Linux"]
            return ["Linux"]
        if cmd == "date":
            return [time.strftime("%a %b %d %H:%M:%S %Y")]
        if cmd == "uptime":
            return ["up 0 min, 1 user, load average: 0.10, 0.05, 0.01"]
        if cmd == "clear":
            return ["__CLEAR__"]
        if cmd == "history":
            return [f"{i+1:3}  {h}" for i, h in enumerate(self.history)]
        if cmd == "tetris":

            import subprocess

            import os

            script = os.path.join(os.path.dirname(__file__), "tetris.py")

            try:

                subprocess.Popen([sys.executable, script])

                return ["[tetris] Тетрис запущен в отдельном окне"]

            except Exception as e:

                return [f"[tetris] ошибка: {e}"]


        if cmd == "2048":



            import subprocess



            import os



            script = os.path.join(os.path.dirname(__file__), "game2048.py")



            try:



                subprocess.Popen([sys.executable, script])



                return ["[2048] 2048 запущена в отдельном окне"]



            except Exception as e:



                return [f"[2048] ошибка: {e}"]




        if cmd == "snake":
            # Запуск Змейки во внешнем окне через subprocess
            import subprocess
            import os
            script = os.path.join(os.path.dirname(__file__), "snake.py")
            try:
                subprocess.Popen([sys.executable, script])
                return ["[snake] Змейка запущена в отдельном окне"]
            except Exception as e:
                return [f"[snake] ошибка: {e}"]

        if cmd == "games":
            return [
                "Доступные игры:",
                "  snake   — Змейка (классика)",
                "  tetris  — Тетрис (классика)",
                "  2048    — 2048 (головоломка)",
                "  (скоро) pong",
            ]

        if cmd == "exit":
            return ["__EXIT__"]
        if cmd == "mkdir":
            if not args: return ["mkdir: missing operand"]
            for a in args:
                self.fs.mkdir(self._res(a))
            return []
        if cmd == "touch":
            if not args: return ["touch: missing operand"]
            for a in args:
                self.fs.touch(self._res(a))
            return []
        if cmd == "rm":
            if not args: return ["rm: missing operand"]
            for a in args:
                if not self.fs.rm(self._res(a)):
                    return [f"rm: cannot remove '{a}'"]
            return []
        if cmd == "tree":
            return self._tree(args)
        if cmd == "grep":
            return self._grep(args)
        if cmd == "head":
            return self._head(args)
        if cmd == "tail":
            return self._tail(args)
        if cmd == "wc":
            return self._wc(args)
        if cmd == "neofetch":
            return self._neofetch()
        if cmd == "man":
            return self._man(args)
        if cmd == "ps":
            return [
                "  PID TTY          TIME CMD",
                "    1 ?        00:00:01 init",
                "  100 ?        00:00:00 bunny-daemon",
                "  500 tty1     00:00:00 bash",
                "  501 tty1     00:00:00 ps",
            ]
        if cmd == "sudo":
            return ["[sudo] password for zayka:", "(simulated) OK"]
        if cmd == "clear":
            return ["__CLEAR__"]

        return [f"bash: {cmd}: command not found"]

    def _ls(self, args):
        path = args[0] if args else self.cwd
        r = self.fs.ls(self._res(path))
        if r is None:
            return [f"ls: cannot access '{path}': No such directory"]
        dirs, files = r
        return [d + "/" for d in dirs] + files

    def _cd(self, args):
        if not args:
            self.cwd = f"/home/{self.user}"
            return []
        t = self._res(args[0])
        if not self.fs.is_dir(t):
            return [f"cd: no such directory: {args[0]}"]
        self.cwd = t
        return []

    def _cat(self, args):
        if not args:
            return ["cat: missing operand"]
        out = []
        for a in args:
            c = self.fs.read(self._res(a))
            if c is None:
                out.append(f"cat: {a}: No such file")
            else:
                out.extend(c.rstrip("\n").split("\n"))
        return out

    def _tree(self, args):
        path = args[0] if args else self.cwd
        root = self._res(path)
        if not self.fs.is_dir(root):
            return [f"tree: {path}: not a directory"]
        out = [root]
        self._walk(root, "", out)
        return out

    def _walk(self, path, prefix, out):
        r = self.fs.ls(path)
        if not r:
            return
        dirs, files = r
        entries = [(d, True) for d in dirs] + [(f, False) for f in files]
        for i, (name, is_d) in enumerate(entries):
            last = i == len(entries) - 1
            br = "\\-- " if last else "|-- "
            out.append(prefix + br + name + ("/" if is_d else ""))
            if is_d:
                np = path.rstrip("/") + "/" + name
                self._walk(np, prefix + ("    " if last else "|   "), out)

    def _grep(self, args):
        if len(args) < 2:
            return ["grep: usage: grep PATTERN FILE"]
        c = self.fs.read(self._res(args[1]))
        if c is None:
            return [f"grep: {args[1]}: No such file"]
        return [l for l in c.splitlines() if args[0] in l]

    def _head(self, args):
        n = 10
        files = []
        for a in args:
            if a.startswith("-"):
                try: n = int(a[1:])
                except: pass
            else:
                files.append(a)
        if not files:
            return ["head: missing operand"]
        c = self.fs.read(self._res(files[0]))
        if c is None:
            return [f"head: {files[0]}: No such file"]
        return c.splitlines()[:n]

    def _tail(self, args):
        n = 10
        files = []
        for a in args:
            if a.startswith("-"):
                try: n = int(a[1:])
                except: pass
            else:
                files.append(a)
        if not files:
            return ["tail: missing operand"]
        c = self.fs.read(self._res(files[0]))
        if c is None:
            return [f"tail: {files[0]}: No such file"]
        return c.splitlines()[-n:]

    def _wc(self, args):
        files = [a for a in args if not a.startswith("-")]
        if not files:
            return ["wc: missing operand"]
        c = self.fs.read(self._res(files[0]))
        if c is None:
            return [f"wc: {files[0]}: No such file"]
        lines = c.splitlines()
        return [f"{len(lines)} {sum(len(l.split()) for l in lines)} {len(c)} {files[0]}"]

    def _neofetch(self):
        logo = [
            "     /\\   /\\     ",
            "    /  \\ /  \\    ",
            "   |    X    |   ",
            "   |   o o   |   ",
            "   |    <    |   ",
            "   |  \\___/  |   ",
            "    \\_______/    ",
            "     /|   |\\     ",
            "    / |   | \\    ",
            "   *  |___|  *   ",
        ]
        info = [
            f"{self.user}@{self.host}",
            "-" * 22,
            "OS:       BunnyOS 1.0 LTS",
            "Kernel:   5.15.0-carrot",
            "Shell:    bunny-sh 1.0",
            "DE:       Luna Desktop",
            "CPU:      BunnyCore i7 (8) @ 3.4GHz",
            "Memory:   512MiB / 4096MiB",
            "Disk:     2GiB / 64GiB",
            "Uptime:   0 min",
        ]
        out = []
        for i in range(max(len(logo), len(info))):
            l = logo[i] if i < len(logo) else " " * 18
            r = info[i] if i < len(info) else ""
            out.append(f"{l}  {r}")
        return out

    def _man(self, args):
        if not args:
            return ["What manual page do you want?"]
        m = {
            "ls":   ["LS(1)", "", "ls — list directory contents", "  ls [path]"],
            "cd":   ["CD(1)", "", "cd — change directory", "  cd <path>"],
            "cat":  ["CAT(1)", "", "cat — print file", "  cat <file>"],
            "grep": ["GREP(1)", "", "grep — pattern search", "  grep PATTERN FILE"],
            "rm":   ["RM(1)", "", "rm — remove files", "  rm <path>"],
        }
        return m.get(args[0], [f"man: no manual for '{args[0]}'"])
