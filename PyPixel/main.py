"""PyPixel — бесконечный процедурный платформер."""
import sys
import random
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, TITLE, TEXT_COLOR,
    LIVES, HEART_COLOR, HEART_EMPTY_COLOR,
    INVULN_TIME, DIFFICULTIES, DEFAULT_DIFFICULTY,
    HP_BAR_BG, HP_BAR_BORDER, HP_COLOR_HIGH, HP_COLOR_MID, HP_COLOR_LOW,
)
from player import Player
from camera import Camera
from menu import Menu
from world import (
    World, surface_y, DEATH_Y, SURFACE_Y,
    get_ambient_temp, weather_zone,
)
from weather import Weather
from background import draw_sky_gradient, draw_mountains, draw_fog_between_layers
from terrain import draw_terrain_polygon, draw_surface_details
from records import save_record
from inventory import Inventory, SLOTS
from crafting import CraftingUI
from card_book import CardBook
from achievements import AchievementsUI
from cards import roll_card, CARD_DEFS
from tools import TOOLS, PICKAXE, AXE, SWORD, draw_tool_icon, get_tool_sprite, get_tool_sprite_rotated
from particles import ParticleSystem
from tools import BOW
from arrows import Arrow
import math
from blocks import BLOCKS, TILE_SIZE, draw_block, draw_dig_progress, AIR, WOOD
from blocks import DIRT as B_DIRT
import sounds
import sound_settings


# ---------- ФОН ----------
def draw_cloud(surface, cx, cy, size, color=(255, 255, 255)):
    w, h = size, size // 3
    pygame.draw.ellipse(surface, color, (cx - w // 2, cy - h // 4, w, h))
    pygame.draw.ellipse(surface, color, (cx - w // 3, cy - h // 2, w // 2, h))
    pygame.draw.ellipse(surface, color, (cx, cy - h // 2, w // 2, h))
    pygame.draw.ellipse(surface, color, (cx - w // 4, cy - h + h // 2, w // 3, h))


def draw_background(screen, camera):
    """Многослойный фон: небо → дальние горы → туман."""
    draw_sky_gradient(screen, camera)
    draw_mountains(screen, camera)
    draw_fog_between_layers(screen, camera, strength=0.10)

    # Облака
    ox = camera.offset_x
    oy = camera.offset_y
    for i in range(40):
        cx_world = i * 350 + (i * 137) % 200 - 100
        cy_world = 200 + (i * 211) % 800
        size = 50 + (i * 31) % 50
        layer = 0.2 + (i % 3) * 0.2
        sx = int(cx_world - ox * layer)
        sy = int(cy_world - oy * 0.6)
        if -size < sx < WIDTH + size and -size < sy < HEIGHT + size:
            draw_cloud(screen, sx + 3, sy + 3, size, (200, 210, 225))
            draw_cloud(screen, sx, sy, size, (255, 255, 255))


# ---------- HUD ----------
def draw_pixel_heart(surface, x, y, scale, color):
    pattern = [" xx xx ", "xxxxxxx", "xxxxxxx", " xxxxx ", "  xxx  ", "   x   "]
    for row, line in enumerate(pattern):
        for col, ch in enumerate(line):
            if ch == "x":
                pygame.draw.rect(surface, color,
                                 (x + col * scale, y + row * scale, scale, scale))


def draw_hearts(screen, lives, max_lives):
    scale = 3
    gap = 8
    hw = 7 * scale
    for i in range(max_lives):
        color = HEART_COLOR if i < lives else HEART_EMPTY_COLOR
        draw_pixel_heart(screen, 14 + i * (hw + gap), 12, scale, color)


def draw_health_bar(screen, font_small, hp, max_hp):
    x, y = 14, 46
    w, h = 200, 16
    pygame.draw.rect(screen, HP_BAR_BORDER, (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(screen, HP_BAR_BG, (x, y, w, h))
    ratio = max(0.0, hp / max_hp)
    fill = int(w * ratio)
    if ratio > 0.6:
        c = HP_COLOR_HIGH
    elif ratio > 0.3:
        c = HP_COLOR_MID
    else:
        c = HP_COLOR_LOW
    if fill > 0:
        pygame.draw.rect(screen, c, (x, y, fill, h))
    label = font_small.render(f"HP {max(0, hp)}/{max_hp}", True, (255, 255, 255))
    screen.blit(label, (x + 8, y + 1))


def draw_hotbar(screen, font_small, inventory):
    """Хотбар внизу экрана."""
    box = 48
    gap = 4
    total = SLOTS * box + (SLOTS - 1) * gap
    x0 = (WIDTH - total) // 2
    y0 = HEIGHT - box - 16

    for i in range(SLOTS):
        x = x0 + i * (box + gap)
        selected = (i == inventory.selected)
        bg = (60, 50, 70) if selected else (35, 30, 45)
        border = (255, 240, 120) if selected else (110, 100, 130)
        pygame.draw.rect(screen, bg, (x, y0, box, box))
        pygame.draw.rect(screen, border, (x, y0, box, box), 2 if selected else 1)

        slot = inventory.slots[i]
        if slot:
            rect = pygame.Rect(x + 6, y0 + 6, box - 12, box - 12)
            if "tool" in slot:
                draw_tool_icon(screen, rect, slot["tool"])
            else:
                draw_block(screen, rect, slot["type"])
                cnt = font_small.render(str(slot["count"]), True, (255, 255, 255))
                screen.blit(cnt, (x + box - cnt.get_width() - 4, y0 + box - 20))

        # номер слота
        num = font_small.render(str((i + 1) % 10), True, (180, 180, 200))
        screen.blit(num, (x + 4, y0 + 2))


def draw_temperature_bar(screen, font_small, body_temp):
    x, y = 14, 68
    w, h = 200, 14
    pygame.draw.rect(screen, (30, 30, 45), (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(screen, (90, 110, 140), (x - 2, y - 2, w + 4, h + 4), 1)
    pygame.draw.rect(screen, (20, 20, 30), (x, y, w, h))

    ratio = max(0.0, min(1.0, body_temp / 100.0))
    fill = int(w * ratio)
    # Градиент: холодный — синий, нормальный — зелёный, тёплый — жёлтый
    if ratio < 0.3:
        color = (90, 140, 220)   # холодно
    elif ratio < 0.6:
        color = (140, 200, 240)
    else:
        color = (240, 180, 100)  # тепло
    if fill > 0:
        pygame.draw.rect(screen, color, (x, y, fill, h))

    label = font_small.render(f"Темп. тела  {int(body_temp)}°", True, (255, 255, 255))
    screen.blit(label, (x + 6, y - 1))


def draw_hud(screen, font_big, font_small, L, lives, difficulty_key):
    distance = max(0, L["max_x"]) // 10
    depth = max(0, L["max_y"] - SURFACE_Y) // 10

    score_txt = font_big.render(f"Очки: {L['score']}", True, TEXT_COLOR)
    screen.blit(score_txt, (WIDTH - score_txt.get_width() - 20, 15))

    zone_names = {
        "freezing": "❄ Вьюга",
        "snow": "🌨 Снега",
        "cold": "Холод",
        "mild": "Погода",
        "cave_warm": "Пещеры",
        "cave_hot": "Лава",
    }
    zone = zone_names.get(weather_zone(L["player"].rect.centery), "")
    stats = (f"Дистанция: {distance} м   Глубина: {depth} м   "
             f"{zone}   Враги: {L['kills']}   Яблоки: {L['apples']}")
    s = font_small.render(stats, True, TEXT_COLOR)
    screen.blit(s, (WIDTH - s.get_width() - 20, 55))

    draw_hearts(screen, lives, DIFFICULTIES[difficulty_key]["lives"])
    draw_health_bar(screen, font_small, L["hp"], L["max_hp"])
    draw_temperature_bar(screen, font_small, L["body_temp"])

    draw_hotbar(screen, font_small, L["inventory"])

    if L["state"] == "game_over":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))
        txt = font_big.render("GAME OVER", True, (240, 90, 90))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 60))
        info = font_small.render(
            f"Дистанция: {distance} м   Глубина: {depth} м",
            True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 - 10))
        info2 = font_small.render("R — заново    M — меню    Esc — выход", True, TEXT_COLOR)
        screen.blit(info2, (WIDTH // 2 - info2.get_width() // 2, HEIGHT // 2 + 30))

    elif L["state"] == "paused":
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        screen.blit(overlay, (0, 0))
        txt = font_big.render("ПАУЗА", True, (255, 240, 120))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 60))
        info = font_small.render("Esc — продолжить    M — в меню", True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 10))


# ---------- ЗАПУСК УРОВНЯ-СЕССИИ ----------
def new_session(difficulty):
    player = Player(x=0, y=surface_y(0) - 100)
    camera = Camera(WIDTH)
    camera.update(player.rect)
    inv = Inventory()
    inv.add_tool(PICKAXE)
    inv.add_tool(AXE)
    inv.add_tool(SWORD)
    inv.add_tool(BOW)
    return {
        "player": player,
        "camera": camera,
        "world": World(difficulty),
        "hp": difficulty["max_hp"],
        "max_hp": difficulty["max_hp"],
        "hit_damage": difficulty["hit_damage"],
        "score": 0,
        "kills": 0,
        "apples": 0,
        "invuln": 0,
        "max_x": 0,
        "max_y": surface_y(0),
        "state": "playing",
        "body_temp": 100.0,
        "freeze_tick": 0,
        "weather": Weather(),
        "inventory": inv,
        "mining": None,            # {"tx", "ty", "progress"}
        "particles": ParticleSystem(),
        "swing_timer": 0,
        "swing_angle": 0,
        "arrows": [],
        "bow_cooldown": 0,
        "cards": set(),
        "card_toast": None,
        "card_toast_timer": 0,
        "blocks_dug": 0,
        "trees_chopped": 0,
        "arrows_hit": 0,
        "max_depth": 0,
        "boss_killed": 0,
        "unlocked": set(),
        "achievement_toast": None,
        "achievement_toast_timer": 0,
    }




def use_tool_at(L, wx, wy, mx, my):
    """Действие инструментом в точке. Вызывается из ЛКМ и клавиши E/F."""
    sel_tool = L["inventory"].selected_tool()
    if not sel_tool:
        return
    L["swing_timer"] = 12

    if sel_tool == SWORD:
        sword_range = TOOLS[SWORD]["attack_range_px"]
        _, enemies, _, _, _ = L["world"].collect()
        hit_any = False
        for e in enemies:
            if not e.alive:
                continue
            dx = e.rect.centerx - L["player"].rect.centerx
            dy = e.rect.centery - L["player"].rect.centery
            if abs(dx) < sword_range and abs(dy) < sword_range:
                e.alive = False
                L["kills"] += 1
                L["score"] += 5
                hit_any = True
                L["particles"].spawn_blood(e.rect.centerx, e.rect.centery, count=16)
        sounds.play("stomp" if hit_any else "hit")
        if hit_any:
            cid = roll_card("enemy", L["cards"])
            if cid:
                L["cards"].add(cid)
                L["card_toast"] = cid
                L["card_toast_timer"] = 180

    elif sel_tool == AXE:
        pos = L["world"].chop_tree(wx, wy, radius_px=140)
        if pos:
            L["inventory"].add(WOOD, 4)
            L["score"] += 3
            L["trees_chopped"] += 1
            L["particles"].spawn_leaves(pos[0], pos[1], count=20)
            L["particles"].spawn_dirt(pos[0], pos[1], count=10, color=(110, 70, 40))
            sounds.play("stomp")

    elif sel_tool == BOW:
        if L.get("bow_cooldown", 0) > 0:
            return
        px = L["player"].rect.centerx
        py = L["player"].rect.centery
        dx = mx - px
        dy = my - py
        dist = math.hypot(dx, dy) or 1
        speed = 13
        vx = dx / dist * speed
        vy = dy / dist * speed
        L.setdefault("arrows", []).append(Arrow(px, py, vx, vy))
        L["bow_cooldown"] = TOOLS[BOW]["cooldown"]
        sounds.play("jump")


def draw_card_toast(screen, font_big, font_small, L):
    """Всплывашка о новой карточке в углу."""
    if L["card_toast_timer"] <= 0 or not L["card_toast"]:
        return
    from cards import CARD_DEFS, RARITY, draw_card_icon
    cid = L["card_toast"]
    info = CARD_DEFS[cid]
    rar = RARITY[info["rarity"]]

    # анимация выезда
    t = L["card_toast_timer"]
    slide = min(1.0, (180 - t) / 20.0)   # выезжает
    fade = min(1.0, t / 40.0)            # исчезает

    box_w = 300
    box_h = 90
    x = WIDTH - box_w - 20
    y = int(20 + (1 - slide) * -120)
    if fade < 1:
        y += int((1 - fade) * -20)

    box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box.fill((18, 14, 32, int(240 * fade)))
    pygame.draw.rect(box, (*rar["color"], int(255 * fade)), (0, 0, box_w, box_h), 2)

    # иконка
    icon_rect = pygame.Rect(8, 8, 74, 74)
    draw_card_icon(box, info["icon"], icon_rect)

    # тексты
    t1 = font_small.render("НОВАЯ КАРТОЧКА", True,
                            (255, 240, 120, int(255 * fade)))
    t2 = font_big.render(info["name"], True, (*rar["color"], int(255 * fade)))
    t3 = font_small.render(rar["name"], True, (200, 200, 220, int(255 * fade)))
    box.blit(t1, (92, 10))
    box.blit(t2, (92, 32))
    box.blit(t3, (92, 62))
    screen.blit(box, (x, y))


def draw_achievement_toast(screen, font_big, font_small, L):
    """Тост о новом достижении в центре сверху."""
    if L["achievement_toast_timer"] <= 0 or not L.get("achievement_toast"):
        return
    from achievements import ACHIEVEMENTS
    aid = L["achievement_toast"]
    ach = ACHIEVEMENTS[aid]

    t = L["achievement_toast_timer"]
    fade = min(1.0, t / 60.0)
    slide = min(1.0, (240 - t) / 20.0)

    box_w, box_h = 460, 90
    x = (WIDTH - box_w) // 2
    y = int(-100 + slide * 120)  # выезжает сверху

    box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box.fill((20, 15, 40, int(240 * fade)))
    pygame.draw.rect(box, (255, 220, 80, int(255 * fade)), (0, 0, box_w, box_h), 3)
    pygame.draw.rect(box, (255, 180, 40, int(255 * fade)), (0, 0, box_w, box_h), 1)

    # медаль
    pygame.draw.circle(box, (255, 220, 80, int(255 * fade)), (45, 45), 32)
    pygame.draw.circle(box, (255, 255, 255, int(255 * fade)), (45, 45), 32, 2)
    star = font_big.render("★", True, (60, 40, 20, int(255 * fade)))
    box.blit(star, (45 - star.get_width() // 2, 45 - star.get_height() // 2))

    t1 = font_small.render("🏆 ДОСТИЖЕНИЕ ПОЛУЧЕНО!", True, (255, 240, 150, int(255 * fade)))
    t2 = font_big.render(ach["name"], True, (255, 255, 255, int(255 * fade)))
    box.blit(t1, (90, 12))
    box.blit(t2, (90, 38))

    if ach["reward"] > 0:
        t3 = font_small.render(f"+{ach['reward']} очков", True, (100, 240, 130, int(255 * fade)))
        box.blit(t3, (box_w - 120, 55))

    screen.blit(box, (x, y))


def main():
    pygame.init()
    sounds.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()
    font_big = pygame.font.SysFont("monospace", 28, bold=True)
    font_small = pygame.font.SysFont("monospace", 18)

    menu = Menu(font_big, font_small)
    craft_ui = CraftingUI(font_big, font_small)
    card_book = CardBook(font_big, font_small)
    achievements = AchievementsUI(font_big, font_small)
    app_state = "menu"
    difficulty_key = DEFAULT_DIFFICULTY
    difficulty = DIFFICULTIES[difficulty_key]
    lives = difficulty["lives"]
    L = None

    running = True
    while running:
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if app_state == "playing" and card_book.open:
                if card_book.handle_event(event, L["cards"]):
                    continue
            if app_state == "playing" and achievements.open:
                if achievements.handle_event(event):
                    continue

            if app_state == "menu":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    running = False
                    continue
                action = menu.handle_event(event)
                if action == "start":
                    difficulty_key = menu.difficulty_key
                    difficulty = DIFFICULTIES[difficulty_key]
                    lives = difficulty["lives"]
                    L = new_session(difficulty)
                    app_state = "playing"
                elif action == "quit":
                    running = False
                continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                # если крафт открыт — обрабатываем только его
                if craft_ui.open and L and L["state"] == "playing":
                    craft_ui.handle_mouse(pygame.mouse.get_pos(), True, L["inventory"])
                    continue
                # обрабатываем мышь отдельно (не через key-chain)
                if L and L["state"] == "playing":
                    mx, my = pygame.mouse.get_pos()
                    wx = mx + L["camera"].ox
                    wy = my + L["camera"].oy
                    if event.button == 3:
                        bt = L["inventory"].selected_type()
                        if bt is not None:
                            if L["world"].place(wx, wy, bt):
                                L["inventory"].take_selected(1)
                    elif event.button == 1:
                        use_tool_at(L, wx, wy, mx, my)
                continue

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                if L["state"] == "playing":
                    L["state"] = "paused"
                elif L["state"] == "paused":
                    L["state"] = "playing"
                else:
                    running = False
            elif event.key == pygame.K_m and L["state"] in ("paused", "game_over"):
                app_state = "menu"
            elif event.key == pygame.K_r and L["state"] == "game_over":
                L = new_session(difficulty)
                lives = difficulty["lives"]
            elif event.key == pygame.K_m and L["state"] == "playing":
                # быстрый мьют прямо в игре
                cfg = sound_settings.load()
                cfg["enabled"] = not cfg["enabled"]
                sound_settings.save(cfg)
                sounds.reload_settings()
            elif event.key in (pygame.K_MINUS, pygame.K_KP_MINUS) and L["state"] == "playing":
                cfg = sound_settings.load()
                cfg["volume"] = max(0.0, round(cfg["volume"] - 0.1, 2))
                sound_settings.save(cfg)
                sounds.reload_settings()
            elif event.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS) and L["state"] == "playing":
                cfg = sound_settings.load()
                cfg["volume"] = min(1.0, round(cfg["volume"] + 0.1, 2))
                sound_settings.save(cfg)
                sounds.reload_settings()
                sounds.play("collect")
            elif event.key == pygame.K_c and L["state"] == "playing":
                craft_ui.toggle()
            elif event.key == pygame.K_b and L["state"] == "playing":
                card_book.toggle()
            elif event.key == pygame.K_j and L["state"] == "playing":
                achievements.toggle()
            elif (event.key in (pygame.K_e, pygame.K_f)
                  or event.scancode in (8, 9)) and L["state"] == "playing":
                mx, my = pygame.mouse.get_pos()
                wx = mx + L["camera"].ox
                wy = my + L["camera"].oy
                use_tool_at(L, wx, wy, mx, my)
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                               pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0):
                n = event.key - pygame.K_1
                if n < 0:
                    n = 9
                L["inventory"].select(n)

            # Мышь — копание / установка
        # ============ МЕНЮ ============
        if app_state == "menu":
            menu.update()
            menu.draw(screen)
            pygame.display.flip()
            continue

        # ============ ИГРА ============
        if L["state"] == "playing":
            keys = pygame.key.get_pressed()
            L["player"].handle_input(keys)

            L["world"].update(L["camera"])
            platforms, enemies, pixels, trees, medkits = L["world"].collect()

            L["player"].update(platforms)
            for e in enemies:
                e.update(platforms)
            L["camera"].update(L["player"].rect)

            # обновляем рекордные координаты
            L["max_x"] = max(L["max_x"], L["player"].rect.x)
            L["max_y"] = max(L["max_y"], L["player"].rect.y)
            from world import SURFACE_Y as _SY
            depth = max(0, (L["player"].rect.y - _SY) // 10)
            L["max_depth"] = max(L["max_depth"], depth)

            # --- ТЕМПЕРАТУРА ТЕЛА ---
            ambient = get_ambient_temp(L["player"].rect.centery)
            if L["body_temp"] > ambient:
                # остывает: чем дальше от комфорта, тем быстрее
                delta = (L["body_temp"] - ambient)
                L["body_temp"] -= 0.15 + delta * 0.002
            else:
                L["body_temp"] += 0.25
            L["body_temp"] = max(0.0, min(100.0, L["body_temp"]))

            # обморожение: при body_temp < 15 теряем HP каждые 60 кадров
            L["freeze_tick"] += 1
            if L["body_temp"] < 15 and L["freeze_tick"] >= 60:
                L["freeze_tick"] = 0
                L["hp"] -= 4
                sounds.play("hit")
                if L["hp"] <= 0:
                    lives -= 1
                    if lives <= 0:
                        L["state"] = "game_over"
                        sounds.play("game_over")
                        save_record(L["score"], 0, 0, L["kills"], L["apples"],
                                    L["max_x"] // 10, difficulty_key)
                    else:
                        L["player"] = Player(x=0, y=surface_y(0) - 100)
                        L["camera"] = Camera(WIDTH)
                        L["hp"] = L["max_hp"]
                        L["body_temp"] = 100.0

            # --- ПОГОДА ---
            L["weather"].update(L["camera"].offset_y)

            # --- СТРЕЛЫ ---
            if L.get("bow_cooldown", 0) > 0:
                L["bow_cooldown"] -= 1
            for arr in L.get("arrows", [])[:]:
                hit = arr.update(platforms, enemies)
                if hit is not None:
                    hit.alive = False
                    L["kills"] += 1
                    L["score"] += 5
                    L["particles"].spawn_blood(hit.rect.centerx, hit.rect.centery, count=14)
                    sounds.play("stomp")
                    L["arrows_hit"] += 1
                    cid = roll_card("enemy", L["cards"])
                    if cid:
                        L["cards"].add(cid)
                        L["card_toast"] = cid
                        L["card_toast_timer"] = 180
                if not arr.alive:
                    L["arrows"].remove(arr)

            # --- ВЗМАХ + ЧАСТИЦЫ ---
            if L["swing_timer"] > 0:
                L["swing_timer"] -= 1
                # кривая: быстро вперёд, медленно назад
                t = 1.0 - (L["swing_timer"] / 12.0)
                if t < 0.5:
                    L["swing_angle"] = -60 * (t / 0.5)   # вперёд
                else:
                    L["swing_angle"] = -60 * (1 - (t - 0.5) / 0.5)
            else:
                L["swing_angle"] = 0
            L["particles"].update()

            # --- КОПАНИЕ (ЛКМ удержание) ---
            mouse_pressed = pygame.mouse.get_pressed()
            mx, my = pygame.mouse.get_pos()
            wx = mx + L["camera"].ox
            wy = my + L["camera"].oy
            tx = wx // TILE_SIZE
            ty = wy // TILE_SIZE
            px_tx = L["player"].rect.centerx // TILE_SIZE
            py_ty = L["player"].rect.centery // TILE_SIZE
            dist = max(abs(tx - px_tx), abs(ty - py_ty))

            if mouse_pressed[0] and dist <= 5:
                # поддерживаем анимацию взмаха, пока копаем
                if L["swing_timer"] <= 0 and L["inventory"].selected_tool():
                    L["swing_timer"] = 8
                bt = L["world"].get_block_type(wx, wy)
                if bt is not None and bt != AIR and bt in BLOCKS:
                    if L["mining"] and L["mining"]["tx"] == tx and L["mining"]["ty"] == ty:
                        # скорость зависит от инструмента
                        speed_mult = 1.0
                        sel_tool = L["inventory"].selected_tool()
                        if sel_tool and BLOCKS[bt].get("tool") == sel_tool:
                            speed_mult = TOOLS[sel_tool]["speed"]
                        elif not sel_tool:
                            speed_mult = 0.6   # руками медленнее
                        L["mining"]["progress"] += speed_mult / BLOCKS[bt]["hardness"]
                        if L["mining"]["progress"] >= 1.0:
                            dug = L["world"].dig(wx, wy)
                            if dug is not None:
                                L["inventory"].add(dug, 1)
                                L["score"] += 1
                                L["blocks_dug"] += 1
                                # дроп карточки с руды
                                if dug == 4:      # COPPER
                                    cid = roll_card("ore", L["cards"])
                                elif dug in (5, 6):  # IRON/GOLD
                                    cid = roll_card("gold", L["cards"])
                                else:
                                    cid = None
                                if cid:
                                    L["cards"].add(cid)
                                    L["card_toast"] = cid
                                    L["card_toast_timer"] = 180
                                # частицы по типу блока
                                cx_px = tx * TILE_SIZE + TILE_SIZE // 2
                                cy_px = ty * TILE_SIZE + TILE_SIZE // 2
                                if dug in (3, 4, 5, 6):   # STONE/COPPER/IRON/GOLD
                                    L["particles"].spawn_sparks(cx_px, cy_px, count=10)
                                else:
                                    L["particles"].spawn_dirt(cx_px, cy_px, count=10)
                                sounds.play("collect")
                            L["mining"] = None
                    else:
                        L["mining"] = {"tx": tx, "ty": ty, "progress": 0.0}
            else:
                L["mining"] = None

            if L["invuln"] > 0:
                L["invuln"] -= 1

            # падение в бездну
            if L["player"].rect.top > DEATH_Y:
                lives -= 1
                if lives <= 0:
                    L["state"] = "game_over"
                    sounds.play("game_over")
                    save_record(L["score"], 0, 0, L["kills"], L["apples"],
                                L["max_x"] // 10, difficulty_key)
                else:
                    L["player"] = Player(x=0, y=surface_y(0) - 100)
                    L["camera"] = Camera(WIDTH)
                    L["hp"] = L["max_hp"]
                    sounds.play("hit")

            # пиксели
            for px in pixels:
                if px.alive and L["player"].rect.colliderect(px.rect):
                    px.alive = False
                    L["score"] += 1
                    sounds.play("collect")

            # яблоки
            for tree in trees:
                for idx, arect in tree.apple_world_rects():
                    if L["player"].rect.colliderect(arect):
                        tree.collect(idx)
                        L["apples"] += 1
                        L["score"] += 2
                        sounds.play("collect")
                        cid = roll_card("apple", L["cards"])
                        if cid:
                            L["cards"].add(cid)
                            L["card_toast"] = cid
                            L["card_toast_timer"] = 180

            # аптечки
            for mk in medkits:
                if mk.alive and L["player"].rect.colliderect(mk.rect):
                    mk.alive = False
                    L["hp"] = min(L["hp"] + 30, L["max_hp"])
                    sounds.play("collect")

            # враги
            for e in enemies:
                if not e.alive:
                    continue
                if L["player"].rect.colliderect(e.rect):
                    stomp = (L["player"].vel_y > 0
                             and L["player"].rect.bottom - L["player"].vel_y
                             <= e.rect.top + 8)
                    if stomp:
                        e.alive = False
                        L["player"].vel_y = -12
                        L["kills"] += 1
                        L["score"] += 5
                        sounds.play("stomp")
                    elif L["invuln"] == 0:
                        L["hp"] -= L["hit_damage"]
                        L["invuln"] = INVULN_TIME
                        sounds.play("hit")
                        if L["hp"] <= 0:
                            lives -= 1
                            if lives <= 0:
                                L["state"] = "game_over"
                                sounds.play("game_over")
                                save_record(L["score"], 0, 0, L["kills"], L["apples"],
                                            L["max_x"] // 10, difficulty_key)
                            else:
                                L["player"] = Player(x=0, y=surface_y(0) - 100)
                                L["camera"] = Camera(WIDTH)
                                L["hp"] = L["max_hp"]

        craft_ui.update()
        card_book.update()
        achievements.update()

        # --- проверка разблокировки достижений ---
        if L["state"] == "playing":
            stats = {
                "blocks_dug": L.get("blocks_dug", 0),
                "trees_chopped": L.get("trees_chopped", 0),
                "kills": L.get("kills", 0),
                "arrows_hit": L.get("arrows_hit", 0),
                "apples": L.get("apples", 0),
                "max_x": L.get("max_x", 0) // 10,
                "max_depth": L.get("max_depth", 0),
                "cards_count": len(L.get("cards", set())),
                "boss_killed": L.get("boss_killed", 0),
            }
            new_ach = achievements.check_unlocks(stats, L["unlocked"])
            if new_ach:
                from achievements import ACHIEVEMENTS
                for a in new_ach:
                    L["score"] += ACHIEVEMENTS[a]["reward"]
                L["achievement_toast"] = new_ach[0]
                L["achievement_toast_timer"] = 240
                # короткий звук
                import sounds as _s
                _s.play("victory")

            if L.get("achievement_toast_timer", 0) > 0:
                L["achievement_toast_timer"] -= 1

        # ---- отрисовка ----
        draw_background(screen, L["camera"])
        ox, oy = L["camera"].ox, L["camera"].oy

        platforms, enemies, pixels, trees, medkits = L["world"].collect()

        # --- РЕЛЬЕФ (новый сглаженный) ---
        draw_terrain_polygon(screen, L["camera"])
        draw_surface_details(screen, L["camera"])

        # Все блоки мира
        for p in platforms:
            p.draw(screen, ox, oy)
        for t in trees:
            t.draw(screen, ox, oy)
        for mk in medkits:
            mk.draw(screen, ox, oy)
        for px in pixels:
            px.draw(screen, ox, oy)
        for e in enemies:
            e.draw(screen, ox, oy)

        blink = L["invuln"] > 0 and (L["invuln"] // 4) % 2 == 0
        if not blink:
            L["player"].draw(screen, ox, oy)

        # Инструмент в руке (с анимацией взмаха)
        tool_id = L["inventory"].selected_tool()
        if tool_id:
            angle = L["swing_angle"]
            sprite = get_tool_sprite_rotated(tool_id, 22, int(angle)) if angle else get_tool_sprite(tool_id, 22)
            if sprite:
                pr = L["player"].rect
                if L["player"].facing_right:
                    tx = pr.right - ox - 6
                    ty = pr.centery - oy - sprite.get_height() // 2
                else:
                    # отражение для левого направления
                    sprite = pygame.transform.flip(sprite, True, False)
                    tx = pr.left - ox - sprite.get_width() + 6
                    ty = pr.centery - oy - sprite.get_height() // 2
                screen.blit(sprite, (tx, ty))

        # Стрелы
        for arr in L.get("arrows", []):
            arr.draw(screen, ox, oy)

        # Частицы — поверх мира
        L["particles"].draw(screen, ox, oy)

        # Прогресс копания на блоке
        if L["mining"]:
            mtx = L["mining"]["tx"] * TILE_SIZE
            mty = L["mining"]["ty"] * TILE_SIZE
            mrect = pygame.Rect(mtx, mty, TILE_SIZE, TILE_SIZE)
            draw_dig_progress(screen, mrect, L["mining"]["progress"], (ox, oy))

        # Подсветка блока под курсором
        if L["state"] == "playing":
            mx, my = pygame.mouse.get_pos()
            wx = mx + L["camera"].ox
            wy = my + L["camera"].oy
            htx = (wx // TILE_SIZE) * TILE_SIZE
            hty = (wy // TILE_SIZE) * TILE_SIZE
            hr = pygame.Rect(htx - ox, hty - oy, TILE_SIZE, TILE_SIZE)
            if -TILE_SIZE < hr.x < WIDTH and -TILE_SIZE < hr.y < HEIGHT:
                pygame.draw.rect(screen, (255, 255, 255), hr, 2)

        # Погода — поверх мира, но под HUD
        L["weather"].draw(screen, L["camera"].offset_y)

        draw_hud(screen, font_big, font_small, L, lives, difficulty_key)
        craft_ui.draw(screen, L["inventory"])
        draw_card_toast(screen, font_big, font_small, L)
        card_book.draw(screen, L["cards"])
        stats = {
            "blocks_dug": L["blocks_dug"],
            "trees_chopped": L["trees_chopped"],
            "kills": L["kills"],
            "arrows_hit": L["arrows_hit"],
            "apples": L["apples"],
            "max_x": L["max_x"] // 10,
            "max_depth": L["max_depth"],
            "cards_count": len(L["cards"]),
            "boss_killed": L["boss_killed"],
        }
        achievements.draw(screen, stats, L["unlocked"])
        draw_achievement_toast(screen, font_big, font_small, L)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
