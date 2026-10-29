import math, random
import pygame

class Particle:
    __slots__ = ('x','y','vx','vy','life','maxlife','color','size')
    def __init__(self, x, y, color, speed=4.0, life=30):
        a = random.uniform(0, math.tau)
        r = random.uniform(0.3, 1.0) * speed
        self.x, self.y = x, y
        self.vx = math.cos(a) * r
        self.vy = math.sin(a) * r - 1.5
        self.life = self.maxlife = life
        self.color = color
        self.size = random.randint(2, 4)

    def update(self, dt):
        f = dt / 16.67
        self.x += self.vx * f
        self.y += self.vy * f
        self.vy += 0.18 * f
        self.vx *= 0.99
        self.life -= f

    def draw(self, surf):
        if self.life <= 0:
            return
        a = max(0.0, self.life / self.maxlife)
        size = max(1, int(self.size * a))
        # simple glow
        try:
            pygame.draw.circle(surf, (*self.color[:3], int(255 * a)),
                               (int(self.x), int(self.y)), size + 2)
        except TypeError:
            pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), size)

class Effects:
    def __init__(self):
        self.particles = []
        self.enable_shake = True
        self.shake = 0.0

    def burst(self, x, y, color, count=14):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))

    def burst_row(self, y_px, board_x, cell, cols, colors):
        for c in range(cols):
            self.burst(board_x + c * cell + cell / 2, y_px + cell / 2,
                       random.choice(colors), count=5)

    def kick(self, power=6.0):
        if self.enable_shake:
            self.shake = max(self.shake, power)

    def update(self, dt):
        f = dt / 16.67
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        self.shake = max(0.0, self.shake - 0.6 * f)

    def draw(self, surf, layer=None):
        if layer is None:
            for p in self.particles:
                p.draw(surf)

    def offset(self):
        if self.shake > 0.1:
            return (random.uniform(-self.shake, self.shake),
                    random.uniform(-self.shake, self.shake))
        return (0, 0)


def apply_bloom(surface, intensity=1.0):
    """Нативный, но аккуратный эффект свечения."""
    try:
        # Уменьшаем радиус размытия с 6 до 2 (чтобы текст не превращался в кашу)
        blurred = pygame.transform.gaussian_blur(surface, 2)
        
        # Делаем размытие полупрозрачным, чтобы оно не "выжигало" цвета
        blurred.set_alpha(100) 
        
        # Накладываем с аддитивным смешиванием
        surface.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    except AttributeError:
        pass
