"""PyPixel TopDown — Зайка-программист."""
import sys
import pygame

from settings import WIDTH, HEIGHT, FPS, TILE
from world_td import World, Camera
from player_td import PlayerTD
from interior import Interior
from pc_ui import MiniPC
from title import TitleScreen
from game_menu import GameMenu
from boot import BootScreen, LoginScreen
import os_sounds


_FULLSCREEN = False


# =============== КАРТА ===============
def make_world_map_surface(world):
    from world_td import T_GRASS, T_PATH, T_WATER, T_STONE, T_TREE, T_FLOWER
    s = 8
    surf = pygame.Surface((world.w * s, world.h * s))
    surf.fill((15, 20, 35))
    colors = {
        T_GRASS: (60, 130, 70), T_PATH: (180, 160, 120),
        T_WATER: (60, 130, 200), T_STONE: (110, 110, 120),
        T_TREE: (30, 90, 50), T_FLOWER: (180, 160, 100),
    }
    for ty in range(world.h):
        for tx in range(world.w):
            t = world.tiles[ty][tx]
            pygame.draw.rect(surf, colors.get(t, (60, 130, 70)),
                             (tx * s, ty * s, s, s))
    for h in world.houses:
        pygame.draw.rect(surf, (200, 90, 80),
                         (h.tx * s, h.ty * s, h.w * s, h.h * s))
    return surf


def draw_big_map(screen, world, player, font_big, font_small):
    from world_td import T_GRASS, T_PATH, T_WATER, T_STONE, T_TREE, T_FLOWER
    screen.fill((15, 20, 35))
    s = 10
    map_w = world.w * s
    map_h = world.h * s
    x0 = (WIDTH - map_w) // 2
    y0 = (HEIGHT - map_h) // 2

    pygame.draw.rect(screen, (40, 35, 55), (x0 - 6, y0 - 6, map_w + 12, map_h + 12))
    pygame.draw.rect(screen, (200, 180, 120), (x0 - 6, y0 - 6, map_w + 12, map_h + 12), 2)

    colors = {
        T_GRASS: (60, 130, 70), T_PATH: (180, 160, 120),
        T_WATER: (60, 130, 200), T_STONE: (110, 110, 120),
        T_TREE: (30, 90, 50), T_FLOWER: (180, 160, 100),
    }
    for ty in range(world.h):
        for tx in range(world.w):
            t = world.tiles[ty][tx]
            pygame.draw.rect(screen, colors.get(t, (60, 130, 70)),
                             (x0 + tx * s, y0 + ty * s, s, s))
    for h in world.houses:
        pygame.draw.rect(screen, (200, 90, 80),
                         (x0 + h.tx * s, y0 + h.ty * s, h.w * s, h.h * s))
        pygame.draw.rect(screen, (255, 240, 200),
                         (x0 + h.door_tx * s, y0 + h.door_ty * s, s, s))
    for v in world.villagers:
        pygame.draw.circle(screen, (240, 220, 80),
                           (x0 + v.tx * s + s // 2, y0 + v.ty * s + s // 2), 3)

    ptx = int(player.x + player.w // 2) // TILE
    pty = int(player.y + player.h // 2) // TILE
    px = x0 + ptx * s + s // 2
    py = y0 + pty * s + s // 2
    pygame.draw.circle(screen, (100, 240, 255), (px, py), 7)
    pygame.draw.circle(screen, (255, 255, 255), (px, py), 7, 2)

    title = font_big.render("КАРТА МИРА", True, (240, 240, 200))
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
    hint = font_small.render("M или Esc — закрыть", True, (200, 200, 180))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))


# =============== ВСПОМОГАТЕЛЬНОЕ ===============
def _draw_hint(screen, font_small, text):
    hint = font_small.render(text, True, (220, 220, 220))
    bg = pygame.Surface((hint.get_width() + 20, hint.get_height() + 10), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))
    screen.blit(bg, (20, HEIGHT - 50))
    screen.blit(hint, (30, HEIGHT - 45))


def _try_enter_house(world, player, return_state):
    """Проверяет стоит ли игрок у двери дома. Возвращает Interior или None."""
    p_rect = player.rect
    for h in world.houses:
        dr = h.door_rect_px().inflate(45, 45)
        if dr.colliderect(p_rect):
            interior = Interior(house_index=world.houses.index(h))
            # Зайти внутрь — зайка появляется у двери изнутри
            player.x = interior.exit_tx * TILE + (TILE - player.w) // 2
            player.y = (interior.exit_ty - 1) * TILE + (TILE - player.h)
            player.direction = "up"
            return interior
    return None


def _try_enter_pc(interior, player):
    """Проверяет стоит ли игрок у стула — садит/включает ПК.
    Возвращает 'sit' | 'pc_on' | 'pc_off' | None."""
    p_rect = player.rect
    if interior.chair_rect().colliderect(p_rect):
        if not interior.sitting:
            interior.sitting = True
            player.x = interior.chair.x + (interior.chair.w - player.w) // 2
            player.y = interior.chair.y + (interior.chair.h - player.h) // 2
            player.direction = "up"
            return "sit"
        else:
            # Уже сидит — переключаем ПК
            interior.pc_on = not interior.pc_on
            if interior.pc_on:
                return "pc_on"
            else:
                return "pc_off"
    else:
        if interior.sitting:
            interior.sitting = False
    return None


def _try_exit_house(interior, player):
    """Проверяет стоит ли игрок у двери (выход)."""
    door_rect = pygame.Rect(interior.exit_tx * TILE,
                            interior.exit_ty * TILE,
                            TILE, TILE)
    return door_rect.colliderect(player.rect)


def _try_talk_villager(world, player):
    """Говорит с ближайшим NPC."""
    for v in world.villagers:
        dx = (v.tx * TILE + TILE // 2) - (player.x + player.w // 2)
        dy = (v.ty * TILE + TILE // 2) - (player.y + player.h // 2)
        if dx * dx + dy * dy < 70 * 70:
            import random as _r
            lines = [
                f"Привет, я {v.name}!",
                "Зайка, покормил грядки?",
                "Компьютер в доме — вещь!",
                "У озера что-то странное.",
                "Осторожнее на востоке.",
            ]
            v.say(_r.choice(lines), frames=180)
            return True
    return False


# =============== ИГРОВАЯ ПАНЕЛЬ (Stardew-style) ===============
INGAME_BAR_H = 72       # высота панели
PAD = 12                # отступ от краёв


def get_ingame_bar_buttons():
    """Возвращает список (label, id, rect) для главных кнопок."""
    labels = [
        ("МЕНЮ", "menu", 130),
        ("КАРТА", "map", 130),
        ("НАСТРОЙКИ", "settings", 170),
    ]
    rects = []
    x = PAD
    for label, bid, w in labels:
        rects.append((label, bid, pygame.Rect(x, HEIGHT - INGAME_BAR_H + 12, w, INGAME_BAR_H - 24)))
        x += w + 8
    return rects


def get_ingame_bar_icons():
    """Правые кнопки — оконный/полный экран."""
    y = HEIGHT - INGAME_BAR_H + 12
    h = INGAME_BAR_H - 24
    return [
        ("window", "window_mode", pygame.Rect(WIDTH - PAD - 100, y, 44, h)),
        ("full", "fullscreen", pygame.Rect(WIDTH - PAD - 50, y, 44, h)),
    ]


def draw_rounded_panel(surface, rect, color, radius=12, alpha=200):
    """Полупрозрачная скруглённая панель."""
    surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(surf, (*color, alpha), (0, 0, rect.w, rect.h), border_radius=radius)
    surface.blit(surf, (rect.x, rect.y))


def draw_rounded_button(surface, rect, hovered=False, active=False, base_color=(70, 55, 45)):
    """Скруглённая кнопка с градиентом и рамкой."""
    r = 10
    # Фон
    if active:
        top = tuple(min(255, c + 30) for c in base_color)
        bot = tuple(max(0, c - 10) for c in base_color)
    elif hovered:
        top = tuple(min(255, c + 40) for c in base_color)
        bot = tuple(min(255, c + 10) for c in base_color)
    else:
        top = base_color
        bot = tuple(max(0, c - 20) for c in base_color)
    # Градиент
    btn = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    for i in range(rect.h):
        t = i / rect.h
        col = tuple(int(top[j] * (1 - t) + bot[j] * t) for j in range(3))
        pygame.draw.rect(btn, (*col, 230), (0, i, rect.w, 1))
    # Маска скругления — рисуем поверх прозрачным
    mask = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, rect.w, rect.h), border_radius=r)
    btn.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surface.blit(btn, (rect.x, rect.y))
    # Рамка
    pygame.draw.rect(surface, (200, 170, 120), rect, 2, border_radius=r)
    # Верхний блик
    pygame.draw.line(surface, (255, 240, 200),
                     (rect.x + 6, rect.y + 3), (rect.right - 6, rect.y + 3), 1)


def draw_icon_menu(surface, cx, cy, color):
    """Иконка меню — три линии."""
    for dy in (-6, 0, 6):
        pygame.draw.line(surface, color, (cx - 12, cy + dy), (cx + 12, cy + dy), 3)


def draw_icon_map(surface, cx, cy, color):
    """Иконка карты — квадрат с сеткой."""
    pygame.draw.rect(surface, color, (cx - 12, cy - 12, 24, 24), 2)
    pygame.draw.line(surface, color, (cx, cy - 12), (cx, cy + 12), 1)
    pygame.draw.line(surface, color, (cx - 12, cy), (cx + 12, cy), 1)


def draw_icon_settings(surface, cx, cy, color):
    """Иконка настроек — шестерёнка (упрощённая)."""
    pygame.draw.circle(surface, color, (cx, cy), 10, 2)
    pygame.draw.circle(surface, color, (cx, cy), 4, 2)
    for ang in range(0, 360, 45):
        import math
        r1 = math.radians(ang)
        x1 = cx + int(math.cos(r1) * 10)
        y1 = cy + int(math.sin(r1) * 10)
        x2 = cx + int(math.cos(r1) * 14)
        y2 = cy + int(math.sin(r1) * 14)
        pygame.draw.line(surface, color, (x1, y1), (x2, y2), 3)


def draw_icon_window(surface, cx, cy, color):
    """Иконка оконного режима."""
    pygame.draw.rect(surface, color, (cx - 11, cy - 9, 22, 18), 2)


def draw_icon_fullscreen(surface, cx, cy, color):
    """Иконка полного экрана — уголки."""
    s = 11
    # 4 уголка
    pygame.draw.line(surface, color, (cx - s, cy - s), (cx - s + 6, cy - s), 3)
    pygame.draw.line(surface, color, (cx - s, cy - s), (cx - s, cy - s + 6), 3)
    pygame.draw.line(surface, color, (cx + s, cy - s), (cx + s - 6, cy - s), 3)
    pygame.draw.line(surface, color, (cx + s, cy - s), (cx + s, cy - s + 6), 3)
    pygame.draw.line(surface, color, (cx - s, cy + s), (cx - s + 6, cy + s), 3)
    pygame.draw.line(surface, color, (cx - s, cy + s), (cx - s, cy + s - 6), 3)
    pygame.draw.line(surface, color, (cx + s, cy + s), (cx + s - 6, cy + s), 3)
    pygame.draw.line(surface, color, (cx + s, cy + s), (cx + s, cy + s - 6), 3)


def draw_ingame_bar(screen, font_small, cursor):
    """Нижняя панель в стиле Stardew Valley."""
    # === Подложка — полупрозрачная тёмная, скругление сверху ===
    bar = pygame.Rect(0, HEIGHT - INGAME_BAR_H, WIDTH, INGAME_BAR_H)
    surf = pygame.Surface((WIDTH, INGAME_BAR_H), pygame.SRCALPHA)
    surf.fill((30, 20, 15, 210))
    # Верхняя золотая линия
    pygame.draw.line(surf, (180, 140, 80, 255), (0, 0), (WIDTH, 0), 3)
    pygame.draw.line(surf, (240, 210, 150, 200), (0, 2), (WIDTH, 2), 1)
    screen.blit(surf, (0, HEIGHT - INGAME_BAR_H))

    mx, my = cursor

    # === Левая группа — главные кнопки ===
    for label, bid, r in get_ingame_bar_buttons():
        hover = r.collidepoint(mx, my)
        draw_rounded_button(screen, r, hovered=hover)

        # Иконка + текст
        cy_icon = r.centery
        cx_icon = r.x + 24
        if bid == "menu":
            draw_icon_menu(screen, cx_icon, cy_icon, (240, 220, 180))
        elif bid == "map":
            draw_icon_map(screen, cx_icon, cy_icon, (240, 220, 180))
        elif bid == "settings":
            draw_icon_settings(screen, cx_icon, cy_icon, (240, 220, 180))

        txt = font_small.render(label, True, (255, 245, 220))
        screen.blit(txt, (cx_icon + 22, r.centery - txt.get_height() // 2))

    # === Правая группа — оконный/полный режим ===
    for icon, bid, r in get_ingame_bar_icons():
        hover = r.collidepoint(mx, my)
        draw_rounded_button(screen, r, hovered=hover)
        if bid == "window_mode":
            draw_icon_window(screen, r.centerx, r.centery, (240, 220, 180))
        elif bid == "fullscreen":
            draw_icon_fullscreen(screen, r.centerx, r.centery, (240, 220, 180))

    # === Подсказка — по центру панели ===
    hint = font_small.render("WASD · E · M · Esc",
                              True, (170, 150, 120))
    hx = WIDTH // 2 - hint.get_width() // 2
    hy = HEIGHT - INGAME_BAR_H // 2 - hint.get_height() // 2
    screen.blit(hint, (hx, hy))


def handle_ingame_bar_click(mx, my):
    """Возвращает 'menu'/'map'/'settings'/'window_mode'/'fullscreen'/None."""
    for label, bid, r in get_ingame_bar_buttons():
        if r.collidepoint(mx, my):
            return bid
    for icon, bid, r in get_ingame_bar_icons():
        if r.collidepoint(mx, my):
            return bid
    return None


# =============== MAIN ===============
def main():
    pygame.init()
    os_sounds.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("🐰 Зайка — Мир")
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("monospace", 26, bold=True)
    font_small = pygame.font.SysFont("monospace", 14, bold=True)
    font_tiny = pygame.font.SysFont("monospace", 12, bold=True)

    # ---- Game objects ----
    world = World()
    camera = Camera()
    player = PlayerTD(15, 22)
    map_surface = make_world_map_surface(world)
    pc = MiniPC(font_small, font_big, map_surface)

    # ---- Screens ----
    title_screen = TitleScreen(font_big, font_small)
    game_menu = GameMenu(font_big, font_small)
    boot_screen = None
    login_screen = None

    interior = None
    interior_return = None

    # ---- State ----
    # title → menu → world ⇄ interior ⇄ pc_boot → pc_login → pc
    state = "title"
    prev_ingame_state = "world"  # куда вернуться из overlay
    toast = None
    toast_timer = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        keys = pygame.key.get_pressed()

        # ============ EVENTS ============
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            # ----- Меню — своя обработка -----
            if state == "menu":
                game_menu.handle_event(event)
                if game_menu.result == "start":
                    state = prev_ingame_state  # вернуться к сохранённой игре
                    game_menu.result = None
                elif game_menu.result == "exit":
                    running = False
                continue
            if state == "ingame_settings":
                game_menu.handle_event(event)
                if game_menu.result == "back_to_game":
                    state = prev_ingame_state
                    game_menu.result = None
                continue

            if event.type == pygame.KEYDOWN:
                # F11 — fullscreen toggle в любом состоянии
                if event.key == pygame.K_F11:
                    global _FULLSCREEN
                    _FULLSCREEN = not _FULLSCREEN
                    from settings import WIDTH as _W, HEIGHT as _H
                    try:
                        if _FULLSCREEN:
                            screen = pygame.display.set_mode((_W, _H),
                                    pygame.FULLSCREEN | pygame.SCALED)
                        else:
                            screen = pygame.display.set_mode((_W, _H))
                    except pygame.error:
                        pass
                    continue

                if event.key == pygame.K_ESCAPE:
                    if state == "pc":
                        if interior:
                            interior.pc_on = False
                        state = "interior"
                        os_sounds.play("shutdown")
                    elif state == "interior":
                        # Выход на улицу
                        state = "world"
                        if interior_return:
                            player.x, player.y = interior_return
                        interior = None
                    elif state == "map":
                        state = "world"
                    elif state == "title":
                        title_screen.done = True
                    else:
                        running = False
                    continue

                if state == "title":
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        title_screen.done = True

                elif state == "world":
                    # Toggle режима тестера
                    if event.key == pygame.K_t:
                        World._test_mode = not getattr(World, "_test_mode", False)
                        if World._test_mode:
                            if not hasattr(World, "_tile_coords"):
                                World._tile_coords = {
                                    "grass": [3, 11], "path": [3, 1],
                                    "water": [18, 4], "tree": [2, 2],
                                }
                            if not hasattr(World, "_test_key"):
                                World._test_key = "grass"
                            print("[тест] ВКЛ · G-категория · WASD-двигать · T-выход")
                        else:
                            print("[тест] ВЫКЛ")
                        continue
                    # В режиме тестера — WASD двигает координаты
                    if getattr(World, "_test_mode", False):
                        cats = ["grass", "path", "water", "tree"]
                        if event.key == pygame.K_g:
                            i = cats.index(World._test_key)
                            World._test_key = cats[(i + 1) % len(cats)]
                            World._real_tiles.clear()
                            print(f"[тест] категория: {World._test_key}")
                        elif event.key in (pygame.K_LEFT, pygame.K_a):
                            World._tile_coords[World._test_key][0] -= 1
                            World._real_tiles.clear()
                        elif event.key in (pygame.K_RIGHT, pygame.K_d):
                            World._tile_coords[World._test_key][0] += 1
                            World._real_tiles.clear()
                        elif event.key in (pygame.K_UP, pygame.K_w):
                            World._tile_coords[World._test_key][1] -= 1
                            World._real_tiles.clear()
                        elif event.key in (pygame.K_DOWN, pygame.K_s):
                            World._tile_coords[World._test_key][1] += 1
                            World._real_tiles.clear()
                        continue
                    # Обычное управление
                    if event.key == pygame.K_m:
                        state = "map"
                    elif event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                        # Войти в дом?
                        new_int = _try_enter_house(world, player, state)
                        if new_int:
                            interior_return = (player.x, player.y)
                            interior = new_int
                            state = "interior"
                            toast = f"Дом #{world.houses.index(new_int.house_index.__class__) if False else ''}"
                            toast_timer = 60
                        else:
                            _try_talk_villager(world, player)

                elif state == "interior" and interior:
                    if event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                        # Сначала — выход у двери
                        if _try_exit_house(interior, player):
                            state = "world"
                            if interior_return:
                                player.x, player.y = interior_return
                            interior = None
                        else:
                            res = _try_enter_pc(interior, player)
                            if res == "pc_on":
                                boot_screen = BootScreen(font_big, font_small)
                                login_screen = None
                                state = "pc_boot"

                elif state == "map":
                    if event.key == pygame.K_m:
                        state = prev_ingame_state
                    elif event.key == pygame.K_ESCAPE:
                        state = prev_ingame_state

                elif state == "pc_boot" and boot_screen:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                        boot_screen.done = True

                elif state == "pc_login" and login_screen:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                        login_screen.done = True

                elif state == "pc":
                    if event.unicode and event.unicode.isprintable():
                        pc.handle_text(event.unicode)
                    _r = pc.handle_key(event.key)
                    if _r == "shutdown":
                        if interior:
                            interior.pc_on = False
                        state = "interior"
                        os_sounds.play("shutdown")

            # === Клики по игровой панели (в мире и в доме) ===
            if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                    and state in ("world", "interior")):
                mx, my = pygame.mouse.get_pos()
                action = handle_ingame_bar_click(mx, my)
                if action == "menu":
                    prev_ingame_state = state
                    game_menu.overlay = False
                    game_menu.return_to_game = True
                    game_menu.in_settings = False
                    game_menu.selected = 0
                    state = "menu"
                    continue
                elif action == "map":
                    prev_ingame_state = state
                    state = "map"
                    continue
                elif action == "settings":
                    prev_ingame_state = state
                    game_menu.open_from_game()
                    state = "ingame_settings"
                    continue
                elif action == "window_mode":
                    from settings import WIDTH as _W, HEIGHT as _H
                    _FULLSCREEN = False
                    try:
                        screen = pygame.display.set_mode((_W, _H), pygame.RESIZABLE)
                    except pygame.error:
                        pass
                    continue
                elif action == "fullscreen":
                    from settings import WIDTH as _W, HEIGHT as _H
                    _FULLSCREEN = not _FULLSCREEN
                    try:
                        if _FULLSCREEN:
                            screen = pygame.display.set_mode((_W, _H),
                                    pygame.FULLSCREEN | pygame.SCALED)
                        else:
                            screen = pygame.display.set_mode((_W, _H))
                    except pygame.error:
                        pass
                    continue

            elif state == "pc":
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    r = pc.handle_click(*pygame.mouse.get_pos(), button=1)
                    if r == "shutdown":
                        if interior:
                            interior.pc_on = False
                        state = "interior"
                        os_sounds.play("shutdown")
                elif event.type == pygame.MOUSEBUTTONUP:
                    pc.mouse_up()
                elif event.type == pygame.MOUSEMOTION:
                    pc.mouse_motion(*pygame.mouse.get_pos())

        # ============ UPDATE ============
        if state == "title":
            title_screen.update(dt)
            if title_screen.done:
                state = "menu"
        elif state == "menu":
            game_menu.update(dt)
            if game_menu.result == "start":
                state = "world"
                game_menu.result = None
            elif game_menu.result == "exit":
                running = False
        elif state == "world":
            if getattr(World, "_test_mode", False):
                pass  # тестер — игрок стоит
            else:
                player.update(keys, world.can_walk)
                camera.follow(player.rect, world.w * TILE, world.h * TILE)
                for v in world.villagers:
                    v.update()
                world.update_animals()
        elif state == "interior" and interior:
            player.update(keys, interior.can_walk)
            interior.update(dt)
            # Центрируем комнату (может быть отрицательный offset)
            camera.x = (interior.w * TILE - WIDTH) // 2
            camera.y = (interior.h * TILE - HEIGHT) // 2
        elif state == "pc_boot":
            if boot_screen:
                boot_screen.update(dt)
                if boot_screen.done:
                    login_screen = LoginScreen(font_big, font_small)
                    state = "pc_login"
        elif state == "pc_login":
            if login_screen:
                login_screen.update(dt)
                if login_screen.done:
                    state = "pc"
        elif state == "pc":
            pc.update(keys, dt)

        if toast_timer > 0:
            toast_timer -= 1

        # ============ DRAW ============
        screen.fill((0, 0, 0))

        # Показываем системный курсор во всех режимах (быстрее чем свой)
        pygame.mouse.set_visible(True)

        if state == "title":
            title_screen.draw(screen)
        elif state == "menu":
            game_menu.draw(screen)
        elif state == "pc_boot" and boot_screen:
            boot_screen.draw(screen)
        elif state == "pc_login" and login_screen:
            login_screen.draw(screen)
        elif state == "pc":
            pc.draw(screen)
        elif state == "map":
            draw_big_map(screen, world, player, font_big, font_small)
        elif state == "world":
            world.draw(screen, camera)
            world.draw_animals(screen, camera, font_tiny)
            world.draw_villagers(screen, camera, font_tiny)
            player.draw(screen, camera.x, camera.y)
            draw_ingame_bar(screen, font_small, (pc.cursor_x, pc.cursor_y))
            # Тестер координат
            if getattr(World, "_test_mode", False) and hasattr(World, "_tile_coords"):
                k = getattr(World, "_test_key", "grass")
                coord = World._tile_coords[k]
                txt = f"[{k}: {coord[0]},{coord[1]}]  G-категория  WASD-двигать  T-выход"
                s = font_small.render(txt, True, (255, 100, 100))
                bg = pygame.Surface((s.get_width() + 10, s.get_height() + 4), pygame.SRCALPHA)
                bg.fill((0, 0, 0, 200))
                screen.blit(bg, (10, 60))
                screen.blit(s, (15, 62))
        elif state == "interior" and interior:
            interior.draw(screen, camera.x, camera.y, font_tiny)
            player.draw(screen, camera.x, camera.y)
            draw_ingame_bar(screen, font_small, (pc.cursor_x, pc.cursor_y))
        elif state == "ingame_settings":
            # Рисуем замороженный мир в фоне
            if prev_ingame_state == "interior" and interior:
                interior.draw(screen, camera.x, camera.y, font_tiny)
                player.draw(screen, camera.x, camera.y)
            else:
                world.draw(screen, camera)
                world.draw_villagers(screen, camera, font_tiny)
                player.draw(screen, camera.x, camera.y)
            # Настройки сверху
            game_menu.draw(screen)

        # (debug надпись убрана)

        # Toast
        if toast and toast_timer > 0:
            txt = font_big.render(toast, True, (255, 240, 120))
            bg = pygame.Surface((txt.get_width() + 30, txt.get_height() + 16), pygame.SRCALPHA)
            bg.fill((20, 15, 40, 220))
            pygame.draw.rect(bg, (255, 220, 80, 255), (0, 0, bg.get_width(), bg.get_height()), 2)
            x = WIDTH // 2 - bg.get_width() // 2
            y = 30
            screen.blit(bg, (x, y))
            screen.blit(txt, (x + 15, y + 8))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
