"""Bunny Protocol — константы."""

WIDTH, HEIGHT = 1024, 640
FPS = 60

TILE = 32
MAP_W, MAP_H = 40, 30

# Цвета — dark cyberpunk (Tokyo Night)
BG        = (13, 15, 24)
FLOOR     = (26, 30, 46)
FLOOR_ALT = (22, 26, 40)
WALL      = (40, 46, 68)
WALL_TOP  = (58, 66, 96)
SERVER    = (35, 42, 60)
SERVER_ON = (60, 200, 120)  # LED-полоска на сервере

PLAYER    = (220, 230, 245)
PLAYER_ACCENT = (120, 200, 255)

ENEMY       = (240, 100, 120)
ENEMY_FOV   = (255, 80, 100, 40)   # конус зрения
ENEMY_ALERT = (255, 40, 60)

KEY_COLOR  = (255, 220, 100)
EXIT_COLOR = (100, 240, 150)
PANEL_COLOR = (180, 130, 255)

TEXT      = (200, 210, 240)
TEXT_DIM  = (100, 110, 140)
HUD_BG    = (10, 12, 20)
ALERT     = (255, 60, 80)
OK        = (100, 240, 150)

# Игрок
PLAYER_SPEED = 240        # px/sec
PLAYER_RADIUS = 12

# Враги
ENEMY_PATROL_SPEED = 80
ENEMY_ALERT_SPEED = 220
ENEMY_VIEW_DIST = 220
ENEMY_VIEW_ANGLE = 60      # градусов
ENEMY_DETECT_RATE = 1.8    # подозрение/сек
ENEMY_FORGET_RATE = 0.6

# Прогрессия
KEYS_REQUIRED = 3
