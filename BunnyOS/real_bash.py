"""UI реального bash — полноэкранный режим."""
import pygame
import re
from settings import WIDTH, HEIGHT
from real_terminal import RealTerminal, SANDBOX_DIR, strip_ansi


C_BG = (6, 8, 14)
C_TEXT = (200, 220, 240)
C_PROMPT = (100, 240, 130)
C_ERROR = (255, 100, 120)
C_WARNING = (255, 200, 80)
C_HEADER = (30, 40, 60)
C_DIM = (100, 120, 150)


class RealBashUI:
    ANSI_COLORS = {
        30: (30, 30, 30), 31: (220, 80, 80), 32: (100, 220, 100),
        33: (220, 200, 80), 34: (100, 160, 220), 35: (200, 100, 220),
        36: (100, 220, 220), 37: (220, 220, 220),
        90: (110, 110, 110), 91: (255, 130, 130), 92: (130, 255, 130),
        93: (255, 240, 130), 94: (130, 200, 255), 95: (240, 130, 255),
        96: (130, 240, 240), 97: (255, 255, 255),
    }

    def __init__(self, font_small):
        self.font = font_small
        self.terminal = RealTerminal(sandbox=True)
        self.open = False
        self.lines = []
        self.input = ""
        self.cursor_blink = 0.0
        self.scroll = 0
        # История команд
        self.history = []
        self.hist_idx = -1

    @staticmethod
    def _copy_to_clipboard(text):
        """Копирует в системный буфер обмена через xclip/wl-copy."""
        import subprocess, shutil
        try:
            if shutil.which("wl-copy"):
                subprocess.run(["wl-copy"], input=text.encode(), check=False, timeout=2)
                return True
            if shutil.which("xclip"):
                subprocess.run(["xclip", "-selection", "clipboard"],
                               input=text.encode(), check=False, timeout=2)
                return True
            if shutil.which("xsel"):
                subprocess.run(["xsel", "--clipboard", "--input"],
                               input=text.encode(), check=False, timeout=2)
                return True
        except Exception:
            pass
        return False

    @staticmethod
    def _paste_from_clipboard():
        """Читает из системного буфера."""
        import subprocess, shutil
        try:
            if shutil.which("wl-paste"):
                r = subprocess.run(["wl-paste"], capture_output=True, timeout=2)
                return r.stdout.decode("utf-8", errors="replace")
            if shutil.which("xclip"):
                r = subprocess.run(["xclip", "-selection", "clipboard", "-o"],
                                   capture_output=True, timeout=2)
                return r.stdout.decode("utf-8", errors="replace")
            if shutil.which("xsel"):
                r = subprocess.run(["xsel", "--clipboard", "--output"],
                                   capture_output=True, timeout=2)
                return r.stdout.decode("utf-8", errors="replace")
        except Exception:
            pass
        return ""

    def open_ui(self):
        if self.open:
            return
        if not self.terminal.start():
            self.lines.append("⚠ Не удалось запустить bash")
            return
        self.open = True
        if self.terminal.used_bwrap:
            self.lines.append("✓ SANDBOX mode (bwrap)")
            self.lines.append(f"  Твоя папка: {SANDBOX_DIR}")
        else:
            self.lines.append("⚠ RAW mode — bwrap не установлен!")
            self.lines.append("  Команды выполняются НАПРЯМУЮ.")
        self.lines.append("")

    def close_ui(self):
        if self.terminal:
            self.terminal.stop()
        self.open = False
        self.lines = []
        self.input = ""

    def handle_event(self, event):
        if not self.open:
            return
        if event.type != pygame.KEYDOWN:
            return

        mods = pygame.key.get_mods()

        if event.key == pygame.K_ESCAPE:
            self.close_ui()
            return

        # Ctrl+Shift+C / Ctrl+Shift+V — буфер обмена
        shift = mods & pygame.KMOD_SHIFT
        if (mods & pygame.KMOD_CTRL) and shift:
            if event.key == pygame.K_c:
                # Копировать выделенные строки (или последние 20)
                text = "\n".join(strip_ansi(l) for l in self.lines[-20:])
                ok = self._copy_to_clipboard(text)
                self.lines.append(f"[копировано {len(text)} байт]" if ok else "[буфер недоступен]")
                return
            if event.key == pygame.K_v:
                pasted = self._paste_from_clipboard()
                if pasted:
                    self.input += pasted.strip()
                return

        # Ctrl-комбинации
        if mods & pygame.KMOD_CTRL:
            if event.key == pygame.K_d:
                self.terminal.send_ctrl_d()
                return
            if event.key == pygame.K_c:
                self.terminal.send_ctrl_c()
                self.lines.append(self.input + "^C")
                self.input = ""
                return
            if event.key == pygame.K_l:
                self.lines = []
                self.scroll = 0
                return
            if event.key == pygame.K_u:
                self.input = ""
                return

        if event.key == pygame.K_TAB:
            # Простое автодополнение из часто-используемых команд
            known = [
                "ls ", "cd ", "pwd", "cat ", "echo ", "grep ", "find ",
                "uname -a", "df -h", "free -h", "ps aux",
                "python3 ", "git ", "pip ", "nano ", "vim ",
                "ls -la ", "ls ~/bunny_sandbox",
                "clear", "exit", "history",
            ]
            last = self.input.split()[-1] if self.input else ""
            matches = [k for k in known if k.startswith(last) or k.startswith(self.input)]
            if len(matches) == 1:
                if " " in self.input:
                    self.input = self.input.rsplit(" ", 1)[0] + " " + matches[0]
                else:
                    self.input = matches[0]
            return

        if event.key == pygame.K_RETURN:
            cmd = self.input.strip()
            if cmd:
                self.history.append(cmd)
                self.hist_idx = -1
                self.lines.append(f"$ {cmd}")
                ok, reason = self.terminal.execute(cmd)
                if not ok:
                    self.lines.append(f"[BLOCKED] {reason}")
            self.input = ""
            return
        elif event.key == pygame.K_UP:
            if self.history:
                if self.hist_idx == -1:
                    self.hist_idx = len(self.history) - 1
                else:
                    self.hist_idx = max(0, self.hist_idx - 1)
                self.input = self.history[self.hist_idx]
        elif event.key == pygame.K_DOWN:
            if self.hist_idx >= 0:
                if self.hist_idx >= len(self.history) - 1:
                    self.hist_idx = -1
                    self.input = ""
                else:
                    self.hist_idx += 1
                    self.input = self.history[self.hist_idx]
        elif event.key == pygame.K_BACKSPACE:
            self.input = self.input[:-1]
        elif event.key == pygame.K_PAGEUP:
            self.scroll = min(self.scroll + 5, max(0, len(self.lines) - 5))
        elif event.key == pygame.K_PAGEDOWN:
            self.scroll = max(0, self.scroll - 5)
        else:
            if event.unicode and event.unicode.isprintable():
                self.input += event.unicode

    def update(self, dt):
        if not self.open or not self.terminal.running:
            return
        self.cursor_blink += dt
        for _ in range(5):
            out = self.terminal.read_output(0.02)
            if not out:
                break
            for line in re.split(r'\r\n|\n', out):
                if line:
                    self.lines.append(line)
        if len(self.lines) > 1000:
            self.lines = self.lines[-1000:]

    def _draw_ansi_line(self, screen, line, x, y):
        parts = re.split(r'(\x1b\[[0-9;]*m)', line)
        color = C_TEXT
        cx = x
        for part in parts:
            if not part:
                continue
            if part.startswith("\x1b["):
                m = re.search(r'\x1b\[(\d+)(?:;\d+)?m', part)
                if m:
                    code = int(m.group(1))
                    if code == 0:
                        color = C_TEXT
                    elif code == 1:
                        color = (255, 255, 255)
                    elif code in self.ANSI_COLORS:
                        color = self.ANSI_COLORS[code]
            else:
                txt = self.font.render(part[:100], True, color)
                screen.blit(txt, (cx, y))
                cx += txt.get_width()

    def draw(self, screen):
        screen.fill(C_BG)

        # Header
        header = pygame.Rect(0, 0, WIDTH, 44)
        pygame.draw.rect(screen, C_HEADER, header)
        border_col = C_PROMPT if self.terminal.used_bwrap else C_ERROR
        pygame.draw.line(screen, border_col, (0, 44), (WIDTH, 44), 2)

        mode = "SANDBOX" if self.terminal.used_bwrap else "RAW ⚠"
        mt = self.font.render(mode, True, border_col)
        screen.blit(mt, (20, 12))

        title = self.font.render("REAL BASH", True, C_TEXT)
        screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 12))

        path = self.font.render(f"📁 {SANDBOX_DIR}", True, C_DIM)
        screen.blit(path, (WIDTH - path.get_width() - 20, 12))

        # Вывод
        line_h = 18
        visible = (HEIGHT - 130) // line_h
        start = max(0, len(self.lines) - visible - self.scroll)
        end = start + visible
        y = 54
        for line in self.lines[start:end]:
            self._draw_ansi_line(screen, line, 20, y)
            y += line_h

        # Ввод
        input_y = HEIGHT - 70
        pygame.draw.rect(screen, (15, 20, 30), (0, input_y, WIDTH, 70))
        pygame.draw.line(screen, C_PROMPT, (0, input_y), (WIDTH, input_y), 2)

        prompt = self.font.render("$", True, C_PROMPT)
        screen.blit(prompt, (20, input_y + 22))
        inp = self.font.render(self.input, True, C_TEXT)
        screen.blit(inp, (40, input_y + 22))

        if int(self.cursor_blink * 2) % 2 == 0:
            cx = 40 + inp.get_width() + 2
            pygame.draw.rect(screen, C_TEXT, (cx, input_y + 24, 8, 18))

        # Hints
        hint = self.font.render(
            "ENTER выполнить  Esc выход  Ctrl+C прервать  Ctrl+L очистить",
            True, C_DIM)
        screen.blit(hint, (20, HEIGHT - 22))

        # Bash упал
        if not self.terminal.running and self.lines:
            warn = self.font.render("bash завершён. Esc — назад.", True, C_ERROR)
            screen.blit(warn, (WIDTH // 2 - warn.get_width() // 2, HEIGHT // 2))
