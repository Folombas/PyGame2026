"""Уровни. Мир расширен: горы сверху, пещеры снизу."""
from settings import WORLD_WIDTH, SURFACE_Y
from platform import Platform
from enemy import Enemy
from collectible import Pixel
from tree import AppleTree
from medkit import Medkit


def level_1():
    """
    Биомы по Y:
      0-250   снежные вершины
      250-500 горы
      500-800 холмы
      800-1200 лес / луг  (SURFACE_Y = 1200)
      1200-1600 пещеры
      1600+ глубокая тьма
    """
    S = SURFACE_Y
    p = []
    # --- ЛУГ ---
    p.append(Platform(0, S, WORLD_WIDTH, 40))
    # --- ХОЛМЫ ---
    p.append(Platform(150, S - 150, 200, 20))
    p.append(Platform(450, S - 220, 200, 20))
    p.append(Platform(750, S - 150, 200, 20))
    # --- ГОРЫ ---
    p.append(Platform(1050, S - 400, 150, 20))
    p.append(Platform(1300, S - 520, 150, 20))
    p.append(Platform(1550, S - 420, 150, 20))
    # --- СНЕЖНЫЕ ВЕРШИНЫ ---
    p.append(Platform(1800, S - 700, 120, 20))
    p.append(Platform(2000, S - 850, 120, 20))
    p.append(Platform(2180, S - 980, 220, 20))
    # --- ПЕЩЕРЫ ---
    p.append(Platform(200, S + 180, 200, 20))
    p.append(Platform(500, S + 320, 200, 20))
    p.append(Platform(800, S + 180, 200, 20))
    p.append(Platform(1100, S + 380, 200, 20))
    # --- ГЛУБОКИЕ ПЕЩЕРЫ ---
    p.append(Platform(1400, S + 550, 200, 20))
    p.append(Platform(1700, S + 650, 200, 20))
    p.append(Platform(2000, S + 750, 300, 20))

    enemies = [
        Enemy(500, S - 248),
        Enemy(800, S - 178),
        Enemy(1350, S - 548),
        Enemy(1600, S - 448),
        Enemy(550, S + 292),
        Enemy(1150, S + 352),
        Enemy(1750, S + 622),
    ]

    pixels = [
        Pixel(200, S - 190), Pixel(250, S - 190),
        Pixel(500, S - 260), Pixel(550, S - 260),
        Pixel(800, S - 190), Pixel(850, S - 190),
        Pixel(1100, S - 440), Pixel(1350, S - 560),
        Pixel(1600, S - 460),
        Pixel(1850, S - 740), Pixel(2050, S - 890),
        Pixel(2250, S - 1020),
        Pixel(250, S + 220), Pixel(550, S + 360),
        Pixel(850, S + 220), Pixel(1150, S + 420),
        Pixel(1450, S + 590), Pixel(2050, S + 790),
    ]

    trees = [
        AppleTree(350, S),
        AppleTree(900, S),
        AppleTree(1450, S),
    ]
    medkits = [
        Medkit(650, S - 300),
        Medkit(1200, S + 300),
        Medkit(2100, S - 850),
    ]

    flag_pos = (2300, S - 980)
    boss_pos = None
    return p, enemies, pixels, trees, medkits, flag_pos, boss_pos


def level_2():
    S = SURFACE_Y
    p = []
    # ЛУГ
    p.append(Platform(0, S, WORLD_WIDTH, 40))
    # ХОЛМЫ
    p.append(Platform(200, S - 150, 120, 20))
    p.append(Platform(400, S - 250, 120, 20))
    p.append(Platform(600, S - 350, 120, 20))
    p.append(Platform(800, S - 250, 120, 20))
    p.append(Platform(1000, S - 150, 120, 20))
    # ГОРЫ
    p.append(Platform(1250, S - 350, 200, 20))
    p.append(Platform(1550, S - 500, 200, 20))
    p.append(Platform(1850, S - 350, 200, 20))
    # ПЕЩЕРЫ
    p.append(Platform(300, S + 200, 200, 20))
    p.append(Platform(600, S + 350, 200, 20))
    p.append(Platform(900, S + 500, 200, 20))
    p.append(Platform(1200, S + 650, 250, 20))

    enemies = [
        Enemy(220, S - 178),
        Enemy(620, S - 378),
        Enemy(1020, S - 178),
        Enemy(1580, S - 528),
        Enemy(650, S + 322),
        Enemy(950, S + 472),
    ]
    pixels = [
        Pixel(230, S - 190), Pixel(250, S - 190),
        Pixel(430, S - 290), Pixel(450, S - 290),
        Pixel(630, S - 390), Pixel(650, S - 390),
        Pixel(830, S - 290), Pixel(850, S - 290),
        Pixel(1030, S - 190), Pixel(1050, S - 190),
        Pixel(1280, S - 390), Pixel(1580, S - 540),
        Pixel(1880, S - 390), Pixel(1920, S - 390),
        Pixel(350, S + 240), Pixel(650, S + 390),
        Pixel(950, S + 540), Pixel(1250, S + 690),
    ]
    trees = [
        AppleTree(100, S),
        AppleTree(1300, S),
        AppleTree(1800, S),
    ]
    medkits = [
        Medkit(300, S - 220),
        Medkit(700, S + 420),
        Medkit(1700, S - 400),
    ]
    flag_pos = (2300, S - 400)
    boss_pos = (1200, S - 400)
    return p, enemies, pixels, trees, medkits, flag_pos, boss_pos


LEVELS = [level_1, level_2]
