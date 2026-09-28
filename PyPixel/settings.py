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
