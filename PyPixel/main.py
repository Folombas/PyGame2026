"""PyPixel — бесконечный процедурный платформер в тайловом мире."""
import sys
import math
import random
import pygame

from settings import (
    WIDTH, HEIGHT, FPS, TITLE, TEXT_COLOR,
    HEART_COLOR, HEART_EMPTY_COLOR,
    INVULN_TIME, DIFFICULTIES, DEFAULT_DIFFICULTY,
    HP_BAR_BG, HP_BAR_BORDER, HP_COLOR_HIGH, HP_COLOR_MID, HP_COLOR_LOW,
)
from blocks import BLOCKS, TILE_SIZE, AIR, draw_block, draw_dig_progress, WOOD
from world import World, SURFACE_TY, TILE, DEATH_TY, get_ambient_temp, weather_zone, surface_ty
from player import Player
from enemy import Enemy
from camera import Camera
from inventory import Inventory, SLOTS
from tools import (TOOLS, PICKAXE, AXE, SWORD, BOW,
                   draw_tool_icon, get_tool_sprite, get_tool_sprite_rotated)
from particles import ParticleSystem
from arrows import Arrow
from boat import Boat
from submarine import Submarine
from records import save_record
from menu import Menu
from card_book import CardBook
from crafting import CraftingUI
from achievements import AchievementsUI
from quests import QuestUI
from cards import roll_card, CARD_DEFS
from weather import Weather
from lighting import LightMask, ambient_from_time, sky_colors_from_time
from blocks import TORCH
import sounds
import sound_settings


# ================= ФОН =================
def draw_cloud(surface, cx, cy, size, color=(255, 255, 255)):
    w, h = size, size // 3
    pygame.draw.ellipse(surface, color, (cx - w // 2, cy - h // 4, w, h))
    pygame.draw.ellipse(surface, color, (cx - w // 3, cy - h // 2, w // 2, h))
    pygame.draw.ellipse(surface, color, (cx, cy - h // 2, w // 2, h))
    pygame.draw.ellipse(surface, color, (cx - w // 4, cy - h + h // 2, w // 3, h))


def draw_background(screen, camera, time_of_day=0.5):
    oy = camera.offset_y
    ox = camera.offset_x
    ground_y = SURFACE_TY * TILE - oy

    # Динамическое небо
    sky_top, sky_bot = sky_colors_from_time(time_of_day)
    cave_top = (55, 40, 35)
    cave_bot = (18, 12, 15)

    for y_screen in range(HEIGHT):
        if y_screen < ground_y:
            t = min(1.0, max(0.0, (ground_y - y_screen) / 500.0))
            col = (int(sky_bot[0] * (1 - t) + sky_top[0] * t),
                   int(sky_bot[1] * (1 - t) + sky_top[1] * t),
                   int(sky_bot[2] * (1 - t) + sky_top[2] * t))
        else:
            t = min(1.0, (y_screen - ground_y) / 700.0)
            col = (int(cave_top[0] * (1 - t) + cave_bot[0] * t),
                   int(cave_top[1] * (1 - t) + cave_bot[1] * t),
                   int(cave_top[2] * (1 - t) + cave_bot[2] * t))
        pygame.draw.line(screen, col, (0, y_screen), (WIDTH, y_screen))

    # облака (только над землёй)
    for i in range(30):
        cx_world = i * 420 + (i * 137) % 200 - 100
        cy_world = 150 + (i * 211) % 600
        if cy_world >= SURFACE_TY * TILE - 100:
            continue
        size = 30 + (i * 17) % 30    # 30..60 px — маленькие
        layer = 0.2 + (i % 3) * 0.2
        sx = int(cx_world - ox * layer)
        sy = int(cy_world - oy)
        if -size < sx < WIDTH + size and -size < sy < HEIGHT + size:
            draw_cloud(screen, sx + 2, sy + 2, size, (200, 210, 225))
            draw_cloud(screen, sx, sy, size, (255, 255, 255))


# ================= HUD =================
def draw_pixel_heart(surface, x, y, scale, color):
    pattern = [" xx xx ", "xxxxxxx", "xxxxxxx", " xxxxx ", "  xxx  ", "   x   "]
    for row, line in enumerate(pattern):
        for col, ch in enumerate(line):
            if ch == "x":
                pygame.draw.rect(surface, color,
                                 (x + col * scale, y + row * scale, scale, scale))


def draw_hearts(screen, lives, max_lives):
    scale = 3; gap = 8
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
    c = HP_COLOR_HIGH if ratio > 0.6 else HP_COLOR_MID if ratio > 0.3 else HP_COLOR_LOW
    if fill > 0:
        pygame.draw.rect(screen, c, (x, y, fill, h))
    label = font_small.render(f"HP {max(0, hp)}/{max_hp}", True, (255, 255, 255))
    screen.blit(label, (x + 8, y + 1))


def draw_temperature_bar(screen, font_small, body_temp):
    x, y = 14, 68
    w, h = 200, 14
    pygame.draw.rect(screen, (30, 30, 45), (x - 2, y - 2, w + 4, h + 4))
    pygame.draw.rect(screen, (90, 110, 140), (x - 2, y - 2, w + 4, h + 4), 1)
    pygame.draw.rect(screen, (20, 20, 30), (x, y, w, h))
    ratio = max(0.0, min(1.0, body_temp / 100.0))
    fill = int(w * ratio)
    if ratio < 0.3:   c = (90, 140, 220)
    elif ratio < 0.6: c = (140, 200, 240)
    else:             c = (240, 180, 100)
    if fill > 0:
        pygame.draw.rect(screen, c, (x, y, fill, h))
    lbl = font_small.render(f"Темп. тела  {int(body_temp)}°", True, (255, 255, 255))
    screen.blit(lbl, (x + 6, y - 1))


def draw_hotbar(screen, font_small, inventory):
    box = 48; gap = 4
    total = SLOTS * box + (SLOTS - 1) * gap
    x0 = (WIDTH - total) // 2
    y0 = HEIGHT - box - 16
    for i in range(SLOTS):
        x = x0 + i * (box + gap)
        sel = (i == inventory.selected)
        bg = (60, 50, 70) if sel else (35, 30, 45)
        border = (255, 240, 120) if sel else (110, 100, 130)
        pygame.draw.rect(screen, bg, (x, y0, box, box))
        pygame.draw.rect(screen, border, (x, y0, box, box), 2 if sel else 1)
        slot = inventory.slots[i]
        if slot:
            r = pygame.Rect(x + 6, y0 + 6, box - 12, box - 12)
            if "tool" in slot:
                draw_tool_icon(screen, r, slot["tool"])
            else:
                draw_block(screen, r, slot["type"])
                cnt = font_small.render(str(slot["count"]), True, (255, 255, 255))
                screen.blit(cnt, (x + box - cnt.get_width() - 4, y0 + box - 20))
        num = font_small.render(str((i + 1) % 10), True, (180, 180, 200))
        screen.blit(num, (x + 4, y0 + 2))


def draw_hud(screen, font_big, font_small, L, lives, difficulty_key):
    distance = max(0, L["max_x"]) // 10
    depth = max(0, L["max_depth"])

    score_txt = font_big.render(f"Очки: {L['score']}", True, TEXT_COLOR)
    screen.blit(score_txt, (WIDTH - score_txt.get_width() - 20, 15))

    # часы
    tod = L["world"].time_of_day
    hours = int(tod * 24)
    minutes = int((tod * 24 - hours) * 60)
    icon = "☀" if 6 <= hours < 20 else "☾"
    clock_txt = font_small.render(f"{icon} {hours:02d}:{minutes:02d}", True, TEXT_COLOR)
    screen.blit(clock_txt, (WIDTH - clock_txt.get_width() - 20, 88))

    zone_names = {"freezing": "Вьюга", "snow": "Снега", "cold": "Холод",
                  "mild": "Погода", "cave_warm": "Пещеры", "deep_ocean": "Глубины"}
    zone = zone_names.get(weather_zone(L["player"].rect.centery), "")
    stats = (f"Дист: {distance}м  Глуб: {depth}м  {zone}  "
             f"Враги: {L['kills']}  Ябл: {L['apples']}")
    s = font_small.render(stats, True, TEXT_COLOR)
    screen.blit(s, (WIDTH - s.get_width() - 20, 55))

    draw_hearts(screen, lives, DIFFICULTIES[difficulty_key]["lives"])
    draw_health_bar(screen, font_small, L["hp"], L["max_hp"])
    draw_temperature_bar(screen, font_small, L["body_temp"])
    draw_hotbar(screen, font_small, L["inventory"])

    # Кислородный индикатор при погружении
    p = L["player"]
    if p.head_in_water and not p.has_scuba:
        ox_x, ox_y = 14, 92
        ox_w, ox_h = 200, 14
        pygame.draw.rect(screen, (30, 30, 45), (ox_x - 2, ox_y - 2, ox_w + 4, ox_h + 4))
        pygame.draw.rect(screen, (90, 160, 220), (ox_x - 2, ox_y - 2, ox_w + 4, ox_h + 4), 1)
        pygame.draw.rect(screen, (20, 20, 30), (ox_x, ox_y, ox_w, ox_h))
        ratio = max(0.0, min(1.0, p.oxygen / 100.0))
        fill = int(ox_w * ratio)
        col = (100, 200, 255) if ratio > 0.4 else (255, 120, 120)
        if fill > 0:
            pygame.draw.rect(screen, col, (ox_x, ox_y, fill, ox_h))
        lbl = font_small.render(f"O2  {int(p.oxygen)}%", True, (255, 255, 255))
        screen.blit(lbl, (ox_x + 6, ox_y - 1))
    if getattr(p, "in_submarine", None) is not None:
        wat = font_big.render("~ БАТИСКАФ ~  (E — выйти)", True, (255, 220, 100))
        screen.blit(wat, (WIDTH // 2 - wat.get_width() // 2, HEIGHT - 130))
    elif p.in_boat is not None:
        wat = font_big.render("~ В ЛОДКЕ ~  (E — выйти)", True, (180, 220, 255))
        screen.blit(wat, (WIDTH // 2 - wat.get_width() // 2, HEIGHT - 130))
    elif p.in_water:
        wat = font_big.render("~ В ВОДЕ ~", True, (100, 200, 255))
        screen.blit(wat, (WIDTH // 2 - wat.get_width() // 2, HEIGHT - 110))

    if L["state"] == "game_over":
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 160))
        screen.blit(veil, (0, 0))
        txt = font_big.render("GAME OVER", True, (240, 90, 90))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 60))
        info = font_small.render(
            f"Дист: {distance}м  Глуб: {depth}м  Очки: {L['score']}",
            True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 - 10))
        info2 = font_small.render("R — заново   M — меню   Esc — выход",
                                  True, TEXT_COLOR)
        screen.blit(info2, (WIDTH // 2 - info2.get_width() // 2, HEIGHT // 2 + 30))

    elif L["state"] == "paused":
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 150))
        screen.blit(veil, (0, 0))
        txt = font_big.render("ПАУЗА", True, (255, 240, 120))
        screen.blit(txt, (WIDTH // 2 - txt.get_width() // 2, HEIGHT // 2 - 60))
        info = font_small.render("Esc — продолжить   M — в меню", True, TEXT_COLOR)
        screen.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 + 10))


def draw_card_toast(screen, font_big, font_small, L):
    if L["card_toast_timer"] <= 0 or not L["card_toast"]:
        return
    from cards import CARD_DEFS, RARITY, draw_card_icon
    cid = L["card_toast"]
    info = CARD_DEFS[cid]
    rar = RARITY[info["rarity"]]
    t = L["card_toast_timer"]
    slide = min(1.0, (180 - t) / 20.0)
    fade = min(1.0, t / 40.0)
    box_w, box_h = 300, 90
    x = WIDTH - box_w - 20
    y = int(20 + (1 - slide) * -120)
    box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box.fill((18, 14, 32, int(240 * fade)))
    pygame.draw.rect(box, (*rar["color"], int(255 * fade)), (0, 0, box_w, box_h), 2)
    draw_card_icon(box, info["icon"], pygame.Rect(8, 8, 74, 74))
    t1 = font_small.render("НОВАЯ КАРТОЧКА", True, (255, 240, 120, int(255 * fade)))
    t2 = font_big.render(info["name"], True, (*rar["color"], int(255 * fade)))
    t3 = font_small.render(rar["name"], True, (200, 200, 220, int(255 * fade)))
    box.blit(t1, (92, 10)); box.blit(t2, (92, 32)); box.blit(t3, (92, 62))
    screen.blit(box, (x, y))


def draw_achievement_toast(screen, font_big, font_small, L):
    if L["achievement_toast_timer"] <= 0 or not L.get("achievement_toast"):
        return
    from achievements import ACHIEVEMENTS
    ach = ACHIEVEMENTS[L["achievement_toast"]]
    t = L["achievement_toast_timer"]
    fade = min(1.0, t / 60.0)
    slide = min(1.0, (240 - t) / 20.0)
    box_w, box_h = 460, 90
    x = (WIDTH - box_w) // 2
    y = int(-100 + slide * 120)
    box = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    box.fill((20, 15, 40, int(240 * fade)))
    pygame.draw.rect(box, (255, 220, 80, int(255 * fade)), (0, 0, box_w, box_h), 3)
    pygame.draw.circle(box, (255, 220, 80, int(255 * fade)), (45, 45), 32)
    pygame.draw.circle(box, (255, 255, 255, int(255 * fade)), (45, 45), 32, 2)
    star = font_big.render("★", True, (60, 40, 20, int(255 * fade)))
    box.blit(star, (45 - star.get_width() // 2, 45 - star.get_height() // 2))
    t1 = font_small.render("ДОСТИЖЕНИЕ ПОЛУЧЕНО!", True, (255, 240, 150, int(255 * fade)))
    t2 = font_big.render(ach["name"], True, (255, 255, 255, int(255 * fade)))
    box.blit(t1, (90, 12)); box.blit(t2, (90, 38))
    if ach["reward"] > 0:
        t3 = font_small.render(f"+{ach['reward']} очков", True, (100, 240, 130, int(255 * fade)))
        box.blit(t3, (box_w - 120, 55))
    screen.blit(box, (x, y))


# ================= ИНСТРУМЕНТЫ =================
def use_tool_at(L, wx, wy, mx, my):
    # --- проверка сундуков (не требует инструмента) ---
    for c in L["world"].chests:
        if c.opened:
            continue
        if c.rect.inflate(30, 30).collidepoint(wx, wy):
            c.opened = True
            L["chests_opened"] = L.get("chests_opened", 0) + 1
            _give_chest_loot(L, c)
            return

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
                cid = roll_card("enemy", L["cards"])
                if cid:
                    L["cards"].add(cid)
                    L["card_toast"] = cid
                    L["card_toast_timer"] = 180
        sounds.play("stomp" if hit_any else "hit")

    elif sel_tool == AXE:
        pos = L["world"].chop_tree(wx, wy, radius_px=150)
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
        d = math.hypot(dx, dy) or 1
        speed = 13
        L["world"].arrows.append(Arrow(px, py, dx / d * speed, dy / d * speed))
        L["bow_cooldown"] = TOOLS[BOW]["cooldown"]
        sounds.play("jump")


# ================= СЕССИЯ =================
def new_session(difficulty):
    # Спавн — на лугу, чуть левее деревни
    spawn_tx = 87
    from world import surface_ty as _st
    spawn_ty = _st(spawn_tx)
    # ставим игрока НА поверхность (bottom = верхний тайл земли)
    player = Player(spawn_tx * TILE, spawn_ty * TILE - 32)
    camera = Camera(WIDTH)
    camera.offset_x = player.rect.centerx - WIDTH // 2
    camera.offset_y = player.rect.centery - HEIGHT // 2

    inv = Inventory()
    inv.add_tool(PICKAXE)
    inv.add_tool(AXE)
    inv.add_tool(SWORD)
    inv.add_tool(BOW)
    inv.add(TORCH, 30)

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
        "max_depth": 0,
        "state": "playing",
        "body_temp": 100.0,
        "freeze_tick": 0,
        "weather": Weather(),
        "inventory": inv,
        "mining": None,
        "particles": ParticleSystem(),
        "swing_timer": 0,
        "swing_angle": 0,
        "bow_cooldown": 0,
        "cards": set(),
        "card_toast": None,
        "card_toast_timer": 0,
        "blocks_dug": 0,
        "trees_chopped": 0,
        "arrows_hit": 0,
        "unlocked": set(),
        "achievement_toast": None,
        "achievement_toast_timer": 0,
        "light_mask": LightMask(),
        "fireflies": [],
        "boats": [],
        "chests_opened": 0,
        "seconds_underwater": 0.0,
        "scuba_used": 0,
        "_uw_seconds_accum": 0.0,
        "submarines": [],
    }


# ================= MAIN =================
def _give_chest_loot(L, chest):
    """Выдаёт лут из сундука игроку."""
    from blocks import COPPER, IRON, GOLD
    from cards import roll_card
    sounds.play("victory")
    # искры вокруг сундука
    cx = chest.rect.centerx
    cy = chest.rect.centery
    for _ in range(24):
        import random as _r
        L["particles"].spawn_sparks(cx, cy, count=1)
    total_score = 0
    for item, count in chest.loot:
        if item == "gold_coin":
            total_score += count * 3
            L["score"] += count * 3
        elif item == "iron_ore":
            L["inventory"].add(IRON, count)
            L["score"] += count
        elif item == "copper_ore":
            L["inventory"].add(COPPER, count)
            L["score"] += count
        elif item == "glowberry_seed":
            # просто +1 карточка из пула
            cid = roll_card("ore", L["cards"])
            if cid:
                L["cards"].add(cid)
                L["card_toast"] = cid
                L["card_toast_timer"] = 180
        elif item == "card":
            cid = roll_card("boss", L["cards"])  # любой из редких
            if cid:
                L["cards"].add(cid)
                L["card_toast"] = cid
                L["card_toast_timer"] = 180


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
    quests_ui = QuestUI(font_big, font_small)

    app_state = "menu"
    difficulty_key = DEFAULT_DIFFICULTY
    difficulty = DIFFICULTIES[difficulty_key]
    lives = difficulty["lives"]
    L = None

    running = True
    while running:
        clock.tick(FPS)

        # ============ EVENTS ============
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
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

            # поглощение событий UI
            if L and card_book.open:
                if card_book.handle_event(event, L["cards"]):
                    continue
            if L and achievements.open:
                if achievements.handle_event(event):
                    continue

            if event.type == pygame.MOUSEBUTTONDOWN:
                if L and L["state"] == "playing":
                    if craft_ui.open:
                        craft_ui.handle_mouse(pygame.mouse.get_pos(), True, L["inventory"])
                        continue
                    mx, my = pygame.mouse.get_pos()
                    wx = mx + L["camera"].ox
                    wy = my + L["camera"].oy
                    if event.button == 3:
                        bt = L["inventory"].selected_type()
                        if bt is not None:
                            tx = wx // TILE; ty = wy // TILE
                            if L["world"].place(tx, ty, bt):
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
            elif event.key == pygame.K_m:
                if L["state"] in ("paused", "game_over"):
                    app_state = "menu"
                elif L["state"] == "playing":
                    cfg = sound_settings.load()
                    cfg["enabled"] = not cfg["enabled"]
                    sound_settings.save(cfg)
                    sounds.reload_settings()
            elif event.key == pygame.K_r and L["state"] == "game_over":
                L = new_session(difficulty)
                lives = difficulty["lives"]
            elif event.key == pygame.K_c and L["state"] == "playing":
                craft_ui.toggle()
            elif event.key == pygame.K_b and L["state"] == "playing":
                card_book.toggle()
            elif event.key == pygame.K_j and L["state"] == "playing":
                achievements.toggle()
            elif event.key == pygame.K_g and L["state"] == "playing":
                L["player"].has_scuba = not L["player"].has_scuba
                if L["player"].has_scuba:
                    L["scuba_used"] = 1
                print(f"[SCUBA] {'включён' if L['player'].has_scuba else 'выключен'}")
            elif event.key == pygame.K_u and L["state"] == "playing":
                px = L["player"].rect.centerx + (60 if L["player"].facing_right else -60)
                py = L["player"].rect.bottom - 44
                L["submarines"].append(Submarine(px, py))
                print("[SUB] Батискаф поставлен")
            elif event.key == pygame.K_k and L["state"] == "playing":
                # поставить лодку перед игроком
                px = L["player"].rect.centerx + (60 if L["player"].facing_right else -60)
                py = L["player"].rect.bottom - 24
                L["boats"].append(Boat(px, py))
                print("[BOAT] поставлена")
            elif event.key in (pygame.K_e, pygame.K_f) and L["state"] == "playing":
                if getattr(L["player"], "in_submarine", None) is not None:
                    sub = L["player"].in_submarine
                    sub.eject(L["player"])
                    sounds.play("jump")
                elif L["player"].in_boat is not None:
                    # выход из лодки
                    boat = L["player"].in_boat
                    L["player"].in_boat = None
                    L["player"].rect.midbottom = (boat.rect.centerx, boat.rect.top - 4)
                    sounds.play("jump")
                else:
                    mx, my = pygame.mouse.get_pos()
                    wx = mx + L["camera"].ox
                    wy = my + L["camera"].oy
                    use_tool_at(L, wx, wy, mx, my)
            elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5,
                               pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0):
                n = event.key - pygame.K_1
                if n < 0: n = 9
                L["inventory"].select(n)

        # ============ МЕНЮ ============
        if app_state == "menu":
            menu.update()
            menu.draw(screen)
            pygame.display.flip()
            continue

        # ============ UPDATE ============
        if L["state"] == "playing":
            keys = pygame.key.get_pressed()
            L["player"].handle_input(keys)

            dt = clock.get_time() / 1000.0
            def nonlocal_do_death():
                """Обрабатывает смерть: отнимает сердце, респавн или GAME OVER."""
                nonlocal lives
                lives -= 1
                if lives <= 0:
                    L["state"] = "game_over"
                    sounds.play("game_over")
                    save_record(L["score"], 0, 0, L["kills"], L["apples"],
                                L["max_x"] // 10, difficulty_key)
                else:
                    # респавн на лугу
                    L["player"] = Player(87 * TILE, surface_ty(87) * TILE - 32)
                    L["camera"] = Camera(WIDTH)
                    L["camera"].offset_x = L["player"].rect.centerx - WIDTH // 2
                    L["camera"].offset_y = L["player"].rect.centery - HEIGHT // 2
                    L["hp"] = L["max_hp"]
                    L["body_temp"] = 100.0
                    L["player"].oxygen = 100
                    L["invuln"] = INVULN_TIME
                    sounds.play("hit")

            def _drown():
                if L["invuln"] == 0:
                    L["hp"] -= 10
                    L["invuln"] = 30
                    sounds.play("hit")
                    if L["hp"] <= 0:
                        L["hp"] = 0
                        nonlocal_do_death()
            L["player"].on_drown = _drown

            def _shark_bite():
                if L["invuln"] == 0:
                    L["hp"] -= 15
                    L["invuln"] = INVULN_TIME
                    sounds.play("hit")
                    if L["hp"] <= 0:
                        L["hp"] = 0
                        nonlocal_do_death()
            L["player"].on_shark_bite = _shark_bite

            # акулам — ссылка на игрока
            L["world"]._player_ref = L["player"]
            L["world"].tick_time(dt)
            L["world"].update(L["camera"])
            L["player"].update(L["world"])

            _, enemies, pixels, trees, medkits = L["world"].collect()
            for e in enemies:
                e.update(L["world"])
            L["camera"].update(L["player"].rect)

            # статистика
            L["max_x"] = max(L["max_x"], L["player"].rect.x)
            depth = max(0, (L["player"].rect.y - SURFACE_TY * TILE) // 10)
            L["max_depth"] = max(L["max_depth"], depth)

            if L["invuln"] > 0:
                L["invuln"] -= 1

            # смерть от бездны
            if L["player"].rect.top > DEATH_TY * TILE:
                lives -= 1
                if lives <= 0:
                    L["state"] = "game_over"
                    sounds.play("game_over")
                    save_record(L["score"], 0, 0, L["kills"], L["apples"],
                                L["max_x"] // 10, difficulty_key)
                else:
                    L["player"] = Player(87 * TILE, surface_ty(87) * TILE - 32)
                    L["camera"] = Camera(WIDTH)
                    L["hp"] = L["max_hp"]
                    sounds.play("hit")

            # температура
            ambient = get_ambient_temp(L["player"].rect.centery)
            if L["body_temp"] > ambient:
                delta = L["body_temp"] - ambient
                L["body_temp"] -= 0.15 + delta * 0.002
            else:
                L["body_temp"] += 0.25
            L["body_temp"] = max(0.0, min(100.0, L["body_temp"]))

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
                        L["player"] = Player(87 * TILE, surface_ty(87) * TILE - 32)
                        L["camera"] = Camera(WIDTH)
                        L["hp"] = L["max_hp"]
                        L["body_temp"] = 100.0

            # погода
            L["weather"].update(L["camera"].offset_y)

            # --- СВЕТЛЯЧКИ (ночью, на поверхности) ---
            tod = L["world"].time_of_day
            is_night = (tod < 0.20 or tod > 0.80)
            if is_night and random.random() < 0.15 and len(L["fireflies"]) < 40:
                px_f = L["camera"].offset_x + random.randint(0, WIDTH)
                py_f = SURFACE_TY * TILE - random.randint(40, 250)
                L["fireflies"].append({
                    "x": px_f, "y": py_f,
                    "vx": random.uniform(-0.6, 0.6),
                    "vy": random.uniform(-0.3, 0.3),
                    "phase": random.uniform(0, 6.28),
                    "life": random.randint(180, 400),
                })
            # обновление
            for ff in L["fireflies"][:]:
                ff["x"] += ff["vx"]
                ff["y"] += ff["vy"]
                ff["phase"] += 0.1
                ff["life"] -= 1
                # мягкий дрейф
                ff["vx"] += random.uniform(-0.05, 0.05)
                ff["vy"] += random.uniform(-0.05, 0.05)
                ff["vx"] = max(-1, min(1, ff["vx"]))
                ff["vy"] = max(-1, min(1, ff["vy"]))
                if ff["life"] <= 0:
                    L["fireflies"].remove(ff)

            # взмах + частицы
            if L["swing_timer"] > 0:
                L["swing_timer"] -= 1
                t = 1.0 - (L["swing_timer"] / 12.0)
                if t < 0.5:
                    L["swing_angle"] = -60 * (t / 0.5)
                else:
                    L["swing_angle"] = -60 * (1 - (t - 0.5) / 0.5)
            else:
                L["swing_angle"] = 0
            L["particles"].update()

            # батискафы
            for s in L["submarines"]:
                s.update(L["world"], keys if s.has_pilot else None)
                # посадка — E на близком расстоянии
                if (getattr(L["player"], "in_submarine", None) is None and
                        L["player"].in_water and
                        L["player"].rect.colliderect(s.rect.inflate(20, 20))):
                    if keys[pygame.K_e]:
                        s.set_pilot(L["player"])
                        L["player"].rect.center = s.rect.center
                        sounds.play("collect")

            # лодки — покачивание и посадка
            for b in L["boats"]:
                b.update(L["world"])
                # посадка: игрок касается лодки и не в лодке и не в воде
                if (L["player"].in_boat is None and
                        not L["player"].in_water and
                        L["player"].rect.colliderect(b.rect.inflate(0, 20))):
                    if pygame.key.get_pressed()[pygame.K_e]:
                        L["player"].in_boat = b
                        sounds.play("collect")

            # счётчик времени под водой (для квеста)
            if L["player"].head_in_water:
                L["_uw_seconds_accum"] += dt
                if L["_uw_seconds_accum"] >= 1.0:
                    L["seconds_underwater"] += 1
                    L["_uw_seconds_accum"] -= 1.0

            # пузырьки под водой
            if L["player"].head_in_water:
                if not hasattr(L, "_bubble_tick"):
                    L["_bubble_tick"] = 0
                L["_bubble_tick"] += 1
                if L["_bubble_tick"] % 18 == 0:
                    L["particles"].spawn_sparks(
                        L["player"].rect.centerx,
                        L["player"].rect.top,
                        count=2,
                    )

            # стрелы
            if L["bow_cooldown"] > 0:
                L["bow_cooldown"] -= 1
            for arr in L["world"].arrows[:]:
                hit = arr.update(L["world"], enemies)
                if hit is not None:
                    hit.alive = False
                    L["kills"] += 1
                    L["score"] += 5
                    L["arrows_hit"] += 1
                    L["particles"].spawn_blood(hit.rect.centerx, hit.rect.centery, count=14)
                    sounds.play("stomp")
                    cid = roll_card("enemy", L["cards"])
                    if cid:
                        L["cards"].add(cid)
                        L["card_toast"] = cid
                        L["card_toast_timer"] = 180
                if not arr.alive:
                    L["world"].arrows.remove(arr)

            # сбор пикселей
            for px in pixels:
                if px.alive and L["player"].rect.colliderect(px.rect):
                    px.alive = False
                    L["score"] += 1
                    sounds.play("collect")

            # сбор яблок
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

            # сбор аптечек
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
                        cid = roll_card("enemy", L["cards"])
                        if cid:
                            L["cards"].add(cid)
                            L["card_toast"] = cid
                            L["card_toast_timer"] = 180
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
                                L["player"] = Player(87 * TILE, surface_ty(87) * TILE - 32)
                                L["camera"] = Camera(WIDTH)
                                L["hp"] = L["max_hp"]

            # КОПАНИЕ (ЛКМ зажать)
            mouse_pressed = pygame.mouse.get_pressed()
            mx, my = pygame.mouse.get_pos()
            wx = mx + L["camera"].ox
            wy = my + L["camera"].oy
            tx = wx // TILE; ty = wy // TILE
            ptx = L["player"].rect.centerx // TILE
            pty = L["player"].rect.centery // TILE
            dist_t = max(abs(tx - ptx), abs(ty - pty))

            if mouse_pressed[0] and dist_t <= 5 and not craft_ui.open and not card_book.open and not achievements.open:
                bt = L["world"].get_block(tx, ty)
                if bt != AIR and bt in BLOCKS:
                    if L["swing_timer"] <= 0 and L["inventory"].selected_tool():
                        L["swing_timer"] = 8
                    if L["mining"] and L["mining"]["tx"] == tx and L["mining"]["ty"] == ty:
                        sel_tool = L["inventory"].selected_tool()
                        speed_mult = 1.0
                        if sel_tool and BLOCKS[bt].get("tool") == sel_tool:
                            speed_mult = TOOLS[sel_tool]["speed"]
                        elif not sel_tool:
                            speed_mult = 0.6
                        L["mining"]["progress"] += speed_mult / BLOCKS[bt]["hardness"]
                        if L["mining"]["progress"] >= 1.0:
                            dug = L["world"].dig(tx, ty)
                            if dug is not None:
                                L["inventory"].add(dug, 1)
                                L["score"] += 1
                                L["blocks_dug"] += 1
                                cxp = tx * TILE + TILE // 2
                                cyp = ty * TILE + TILE // 2
                                if dug in (3, 4, 5, 6):
                                    L["particles"].spawn_sparks(cxp, cyp, count=10)
                                    if dug == 4:      cid = roll_card("ore", L["cards"])
                                    elif dug in (5, 6): cid = roll_card("gold", L["cards"])
                                    else:             cid = None
                                else:
                                    L["particles"].spawn_dirt(cxp, cyp, count=10)
                                    cid = None
                                if cid:
                                    L["cards"].add(cid)
                                    L["card_toast"] = cid
                                    L["card_toast_timer"] = 180
                                sounds.play("collect")
                            L["mining"] = None
                    else:
                        L["mining"] = {"tx": tx, "ty": ty, "progress": 0.0}
            else:
                L["mining"] = None

            # тосты
            if L["card_toast_timer"] > 0: L["card_toast_timer"] -= 1
            if L["achievement_toast_timer"] > 0: L["achievement_toast_timer"] -= 1

            # --- проверка квестов ---
            if not hasattr(L, "_quest_counter"):
                L["_quest_counter"] = 0
            L["_quest_counter"] += 1
            if L["_quest_counter"] % 30 == 0:
                qstats = {
                    "blocks_dug": L.get("blocks_dug", 0),
                    "chests_opened": L.get("chests_opened", 0),
                    "kills": L.get("kills", 0),
                    "max_depth": L.get("max_depth", 0),
                    "cards_count": len(L.get("cards", set())),
                    "seconds_underwater": int(L.get("seconds_underwater", 0)),
                    "scuba_used": L.get("scuba_used", 0),
                }
                newly_q = quests_ui.check(qstats)
                if newly_q:
                    for q in newly_q:
                        L["score"] += q["reward"]
                    sounds.play("victory")

            # достижения (раз в 30 кадров)
            if not hasattr(L, "_ach_counter"): L["_ach_counter"] = 0
            L["_ach_counter"] += 1
            if L["_ach_counter"] % 30 == 0:
                stats_ach = {
                    "blocks_dug": L["blocks_dug"],
                    "trees_chopped": L["trees_chopped"],
                    "kills": L["kills"],
                    "arrows_hit": L["arrows_hit"],
                    "apples": L["apples"],
                    "max_x": L["max_x"] // 10,
                    "max_depth": L["max_depth"],
                    "cards_count": len(L["cards"]),
                    "boss_killed": 0,
                }
                new_ach = achievements.check_unlocks(stats_ach, L["unlocked"])
                if new_ach:
                    from achievements import ACHIEVEMENTS
                    for a in new_ach:
                        L["score"] += ACHIEVEMENTS[a]["reward"]
                    L["achievement_toast"] = new_ach[0]
                    L["achievement_toast_timer"] = 240
                    sounds.play("victory")

        card_book.update()
        achievements.update()
        craft_ui.update()
        quests_ui.update()

        # ============ DRAW ============
        draw_background(screen, L["camera"], L["world"].time_of_day)
        ox, oy = L["camera"].ox, L["camera"].oy

        L["world"].draw_tiles(screen, L["camera"])
        L["world"].draw_underwater(screen, L["camera"])
        # лодки — рисуем до игрока (игрок сверху)
        for b in L["boats"]:
            b.draw(screen, ox, oy)
        # батискафы
        for s in L["submarines"]:
            s.draw(screen, ox, oy)
        L["world"].draw_entities(screen, L["camera"])

        # подсветка блока под курсором
        if L["state"] == "playing":
            mx, my = pygame.mouse.get_pos()
            wx = mx + ox; wy = my + oy
            htx = (wx // TILE) * TILE
            hty = (wy // TILE) * TILE
            hr = pygame.Rect(htx - ox, hty - oy, TILE, TILE)
            if -TILE < hr.x < WIDTH and -TILE < hr.y < HEIGHT:
                pygame.draw.rect(screen, (255, 255, 255), hr, 2)

        # прогресс копания
        if L["mining"]:
            mrect = pygame.Rect(L["mining"]["tx"] * TILE, L["mining"]["ty"] * TILE,
                                TILE, TILE)
            draw_dig_progress(screen, mrect, L["mining"]["progress"], (ox, oy))

        # игрок
        blink = L["invuln"] > 0 and (L["invuln"] // 4) % 2 == 0
        if not blink:
            L["player"].draw(screen, ox, oy)

        # инструмент в руке
        tool_id = L["inventory"].selected_tool()
        if tool_id:
            angle = L["swing_angle"]
            sprite = (get_tool_sprite_rotated(tool_id, 22, int(angle)) if angle
                      else get_tool_sprite(tool_id, 22))
            if sprite:
                pr = L["player"].rect
                if L["player"].facing_right:
                    tx_ = pr.right - ox - 6
                    ty_ = pr.centery - oy - sprite.get_height() // 2
                else:
                    sprite = pygame.transform.flip(sprite, True, False)
                    tx_ = pr.left - ox - sprite.get_width() + 6
                    ty_ = pr.centery - oy - sprite.get_height() // 2
                screen.blit(sprite, (tx_, ty_))

        L["particles"].draw(screen, ox, oy)

        # --- ОСВЕЩЕНИЕ ---
        ambient = ambient_from_time(L["world"].time_of_day)
        # в пещерах темнее, но не критично
        depth = L["player"].rect.centery - SURFACE_TY * TILE
        if depth > 200:
            ambient = min(170, ambient + int(min(80, depth / 40)))
        light_sources = L["world"].get_light_sources(L["camera"])
        # сам игрок немного светится
        light_sources.append((L["player"].rect.centerx, L["player"].rect.centery, 240))
        # светлячки — маленькие источники света
        for ff in L["fireflies"]:
            light_sources.append((ff["x"], ff["y"], 90))
        # прожектор батискафа
        for s in L["submarines"]:
            lx, ly, lr = s.get_light()
            light_sources.append((lx, ly, lr))
        L["light_mask"].render(screen, L["camera"], light_sources, ambient)

        # светлячки — яркие точки
        for ff in L["fireflies"]:
            fx = int(ff["x"] - ox)
            fy = int(ff["y"] - oy)
            if -5 < fx < WIDTH + 5 and -5 < fy < HEIGHT + 5:
                import math as _m
                glow_a = 100 + int(80 * _m.sin(ff["phase"]))
                glow = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(glow, (200, 255, 150, glow_a // 3), (10, 10), 10)
                pygame.draw.circle(glow, (255, 255, 180, glow_a), (10, 10), 3)
                screen.blit(glow, (fx - 10, fy - 10))

        L["weather"].draw(screen, L["camera"].offset_y)

        draw_hud(screen, font_big, font_small, L, lives, difficulty_key)

        # Sidebar квестов
        qstats = {
            "blocks_dug": L.get("blocks_dug", 0),
            "chests_opened": L.get("chests_opened", 0),
            "kills": L.get("kills", 0),
            "max_depth": L.get("max_depth", 0),
            "cards_count": len(L.get("cards", set())),
            "seconds_underwater": int(L.get("seconds_underwater", 0)),
            "scuba_used": L.get("scuba_used", 0),
        }
        quests_ui.draw_sidebar(screen, qstats, difficulty_key)

        craft_ui.draw(screen, L["inventory"])
        draw_card_toast(screen, font_big, font_small, L)
        card_book.draw(screen, L["cards"])
        stats_ach = {
            "blocks_dug": L["blocks_dug"], "trees_chopped": L["trees_chopped"],
            "kills": L["kills"], "arrows_hit": L["arrows_hit"],
            "apples": L["apples"], "max_x": L["max_x"] // 10,
            "max_depth": L["max_depth"], "cards_count": len(L["cards"]),
            "boss_killed": 0,
        }
        achievements.draw(screen, stats_ach, L["unlocked"])
        draw_achievement_toast(screen, font_big, font_small, L)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
