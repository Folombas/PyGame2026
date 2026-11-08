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


def font(size: int, bold: bool = False) -> pygame.font.Font:
    for name in ("Roboto", "DejaVu Sans", "Arial"):
        try:
            return pygame.font.SysFont(name, size, bold=bold)
        except Exception:
            pass
    return pygame.font.Font(None, size)
