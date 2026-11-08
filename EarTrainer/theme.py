"""Material Design палитра и шрифты."""
import pygame

MD_PRIMARY = (187, 134, 252)
MD_PRIMARY_DIM = (120, 80, 180)
MD_SECONDARY = (3, 218, 198)
MD_BG = (18, 18, 24)
MD_SURFACE = (30, 30, 40)
MD_SURFACE_HI = (44, 44, 58)
MD_ON_BG = (232, 232, 245)
MD_ON_SURFACE = (220, 220, 235)
MD_MUTED = (140, 140, 170)
MD_ERROR = (220, 60, 60)
MD_SUCCESS = (80, 220, 120)
MD_GOLD = (255, 215, 100)

WIDTH = 900
HEIGHT = 720
FPS = 60


# Проверяем доступные системные шрифты один раз
_AVAILABLE = set(pygame.font.get_fonts())  # возвращает lowercase без пробелов

def _pick_font_name():
    """Возвращает имя первого доступного шрифта с поддержкой кириллицы."""
    candidates = ("notosans", "dejavusans", "liberationsans", "arial", "freesans")
    for name in candidates:
        if name in _AVAILABLE:
            return name
    return None

_FONT_NAME = _pick_font_name()

def font(size: int, bold: bool = False) -> pygame.font.Font:
    if _FONT_NAME:
        try:
            return pygame.font.SysFont(_FONT_NAME, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)

# --- Autofix: недостающие цвета ---
MD_ON_PRIMARY = (0, 0, 0)
