"""BunnyNet — мини-браузер: реальные сайты через requests + BeautifulSoup."""
import threading
import pygame

try:
    import requests
    from bs4 import BeautifulSoup
    NET_OK = True
except ImportError:
    NET_OK = False


HOME_URL = "https://habr.com/ru/all/"

# Быстрые закладки (проверенные рабочие сайты)
BOOKMARKS = [
    ("Habr",    "https://habr.com/ru/all/"),
    ("HN",      "https://news.ycombinator.com"),
    ("Lenta",   "https://lenta.ru"),
    ("PyGame",  "https://habr.com/ru/hubs/gamedev/"),
]


class BrowserApp:
    app_id = "browser"

    def __init__(self, os_ref):
        self.os = os_ref
        self.url = HOME_URL
        self.input = ""
        self.input_focus = False
        self.lines = ["Нажми ⟳ или выбери адрес, чтобы загрузить."]
        self.title = "BunnyNet"
        self.links = []      # [(y_line_index, url)]
        self.scroll = 0
        self.loading = False
        self.error = None
        # Кнопки навигации
        self._nav_y = 0
        self._load(self.url)

    # ---------- ЗАГРУЗКА ----------
    def _load(self, url):
        if not NET_OK:
            self.lines = ["[!] requests/bs4 не установлены.", "pip install requests beautifulsoup4 lxml"]
            return
        if not url.startswith("http"):
            url = "https://" + url
        self.url = url
        self.loading = True
        self.error = None
        self.lines = ["Загрузка..."]
        self.links = []
        self.scroll = 0
        t = threading.Thread(target=self._fetch, args=(url,), daemon=True)
        t.start()

    def _fetch(self, url):
        try:
            # Полноценные заголовки браузера — многие сайты блокируют ботов
            headers = {
                "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ru,en;q=0.9",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
            r = requests.get(url, timeout=10, headers=headers, allow_redirects=True)
            r.encoding = r.apparent_encoding or "utf-8"

            # Пробуем lxml, если нет — html.parser
            try:
                soup = BeautifulSoup(r.text, "lxml")
            except Exception:
                soup = BeautifulSoup(r.text, "html.parser")

            # Заголовок страницы
            t = soup.find("title")
            self.title = t.get_text().strip()[:60] if t else url

            # Собираем текст
            lines = []
            links = []

            h1 = soup.find("h1")
            if h1:
                txt = h1.get_text().strip()
                if txt:
                    lines.append("")
                    lines.append("=" * 60)
                    lines.append("  " + txt)
                    lines.append("=" * 60)

            paras = soup.find_all(["h2", "h3", "p", "li"])
            for el in paras:
                txt = el.get_text().strip()
                if not txt or len(txt) < 3:
                    continue
                if el.name == "h2":
                    lines.append("")
                    lines.append("-- " + txt + " --")
                elif el.name == "h3":
                    lines.append("")
                    lines.append("> " + txt)
                else:
                    while len(txt) > 90:
                        cut = txt.rfind(" ", 0, 90)
                        if cut < 40:
                            cut = 90
                        lines.append(txt[:cut])
                        txt = txt[cut:].lstrip()
                    if txt:
                        lines.append(txt)
                if len(lines) > 400:
                    break

            # Ссылки — 30 штук с http
            seen = set()
            base_url = "/".join(url.split("/")[:3])
            for a in soup.find_all("a", href=True)[:60]:
                href = a["href"]
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = base_url + href
                if href.startswith("http") and href not in seen:
                    seen.add(href)
                    txt = a.get_text().strip()[:50]
                    if not txt:
                        continue
                    links.append((len(lines), href))
                    lines.append(f"   -> {txt}")

            self.lines = lines if lines else ["(пустая страница)"]
            self.links = links
        except requests.exceptions.Timeout:
            self.error = "timeout"
            self.lines = ["[!] Таймаут: сайт не отвечает 10 секунд",
                          "", f"URL: {url}",
                          "Попробуй другой сайт или повтори позже."]
        except requests.exceptions.ConnectionError as e:
            self.error = "connection"
            self.lines = ["[!] Соединение сброшено:",
                          f"   {str(e)[:80]}",
                          "", f"URL: {url}", "",
                          "Возможные причины:",
                          "  - Провайдер блокирует сайт",
                          "  - Сайт блокирует ботов",
                          "  - Нет интернета",
                          "",
                          "Попробуй резервные адреса (кнопка Home):",
                          "   - lite.duckduckgo.com/lite/?q=linux",
                          "   - news.ycombinator.com",
                          "   - ru.m.wikipedia.org"]
        except Exception as e:
            self.error = str(e)
            self.lines = [f"[!] Ошибка: {type(e).__name__}",
                          f"   {str(e)[:100]}",
                          "", f"URL: {url}"]
        finally:
            self.loading = False

    # ---------- СОБЫТИЯ ----------
    def handle_event(self, event, rect):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            # Закладки (вторая строка)
            bm_y = rect.y + 38
            bx = rect.x + 8
            for name, url in BOOKMARKS:
                bw = len(name) * 8 + 16
                br = pygame.Rect(bx, bm_y, bw, 20)
                if br.collidepoint(mx, my):
                    self._load(url)
                    return
                bx += bw + 4
            # Навигационные кнопки
            nav_y = rect.y + 8
            bx = rect.x + 8
            for key, w in [("back", 30), ("fwd", 30), ("reload", 30), ("home", 30)]:
                br = pygame.Rect(bx, nav_y, w, 26)
                if br.collidepoint(mx, my):
                    if key == "reload":
                        self._load(self.url)
                    elif key == "home":
                        self._load(HOME_URL)
                    elif key == "back":
                        self._load(HOME_URL)
                    return
                bx += w + 4
            # Адресная строка
            url_r = pygame.Rect(rect.x + 152, nav_y, rect.w - 160, 26)
            self.input_focus = url_r.collidepoint(mx, my)
            if self.input_focus:
                self.input = self.url
            # Клик по ссылкам
            if not self.input_focus:
                y0 = rect.y + 80 - self.scroll
                for line_no, url in self.links:
                    ly = y0 + line_no * 16
                    if rect.y + 40 < my < rect.bottom - 8 and ly <= my <= ly + 16:
                        self._load(url)
                        return

        if event.type == pygame.KEYDOWN and self.input_focus:
            if event.key == pygame.K_RETURN:
                self._load(self.input)
                self.input_focus = False
            elif event.key == pygame.K_BACKSPACE:
                self.input = self.input[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.input_focus = False
            else:
                if event.unicode and event.unicode.isprintable():
                    self.input += event.unicode

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if rect.collidepoint(mx, my):
                self.scroll -= event.y * 30
                if self.scroll < 0:
                    self.scroll = 0

    # ---------- ОТРИСОВКА ----------
    def draw(self, scr, rect, font):
        pygame.draw.rect(scr, (250, 250, 250), rect)
        mono = pygame.font.Font(None, 16)
        small = pygame.font.Font(None, 14)

        # Навигационная панель
        nav = pygame.Rect(rect.x, rect.y, rect.w, 42)
        pygame.draw.rect(scr, (225, 220, 215), nav)
        pygame.draw.line(scr, (190, 185, 180), (nav.x, nav.bottom), (nav.right, nav.bottom))

        mx, my = pygame.mouse.get_pos()
        bx = rect.x + 8
        by = rect.y + 8
        for key, label in [("back", "←"), ("fwd", "→"), ("reload", "⟳"), ("home", "⌂")]:
            br = pygame.Rect(bx, by, 30, 26)
            hover = br.collidepoint(mx, my)
            col = (210, 205, 200) if not hover else (180, 175, 170)
            pygame.draw.rect(scr, col, br, border_radius=4)
            pygame.draw.rect(scr, (150, 145, 140), br, 1, border_radius=4)
            t = mono.render(label, True, (40, 40, 40))
            scr.blit(t, (br.centerx - t.get_width() // 2, br.centery - t.get_height() // 2))
            bx += 34

        # Адресная строка
        url_r = pygame.Rect(rect.x + 152, by, rect.w - 160, 26)
        focus = self.input_focus
        pygame.draw.rect(scr, (255, 255, 255), url_r, border_radius=4)
        pygame.draw.rect(scr, (0, 120, 215) if focus else (150, 145, 140),
                         url_r, 2 if focus else 1, border_radius=4)
        shown_url = self.input if focus else self.url
        ut = mono.render(shown_url[:90], True, (30, 30, 30))
        scr.blit(ut, (url_r.x + 6, url_r.y + 6))

        # Закладки
        bm_y = rect.y + 38
        bx = rect.x + 8
        small_f = pygame.font.Font(None, 14)
        for name, url in BOOKMARKS:
            bw = len(name) * 8 + 16
            br = pygame.Rect(bx, bm_y, bw, 20)
            hover = br.collidepoint(mx, my)
            col = (210, 230, 250) if hover else (230, 230, 235)
            pygame.draw.rect(scr, col, br, border_radius=3)
            pygame.draw.rect(scr, (170, 170, 180), br, 1, border_radius=3)
            t = small_f.render(name, True, (30, 60, 120))
            scr.blit(t, (br.x + 6, br.y + 4))
            bx += bw + 4

        # Контент
        content = pygame.Rect(rect.x + 4, rect.y + 66, rect.w - 8, rect.h - 74)
        pygame.draw.rect(scr, (255, 255, 255), content)
        pygame.draw.rect(scr, (210, 210, 210), content, 1)
        # Клипаем
        old_clip = scr.get_clip()
        scr.set_clip(content)

        y = content.y + 8 - self.scroll
        for line in self.lines:
            if line.startswith("═"):
                t = mono.render(line, True, (0, 100, 200))
            elif line.startswith("──"):
                t = mono.render(line, True, (150, 80, 0))
            elif line.startswith("▶"):
                t = mono.render(line, True, (0, 120, 0))
            elif line.startswith("   →"):
                t = mono.render(line, True, (0, 80, 200))
                # Подчеркнуть
            elif line.startswith("[!]"):
                t = mono.render(line, True, (200, 0, 0))
            else:
                t = mono.render(line, True, (30, 30, 30))
            scr.blit(t, (content.x + 8, y))
            y += 16

        scr.set_clip(old_clip)

        # Статус-бар
        status = f"{self.title}   |   ссылок: {len(self.links)}   |   колесо — скролл"
        if self.loading:
            status = "Загрузка..."
        st = small.render(status, True, (100, 100, 100))
        scr.blit(st, (content.x + 4, content.bottom - 2))
