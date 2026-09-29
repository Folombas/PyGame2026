"""Константы и настройки игры."""

# Экран
WIDTH, HEIGHT = 800, 600
FPS = 60
TITLE = "PyPixel"

# Цвета
BG_COLOR = (24, 20, 37)
PLAYER_COLOR = (120, 200, 120)
GROUND_COLOR = (60, 50, 80)

# Физика
GRAVITY = 0.7
PLAYER_SPEED = 5
JUMP_POWER = -15
GROUND_Y = HEIGHT - 60  # высота "земли" от верха экрана

# Платформы
PLATFORM_COLOR = (90, 75, 120)

# Мир
WORLD_WIDTH = 2400          # уровень в 3 экрана шириной
SKY_COLOR = (18, 16, 30)
STAR_COLOR = (200, 200, 230)

# Враги и очки
ENEMY_COLOR = (230, 90, 90)
PIXEL_COLOR = (255, 220, 90)
TEXT_COLOR = (230, 230, 240)
ENEMY_SPEED = 2

# Жизни и флаг
LIVES = 5
HEART_COLOR = (240, 70, 90)
HEART_EMPTY_COLOR = (70, 40, 50)
FLAG_COLOR = (250, 210, 80)
FLAG_POLE_COLOR = (220, 220, 230)
VICTORY_TEXT_COLOR = (255, 240, 120)
INVULN_TIME = 90          # кадров неуязвимости (~1.5 сек)

# Здоровье
MAX_HP = 100
HIT_DAMAGE = 25
HP_BAR_BG = (35, 25, 40)
HP_BAR_BORDER = (110, 90, 140)
HP_COLOR_HIGH = (100, 220, 120)
HP_COLOR_MID = (240, 200, 80)
HP_COLOR_LOW = (240, 80, 90)


# Сложности
DIFFICULTIES = {
    "easy":   {"lives": 5, "max_hp": 100, "hit_damage": 15, "enemy_speed": 1.5, "label": "Лёгкий"},
    "normal": {"lives": 5, "max_hp": 100, "hit_damage": 25, "enemy_speed": 2.0, "label": "Обычный"},
    "hard":   {"lives": 3, "max_hp": 75,  "hit_damage": 40, "enemy_speed": 3.0, "label": "Сложный"},
}
DEFAULT_DIFFICULTY = "normal"
