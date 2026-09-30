"""Босс — летающая голова, стреляет снарядами, умирает от 5 прыжков сверху."""
import math
import pygame


# ---------- Спрайт босса (14x14, scale=4 → 56x56) ----------
BOSS_SPRITE = [
    "KK..........KK",
    "KKK........KKK",
    ".KKK......KKK.",
    "..KKRRRRRRKK..",
    ".KRRRRRRRRRRK.",
    "KRRWWRRRRWWRRK",
    "KRRWWRRRRWWRRK",
    "KRRRRRRRRRRRRK",
    "KRRRRWWWWRRRRK",
    "KRRRWKWKKWRRRK",
    "KRRRRWWWWRRRRK",
    ".KRRRRRRRRRRK.",
    "..KKRRRRRRKK..",
    "....KKKKKK....",
]

BOSS_PALETTE = {
    "R": (200, 50, 50),    # красное тело
    "K": (30, 20, 30),     # чёрный контур / рога
    "W": (255, 255, 255),  # глаза и зубы
}

BOSS_SCALE = 4
BOSS_SIZE = 14 * BOSS_SCALE   # 56


# ---------- Спрайт снаряда (6x6, scale=4 → 24x24) ----------
PROJECTILE_SPRITE = [
    "..YY..",
    ".YOOY.",
    "YOWWOY",
    "YORROY",
    ".YOOY.",
    "..YY..",
]

PROJECTILE_PALETTE = {
    "Y": (255, 230, 90),
    "O": (240, 130, 40),
    "R": (220, 50, 40),
    "W": (255, 255, 240),
}

PROJECTILE_SCALE = 4
PROJECTILE_SIZE = 6 * PROJECTILE_SCALE  # 24


def _build_sprite(pattern, palette, scale):
    h = len(pattern)
    w = len(pattern[0])
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    for y, row in enumerate(pattern):
        for x, ch in enumerate(row):
            color = palette.get(ch)
            if color is not None:
                surf.set_at((x, y), color)
    return pygame.transform.scale(surf, (w * scale, h * scale))


class Projectile:
    """Огненный снаряд босса. Летит в направлении игрока."""

    _sprite_cache = None

    @classmethod
    def _get_sprite(cls):
        if cls._sprite_cache is None:
            cls._sprite_cache = _build_sprite(
                PROJECTILE_SPRITE, PROJECTILE_PALETTE, PROJECTILE_SCALE
            )
        return cls._sprite_cache

    def __init__(self, x, y, vx, vy):
        self.rect = pygame.Rect(x, y, PROJECTILE_SIZE, PROJECTILE_SIZE)
        self.vx = vx
        self.vy = vy
        self.alive = True
        self.lifetime = 300    # ~5 секунд при 60 FPS

    def update(self, platforms):
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False
            return
        # разбивается о платформы
        for p in platforms:
            if self.rect.colliderect(p.rect):
                self.alive = False
                return

    def draw(self, surface, offset_x=0):
        if not self.alive:
            return
        sprite = self._get_sprite()
        r = sprite.get_rect(center=self.rect.center)
        r.x -= offset_x
        surface.blit(sprite, r)


class Boss:
    """Летающая голова. 5 HP. Стомп снимает 1 HP. Неуязвим 30 кадров после урона."""

    MAX_HP = 5
    SHOOT_INTERVAL = 110      # кадров между выстрелами (~1.8 сек)
    INVULN_FRAMES = 30

    _sprite_cache = None

    @classmethod
    def _get_sprite(cls):
        if cls._sprite_cache is None:
            cls._sprite_cache = _build_sprite(BOSS_SPRITE, BOSS_PALETTE, BOSS_SCALE)
        return cls._sprite_cache

    def __init__(self, x, y, patrol_range=400):
        self.spawn_x = x
        self.spawn_y = y
        self.rect = pygame.Rect(x, y, BOSS_SIZE, BOSS_SIZE)
        self.rect.center = (x, y)
        self.hp = self.MAX_HP
        self.max_hp = self.MAX_HP
        self.alive = True
        self.vel_x = 2.5
        self.min_x = x - patrol_range // 2
        self.max_x = x + patrol_range // 2
        self.bob_timer = 0.0
        self.shoot_timer = 60       # первый выстрел через 1 сек
        self.invuln = 0
        self.projectiles = []
        self.death_timer = 0        # для анимации после смерти

    def update(self, player, platforms):
        if not self.alive:
            return

        # горизонтальное патрулирование
        self.rect.x += int(self.vel_x)
        if self.rect.centerx < self.min_x:
            self.rect.centerx = self.min_x
            self.vel_x = abs(self.vel_x)
        elif self.rect.centerx > self.max_x:
            self.rect.centerx = self.max_x
            self.vel_x = -abs(self.vel_x)

        # вертикальное покачивание
        self.bob_timer += 0.05
        bob = int(math.sin(self.bob_timer) * 8)
        self.rect.y = self.spawn_y - BOSS_SIZE // 2 + bob

        # стрельба
        if self.shoot_timer > 0:
            self.shoot_timer -= 1
        else:
            self._shoot(player)
            self.shoot_timer = self.SHOOT_INTERVAL

        if self.invuln > 0:
            self.invuln -= 1

        # снаряды
        for pr in self.projectiles:
            pr.update(platforms)
        self.projectiles = [pr for pr in self.projectiles if pr.alive]

    def _shoot(self, player):
        bx, by = self.rect.center
        px, py = player.rect.center
        dx, dy = px - bx, py - by
        dist = math.hypot(dx, dy) or 1
        speed = 5.0
        self.projectiles.append(Projectile(
            bx - PROJECTILE_SIZE // 2,
            by - PROJECTILE_SIZE // 2,
            dx / dist * speed,
            dy / dist * speed,
        ))

    def take_damage(self):
        """Возвращает True, если босс убит. False — если проглотил (invuln)."""
        if self.invuln > 0:
            return False
        self.hp -= 1
        self.invuln = self.INVULN_FRAMES
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False

    def draw(self, surface, offset_x=0):
        if not self.alive:
            return
        # мерцание при неуязвимости
        if self.invuln > 0 and (self.invuln // 3) % 2 == 0:
            return
        sprite = self._get_sprite()
        r = sprite.get_rect(center=self.rect.center)
        r.x -= offset_x
        surface.blit(sprite, r)
        # снаряды
        for pr in self.projectiles:
            pr.draw(surface, offset_x)
