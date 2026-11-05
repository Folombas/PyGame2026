CELL = 30
COLS, ROWS = 10, 20
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
SIDEBAR = 320
WIDTH = BOARD_W + SIDEBAR + 60
HEIGHT = 760
FPS = 60

BG        = (12, 10, 24)
GRID      = (26, 22, 44)
TEXT      = (232, 232, 255)
MUTED     = (140, 140, 180)
ACCENT    = (0, 255, 200)
ACCENT2   = (255, 60, 180)
DANGER    = (255, 80, 80)
GOLD      = (255, 215, 100)

COLORS = {
    'I': (0, 240, 240),
    'O': (240, 240, 0),
    'T': (170, 0, 240),
    'S': (0, 240, 0),
    'Z': (240, 40, 60),
    'J': (60, 100, 240),
    'L': (240, 160, 0),
}

SHAPES = {
    'I': [[1,1,1,1]],
    'O': [[1,1],[1,1]],
    'T': [[0,1,0],[1,1,1]],
    'S': [[0,1,1],[1,1,0]],
    'Z': [[1,1,0],[0,1,1]],
    'J': [[1,0,0],[1,1,1]],
    'L': [[0,0,1],[1,1,1]],
}

SCORES_FILE = 'data/scores.json'
META_FILE   = 'data/meta.json'


# --- Assets ---
ASSETS_DIR = "assets"
BLOCK_SPRITES_DIR = "assets/blocks"


# Sprint Mode
SPRINT_GOAL = 40

# --- Material Design Theme (Dark) ---
MD_PRIMARY = (187, 134, 252)      # #BB86FC
MD_PRIMARY_VARIANT = (55, 0, 179) # #3700B3
MD_SECONDARY = (3, 218, 198)      # #03DAC6
MD_BACKGROUND = (18, 18, 18)      # #121212
MD_SURFACE = (30, 30, 30)         # #1E1E1E
MD_ERROR = (176, 0, 32)           # #B00020
MD_ON_PRIMARY = (0, 0, 0)         # #000000
MD_ON_SECONDARY = (0, 0, 0)       # #000000
MD_ON_BACKGROUND = (255, 255, 255) # #FFFFFF
MD_ON_SURFACE = (255, 255, 255)   # #FFFFFF
MD_MUTED = (180, 180, 180)

# --- Fonts ---
import os
FONT_REGULAR = os.path.join("assets", "fonts", "Roboto-Regular.ttf")
FONT_BOLD = os.path.join("assets", "fonts", "Roboto-Bold.ttf")
