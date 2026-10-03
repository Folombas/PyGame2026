"""PyPixel TopDown — игрок ходит по миру сверху."""
import sys
import pygame

from settings import *
from world_td import World, Camera, TILE
from player_td import PlayerTD
from interior import Interior


def draw_map_screen(screen, world, player, font_big, font_small, camera):
    """Полноэкранная карта мира."""
    screen.fill((15, 20, 35))

    # Масштаб карты
    map_w = 60 * 8    # 8 px на тайл
    map_h = 45 * 8
    x0 = (WIDTH - map_w) // 2
    y0 = (HEIGHT - map_h) // 2

    # Рамка
    pygame.draw.rect(screen, (60, 50, 80), (x0 - 4, y0 - 4, map_w + 8, map_h + 8))
    pygame.draw.rect(screen, UI_BORDER, (x0 - 4, y0 - 4, map_w + 8, map_h + 8), 2)

    # Тайлы
    from world_td import T_GRASS, T_PATH, T_WATER, T_STONE, T_TREE, T_FLOWER
    colors = {
        T_GRASS: (60, 130, 70),
        T_PATH: (180, 160, 120),
        T_WATER: (60, 130, 200),
        T_STONE: (110, 110, 120),
        T_TREE: (30, 90, 50),
        T_FLOWER: (180, 160, 100),
    }
    s = 8
    for ty in range(world.h):
        for tx in range(world.w):
            t = world.tiles[ty][tx]
            pygame.draw.rect(screen, colors.get(t, (60, 130, 70)),
                             (x0 + tx * s, y0 + ty * s, s, s))

    # Дома — красные квадраты
    for h in world.houses:
        pygame.draw.rect(screen, (200, 90, 80),
                         (x0 + h.tx * s, y0 + h.ty * s, h.w * s, h.h * s))
        pygame.draw.rect(screen, (255, 240, 200),
                         (x0 + h.door_tx * s, y0 + h.door_ty * s, s, s))

    # Жители
    for v in world.villagers:
        pygame.draw.circle(screen, (240, 220, 80),
                           (x0 + v.tx * s + s // 2, y0 + v.ty * s + s // 2), 3)

    # Игрок
    ptx = int(player.x + player.w // 2) // TILE
    pty = int(player.y + player.h // 2) // TILE
    px = x0 + ptx * s + s // 2
    py = y0 + pty * s + s // 2
    pygame.draw.circle(screen, (100, 240, 255), (px, py), 6)
    pygame.draw.circle(screen, (255, 255, 255), (px, py), 6, 2)

    # Заголовок
    title = font_big.render("КАРТА МИРА", True, UI_TEXT)
    screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 20))

    hint = font_small.render("M или Esc — закрыть", True, (200, 200, 180))
    screen.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT - 40))

    # Легенда
    legend = [
        ("🟩 Трава", (60, 130, 70)),
        ("🟫 Тропа", (180, 160, 120)),
        ("🟦 Вода", (60, 130, 200)),
        ("🟥 Дома", (200, 90, 80)),
        ("🟡 Жители", (240, 220, 80)),
        ("🔵 Ты", (100, 240, 255)),
    ]
    ly = 60
    for label, col in legend:
        pygame.draw.rect(screen, col, (WIDTH - 160, ly, 14, 14))
        txt = font_small.render(label, True, UI_TEXT)
        screen.blit(txt, (WIDTH - 140, ly - 2))
        ly += 22


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("PyPixel TopDown")
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("monospace", 26, bold=True)
    font_small = pygame.font.SysFont("monospace", 14, bold=True)
    font_tiny = pygame.font.SysFont("monospace", 12, bold=True)

    world = World()
    camera = Camera()

    # Игрок спавн — рядом с началом тропы
    player = PlayerTD(15, 22)

    interior = None
    interior_player_pos = None  # для возврата наружу
    state = "world"   # world | interior | map
    toast = None
    toast_timer = 0

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0

        # ============ EVENTS ============
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if state == "map":
                        state = "world"
                    elif state == "interior":
                        # Выходим через дверь
                        pass
                    else:
                        running = False

                elif event.key == pygame.K_m:
                    if state == "map":
                        state = "world"
                    elif state == "world":
                        state = "map"

                elif event.key in (pygame.K_e, pygame.K_SPACE, pygame.K_RETURN):
                    # Взаимодействие
                    if state == "world":
                        # Проверка дома (дверь рядом)
                        p_rect = player.rect
                        for h in world.houses:
                            dr = h.door_rect_px().inflate(20, 20)
                            if dr.colliderect(p_rect):
                                # Войти
                                interior = Interior(house_index=world.houses.index(h))
                                interior_player_pos = (player.x, player.y)
                                # Игрок появляется перед дверью (центр снизу)
                                player.x = interior.exit_tx * TILE + (TILE - player.w) // 2
                                player.y = (interior.exit_ty - 1) * TILE + (TILE - player.h)
                                player.direction = "up"
                                state = "interior"
                                toast = f"Вошли в дом #{world.houses.index(h)+1}"
                                toast_timer = 120
                                break
                        else:
                            # Проверка NPC рядом
                            for v in world.villagers:
                                dx = (v.tx * TILE + TILE // 2) - (player.x + player.w // 2)
                                dy = (v.ty * TILE + TILE // 2) - (player.y + player.h // 2)
                                if dx * dx + dy * dy < 60 * 60:
                                    import random as _r
                                    lines = [
                                        f"Привет, я {v.name}!",
                                        "Хочешь прогуляться по деревне?",
                                        "Дома — заходи, там уютно.",
                                        "Справа озеро, слева пруд.",
                                        "Говорят, на востоке — руины...",
                                    ]
                                    v.say(_r.choice(lines), frames=180)
                                    break

                    elif state == "interior":
                        # Выход из дома через дверь
                        p_rect = player.rect
                        # Локальный тайл двери
                        door_rect = pygame.Rect(interior.exit_tx * TILE,
                                                interior.exit_ty * TILE,
                                                TILE, TILE)
                        if door_rect.colliderect(p_rect):
                            # Возвращаемся на улицу
                            state = "world"
                            if interior_player_pos:
                                player.x, player.y = interior_player_pos
                            interior = None
                            toast = "Вышли на улицу"
                            toast_timer = 100

        # ============ UPDATE ============
        keys = pygame.key.get_pressed()

        if state == "world":
            player.update(keys, world.can_walk)
            camera.follow(player.rect, world.w * TILE, world.h * TILE)
            for v in world.villagers:
                v.update()
        elif state == "interior":
            player.update(keys, interior.can_walk)
            # Камера — центруем комнату
            room_w = interior.w * TILE
            room_h = interior.h * TILE
            camera.x = max(0, room_w // 2 - WIDTH // 2)
            camera.y = max(0, room_h // 2 - HEIGHT // 2)

        if toast_timer > 0:
            toast_timer -= 1

        # ============ DRAW ============
        screen.fill(BG)

        if state == "map":
            draw_map_screen(screen, world, player, font_big, font_small, camera)
        elif state == "world":
            world.draw(screen, camera)
            world.draw_villagers(screen, camera, font_tiny)
            player.draw(screen, camera.x, camera.y)
            # HUD
            hint = font_small.render("WASD — ходить   E — говорить/зайти   M — карта   Esc — выход",
                                     True, (220, 220, 220))
            bg = pygame.Surface((hint.get_width() + 20, hint.get_height() + 10), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            screen.blit(bg, (20, HEIGHT - 50))
            screen.blit(hint, (30, HEIGHT - 45))
        elif state == "interior":
            interior.draw(screen, camera.x, camera.y)
            player.draw(screen, camera.x, camera.y)
            hint = font_small.render("E у двери — выйти из дома", True, (220, 220, 220))
            bg = pygame.Surface((hint.get_width() + 20, hint.get_height() + 10), pygame.SRCALPHA)
            bg.fill((0, 0, 0, 160))
            screen.blit(bg, (20, HEIGHT - 50))
            screen.blit(hint, (30, HEIGHT - 45))

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


if __name__ == "__main__":
    main()
