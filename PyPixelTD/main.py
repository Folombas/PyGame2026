"""PyPixel TopDown — зайка, деревня, дом с ПК."""
import sys
import pygame

from settings import *
from world_td import World, Camera, TILE
from player_td import PlayerTD
from interior import Interior
from pc_ui import MiniPC
from boot import BootScreen, LoginScreen
from title import TitleScreen
from game_menu import GameMenu
import os_sounds


def make_world_map_surface(world):
    """Рендер карты мира в Surface для окна браузера."""
    s = 8
    surf = pygame.Surface((world.w * s, world.h * s))
    surf.fill((15, 20, 35))
    from world_td import T_GRASS, T_PATH, T_WATER, T_STONE, T_TREE, T_FLOWER
    colors = {
        T_GRASS: (60, 130, 70), T_PATH: (180, 160, 120),
        T_WATER: (60, 130, 200), T_STONE: (110, 110, 120),
        T_TREE: (30, 90, 50), T_FLOWER: (180, 160, 100),
    }
    for ty in range(world.h):
        for tx in range(world.w):
            t = world.tiles[ty][tx]
            pygame.draw.rect(surf, colors.get(t, (60, 130, 70)), (tx * s, ty * s, s, s))
    for h in world.houses:
        pygame.draw.rect(surf, (200, 90, 80), (h.tx * s, h.ty * s, h.w * s, h.h * s))
    return surf


def draw_big_map(screen, world, player, font_big, font_small):
    """Полноэкранная карта (клавиша M)."""
    screen.fill((15, 20, 35))
    map_w = world.w * 10
    map_h = world.h * 10
    x0 = (WIDTH - map_w) // 2
    y0 = (HEIGHT - map_h) // 2
    pygame.draw.rect(screen, (60, 50, 80), (x0 - 4, y0 - 4, map_w + 8, map_h + 8))
    pygame.draw.rect(screen, UI_BORDER, (x0 - 4, y0 - 4, map_w + 8, map_h + 8), 2)

    from world_td import T_GRASS, T_PATH, T_WATER, T_STONE, T_TREE, T_FLOWER
    colors = {
        T_GRASS: (60, 130, 70), T_PATH: (180, 160, 120),
        T_WATER: (60, 130, 200), T_STONE: (110, 110, 120),
        T_TREE: (30, 90, 50), T_FLOWER: (180, 160, 100),
    }
    s = 10
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

    title = font_big.render("КАРТА МИРА", True, UI_TEXT)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))
    hint = font_small.render("M или Esc — закрыть", True, (200, 200, 180))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))


def main():
    pygame.init()
    os_sounds.init()
    # FULLSCREEN | SCALED для правильного масштаба
    try:
        screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                          pygame.FULLSCREEN | pygame.SCALED)
    except pygame.error:
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("🐰 Зайка — Мир")
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("monospace", 26, bold=True)
    font_small = pygame.font.SysFont("monospace", 14, bold=True)
    font_tiny = pygame.font.SysFont("monospace", 12, bold=True)

    world = World()
    camera = Camera()
    player = PlayerTD(15, 22)

    # Карта мира — рендер один раз
    map_surface = make_world_map_surface(world)
    pc = MiniPC(font_small, font_big, map_surface)

    interior = None
    interior_return = None
    # title → menu → world → interior → map → pc_boot → pc
    state = "title"
    toast = None
    toast_timer = 0

    title_screen = TitleScreen(font_big, font_small)
    game_menu = GameMenu(font_big, font_small)
    boot_screen = None     # создастся при включении ПК
    login_screen = None

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ============ EVENTS ============
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if state == "menu":
                    game_menu.handle_event(event)
                    continue
                if event.key == pygame.K_ESCAPE:
                    if state in ("title", "pc_boot", "pc_login"):
                        state = "menu" if state == "title" else "interior"
                    elif state == "menu":
                        running = False
                    elif state == "pc":
                        # Выключаем ПК
                        if interior:
                            interior.pc_on = False
                        state = "interior"
                        toast = "ПК выключен"
                        toast_timer = 100
                    elif state == "map":
                        state = "world"
                    elif state == "interior":
                        running = False
                    else:
                        running = False

                elif event.key == pygame.K_m:
                    if state == "map":
                        state = "world"
                    elif state == "world":
                        state = "map"

                elif event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                    if state == "world":
                        _try_interact_world(world, player)
                        # Проверяем — не вошли ли в дом
                        pending = getattr(world, "_pending_enter", None)
                        if pending:
                            interior = Interior(house_index=world.houses.index(pending))
                            interior_return = (player.x, player.y)
                            player.x = interior.exit_tx * TILE + (TILE - player.w) // 2
                            player.y = (interior.exit_ty - 1) * TILE + (TILE - player.h)
                            player.direction = "up"
                            state = "interior"
                            toast = f"Вошли в дом"
                            toast_timer = 100
                            world._pending_enter = None
                    elif state == "interior" and interior:
                        result = _try_interact_interior(interior, player,
                                                       lambda: None)
                        if result == "pc":
                            if interior.pc_on:
                                # Запускаем загрузку BunnyOS
                                boot_screen = BootScreen(font_big, font_small)
                                login_screen = None
                                state = "pc_boot"
                                toast = "BunnyOS загружается..."
                                toast_timer = 120
                        # Проверяем выход из дома
                        p_rect = player.rect
                        door_rect = pygame.Rect(interior.exit_tx * TILE,
                                                interior.exit_ty * TILE, TILE, TILE)
                        if door_rect.colliderect(p_rect):
                            state = "world"
                            if interior_return:
                                player.x, player.y = interior_return
                            interior = None
                            toast = "Вышли из дома"
                            toast_timer = 100

            elif event.type == pygame.MOUSEBUTTONDOWN and state == "pc":
                if event.button == 1:
                    pc.handle_click(*pygame.mouse.get_pos(), button=1)
            elif event.type == pygame.MOUSEBUTTONUP and state == "pc":
                pc.handle_mouse_up()
            elif event.type == pygame.MOUSEMOTION and state == "pc":
                pc.handle_mouse_motion(*pygame.mouse.get_pos())

        # ============ UPDATE ============
        keys = pygame.key.get_pressed()

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
        elif state == "pc_boot":
            if boot_screen:
                boot_screen.update(dt)
                if boot_screen.done:
                    state = "pc_login"
                    login_screen = LoginScreen(font_big, font_small)
        elif state == "pc_login":
            if login_screen:
                login_screen.update(dt)
                if login_screen.done:
                    state = "pc"
        elif state == "pc":
            pc.update(keys, dt)
        elif state == "world":
            player.update(keys, world.can_walk)
            camera.follow(player.rect, world.w * TILE, world.h * TILE)
            for v in world.villagers:
                v.update()
        elif state == "interior" and interior:
            player.update(keys, interior.can_walk)
            interior.update(dt)
            room_w = interior.w * TILE
            room_h = interior.h * TILE
            camera.x = max(0, room_w // 2 - WIDTH // 2)
            camera.y = max(0, room_h // 2 - HEIGHT // 2)

        if toast_timer > 0:
            toast_timer -= 1

        # ============ DRAW ============
        screen.fill(BG)

        if state == "boot":
            boot_screen.draw(screen)
        elif state == "login":
            login_screen.draw(screen)
        elif state == "map":
            draw_big_map(screen, world, player, font_big, font_small)
        elif state == "world":
            world.draw(screen, camera)
            world.draw_villagers(screen, camera, font_tiny)
            player.draw(screen, camera.x, camera.y)
            _draw_hint(screen, font_small,
                       "WASD — ходить   E — говорить/зайти   M — карта   Esc — выход")
        elif state == "interior" and interior:
            interior.draw(screen, camera.x, camera.y, font_tiny)
            player.draw(screen, camera.x, camera.y)
            _draw_hint(screen, font_small,
                       "WASD — ходить   E — сесть/включить ПК / выйти   Esc — выход")
        elif state == "pc":
            pc.draw(screen)

        # Тост
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


def _draw_hint(screen, font_small, text):
    hint = font_small.render(text, True, (220, 220, 220))
    bg = pygame.Surface((hint.get_width() + 20, hint.get_height() + 10), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 160))
    screen.blit(bg, (20, HEIGHT - 50))
    screen.blit(hint, (30, HEIGHT - 45))


def _try_interact_world(world, player):
    """Взаимодействие с миром: дом, NPC."""
    p_rect = player.rect
    for h in world.houses:
        dr = h.door_rect_px().inflate(20, 20)
        if dr.colliderect(p_rect):
            world._pending_enter = h
            return
    for v in world.villagers:
        dx = (v.tx * TILE + TILE // 2) - (player.x + player.w // 2)
        dy = (v.ty * TILE + TILE // 2) - (player.y + player.h // 2)
        if dx * dx + dy * dy < 60 * 60:
            import random as _r
            lines = [
                f"Привет, я {v.name}!",
                "Зайка, ты уже покормил грядки?",
                "Компьютер в доме — вещь! Интернет, карты...",
                "У озера видели что-то странное.",
                "Осторожнее на востоке.",
            ]
            v.say(_r.choice(lines), frames=180)
            break


def _try_interact_interior(interior, player, enter_pc_fn):
    """Взаимодействие внутри дома: сесть, включить ПК, выйти."""
    p_rect = player.rect
    # Стул рядом?
    if interior.chair_rect().colliderect(p_rect):
        if not interior.sitting:
            interior.sitting = True
            # Ставим игрока на стул
            player.x = interior.chair.x + (interior.chair.w - player.w) // 2
            player.y = interior.chair.y + (interior.chair.h - player.h) // 2
            player.direction = "up"
            return "sat"
        else:
            # Сидит — переключаем ПК
            interior.pc_on = not interior.pc_on
            if interior.pc_on:
                enter_pc_fn()
            return "pc"
    else:
        # Если игрок отошёл — перестаёт сидеть
        if interior.sitting:
            # проверяем что игрок всё ещё на стуле
            if not interior.chair_rect().colliderect(p_rect):
                interior.sitting = False
    return None


_pending_pc_entry = None

def _enter_pc(interior, toast_fn):
    global _pending_pc_entry
    _pending_pc_entry = True


if __name__ == "__main__":
    main()
