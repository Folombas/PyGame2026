"""Данные уровней."""
from settings import HEIGHT, WORLD_WIDTH
from platform import Platform
from enemy import Enemy
from collectible import Pixel
from tree import AppleTree
from medkit import Medkit


def level_1():
    platforms = [
        Platform(0, HEIGHT - 40, WORLD_WIDTH, 40),
        Platform(120, HEIGHT - 160, 160, 20),
        Platform(360, HEIGHT - 240, 160, 20),
        Platform(600, HEIGHT - 160, 160, 20),
        Platform(820, HEIGHT - 300, 100, 20),
        Platform(980, HEIGHT - 380, 100, 20),
        Platform(1140, HEIGHT - 300, 100, 20),
        Platform(1360, HEIGHT - 160, 160, 20),
        Platform(1600, HEIGHT - 240, 160, 20),
        Platform(1840, HEIGHT - 320, 200, 20),
        Platform(2150, HEIGHT - 400, 200, 20),
    ]
    enemies = [
        Enemy(380, HEIGHT - 240 - 28),
        Enemy(640, HEIGHT - 160 - 28),
        Enemy(1000, HEIGHT - 380 - 28),
        Enemy(1400, HEIGHT - 160 - 28),
        Enemy(1640, HEIGHT - 240 - 28),
        Enemy(1900, HEIGHT - 320 - 28),
    ]
    pixels = [
        Pixel(150, HEIGHT - 200), Pixel(200, HEIGHT - 200),
        Pixel(400, HEIGHT - 280), Pixel(460, HEIGHT - 280),
        Pixel(640, HEIGHT - 200), Pixel(700, HEIGHT - 200),
        Pixel(840, HEIGHT - 340), Pixel(1000, HEIGHT - 420),
        Pixel(1160, HEIGHT - 340),
        Pixel(1400, HEIGHT - 200), Pixel(1450, HEIGHT - 200),
        Pixel(1640, HEIGHT - 280), Pixel(1700, HEIGHT - 280),
        Pixel(1880, HEIGHT - 360), Pixel(1940, HEIGHT - 360),
        Pixel(2200, HEIGHT - 440), Pixel(2280, HEIGHT - 440),
    ]
    trees = [
        AppleTree(400, HEIGHT - 40),
        AppleTree(1000, HEIGHT - 40),
        AppleTree(1700, HEIGHT - 40),
        AppleTree(2200, HEIGHT - 40),
    ]
    medkits = [
        Medkit(700, HEIGHT - 220),
        Medkit(1500, HEIGHT - 100),
        Medkit(2050, HEIGHT - 380),
    ]
    flag_pos = (2330, HEIGHT - 400)
    boss_pos = None
    return platforms, enemies, pixels, trees, medkits, flag_pos, boss_pos


def level_2():
    platforms = [
        Platform(0, HEIGHT - 40, WORLD_WIDTH, 40),
        Platform(200, HEIGHT - 150, 120, 20),
        Platform(400, HEIGHT - 250, 120, 20),
        Platform(600, HEIGHT - 350, 120, 20),
        Platform(800, HEIGHT - 250, 120, 20),
        Platform(1000, HEIGHT - 150, 120, 20),
        Platform(1250, HEIGHT - 200, 200, 20),
        Platform(1550, HEIGHT - 300, 200, 20),
        Platform(1850, HEIGHT - 200, 200, 20),
        Platform(2150, HEIGHT - 300, 200, 20),
    ]
    enemies = [
        Enemy(220, HEIGHT - 150 - 28),
        Enemy(620, HEIGHT - 350 - 28),
        Enemy(1020, HEIGHT - 150 - 28),
        Enemy(1580, HEIGHT - 300 - 28),
        Enemy(1880, HEIGHT - 200 - 28),
    ]
    pixels = [
        Pixel(220, HEIGHT - 190), Pixel(240, HEIGHT - 190),
        Pixel(420, HEIGHT - 290), Pixel(440, HEIGHT - 290),
        Pixel(620, HEIGHT - 390), Pixel(640, HEIGHT - 390),
        Pixel(820, HEIGHT - 290), Pixel(840, HEIGHT - 290),
        Pixel(1020, HEIGHT - 190), Pixel(1040, HEIGHT - 190),
        Pixel(1280, HEIGHT - 240), Pixel(1300, HEIGHT - 240),
        Pixel(1580, HEIGHT - 340), Pixel(1600, HEIGHT - 340),
        Pixel(1880, HEIGHT - 240), Pixel(1900, HEIGHT - 240),
        Pixel(2200, HEIGHT - 340), Pixel(2260, HEIGHT - 340),
    ]
    trees = [
        AppleTree(100, HEIGHT - 40),
        AppleTree(1300, HEIGHT - 40),
        AppleTree(1800, HEIGHT - 40),
        AppleTree(2150, HEIGHT - 40),
    ]
    medkits = [
        Medkit(320, HEIGHT - 220),
        Medkit(700, HEIGHT - 420),
        Medkit(1700, HEIGHT - 380),
    ]
    flag_pos = (2330, HEIGHT - 300)
    # Босс летает над ареной в середине уровня
    boss_pos = (1200, HEIGHT - 380)
    return platforms, enemies, pixels, trees, medkits, flag_pos, boss_pos


LEVELS = [level_1, level_2]
