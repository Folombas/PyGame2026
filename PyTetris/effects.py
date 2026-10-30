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
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.life > 0]
        for w in self.waves:
            w.update(dt)
        self.waves = [w for w in self.waves if w.life > 0]
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
        self.shake = 0.0
        self.texts = []
        self.waves = []
        self.enable_shake = True

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
        for t in self.texts:
            t.update(dt)
        self.texts = [t for t in self.texts if t.life > 0]
        for w in self.waves:
            w.update(dt)
        self.waves = [w for w in self.waves if w.life > 0]
        f = dt / 16.67
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.life > 0]
        self.shake = max(0.0, self.shake - 0.6 * f)

    def draw(self, surf, layer=None, font=None):
        if layer is None:
            for p in self.particles:
                p.draw(surf)
            for w in self.waves:
                w.draw(surf)
            if font:
                for t in self.texts:
                    t.draw(surf, font)

    def offset(self):
        if self.shake > 0.1:
            return (random.uniform(-self.shake, self.shake),
                    random.uniform(-self.shake, self.shake))
        return (0, 0)

class FloatingText:
    def __init__(self, x, y, text, color, life=60):
        self.x, self.y = x, y
        self.text = text
        self.color = color
        self.life = self.max_life = life

    def update(self, dt):
        self.y -= (dt / 16.67) * 1.5
        self.life -= dt / 16.67

    def draw(self, surf, font):
        if self.life > 0:
            a = max(0, min(255, int(255 * (self.life / self.max_life))))
            img = font.render(self.text, True, self.color)
            img.set_alpha(a)
            surf.blit(img, (self.x - img.get_width()//2, self.y))

class Shockwave:
    def __init__(self, x, y, color, max_radius=100, life=20):
        self.x, self.y = x, y
        self.color = color
        self.radius = 0
        self.max_radius = max_radius
        self.life = self.max_life = life

    def update(self, dt):
        self.radius += (self.max_radius / self.max_life) * (dt / 16.67)
        self.life -= dt / 16.67

    def draw(self, surf):
        if self.life > 0:
            a = max(0, int(255 * (self.life / self.max_life)))
            w = max(1, int(5 * (self.life / self.max_life)))
            try:
                pygame.draw.circle(surf, (*self.color[:3], a), (int(self.x), int(self.y)), int(self.radius), w)
            except TypeError:
                pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), int(self.radius), w)


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
