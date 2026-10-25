"""Bunny Protocol — top-down stealth-action."""
import sys
import math
import pygame
from settings import *
from world import World
from player import Player
from enemies import spawn_enemies
from pickups import spawn_keys, spawn_panels, Exit
from render import Camera, draw_world
from ui import HUD


class Game:
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init()
        except Exception:
            pass
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Bunny Protocol")
        self.clock = pygame.time.Clock()

        self.font_big = pygame.font.Font(None, 96)
        self.font = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 20)

        self.state = "title"
        self.running = True
        self.timer = 0.0
        self.best_time = 0
        self._new_game()
        try:
            self.best_time = self._load_best()
        except Exception:
            self.best_time = 0

    def _new_game(self):
        self.world = World()
        sx, sy = self.world.spawn_point()
        self.player = Player(sx, sy)
        self.enemies = spawn_enemies(self.world, n=4)
        self.keys = spawn_keys(self.world)
        self.panels = spawn_panels(self.world, n=2)
        ex, ey = self.world.exit_point()
        self.exit = Exit(ex, ey)
        self.camera = Camera(MAP_W, MAP_H)
        self.hud = HUD(self.font_small, self.font)

        self.lights_off_timer = 0.0
        self.alert_level = 0.0
        self.caught_timer = 0.0
        self.play_time = 0.0
        self.best_time = getattr(self, "best_time", 0) or 0

    def _load_best(self):
        import os, json
        p = os.path.expanduser("~/.bunny_protocol_best.json")
        try:
            with open(p) as f:
                return json.load(f).get("best_time", 0)
        except Exception:
            return 0

    def _save_best(self, t):
        import os, json
        if self.best_time == 0 or t < self.best_time:
            self.best_time = t
            p = os.path.expanduser("~/.bunny_protocol_best.json")
            try:
                with open(p, "w") as f:
                    json.dump({"best_time": t}, f)
            except Exception:
                pass

    def _restart(self):
        self._new_game()
        self.state = "play"

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            self.running = False
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.running = False
            if self.state == "title" and e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = "play"
            elif self.state in ("caught", "win") and e.key == pygame.K_RETURN:
                self._restart()
            elif self.state == "play" and e.key == pygame.K_e:
                self._try_interact()

    def _try_interact(self):
        """E — взаимодействие с ближайшей панелью."""
        for panel in self.panels:
            if panel.used:
                continue
            if panel.dist_to(self.player) < 50:
                panel.used = True
                if panel.kind == "lights":
                    self.lights_off_timer = 5.0
                else:
                    # Открыть дверь = телепорт к выходу (упрощение)
                    # На деле — просто пропустим, замок на выходе
                    pass
                break

    def update(self, dt):
        self.timer += dt

        if self.state != "play":
            return

        self.play_time += dt

        # Игрок
        keys = pygame.key.get_pressed()
        self.player.update(dt, keys, self.world)

        # Камера
        self.camera.follow(self.player.x, self.player.y)

        # Враги
        caught = False
        for e in self.enemies:
            res = e.update(dt, self.player, self.world, self.enemies)
            if res == "caught":
                caught = True

        # Alert level — максимум по врагам
        self.alert_level = max((e.suspicion for e in self.enemies), default=0.0)

        # Поймали?
        if caught and self.caught_timer <= 0:
            self.state = "caught"
            self.caught_timer = 1.0

        # Свет выключен
        if self.lights_off_timer > 0:
            self.lights_off_timer -= dt
            if self.lights_off_timer <= 0:
                self.lights_off_timer = 0
                # Восстанавливаем
            else:
                # Ослабляем зрение врагов
                for e in self.enemies:
                    e.suspicion = max(0.0, e.suspicion - dt * 2)

        # Ключи
        for k in self.keys:
            if k.update(dt, self.player):
                self.player.keys_collected += 1

        # Выход
        if self.exit.can_enter(self.player, self.player.keys_collected):
            self.state = "win"
            self._save_best(self.play_time)

    def _draw_world_with_fov_darken(self):
        """Мир + туман вне зоны видимости игрока."""
        draw_world(self.screen, self.world, self.camera)

        # Если свет отключён — сильнее туман
        fog_alpha = 100 if self.lights_off_timer > 0 else 40

        # Виньетка (тёмные края вокруг игрока)
        fog = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        fog.fill((0, 0, 0, fog_alpha))
        # Вырезаем круг вокруг игрока
        px = int(self.player.x - self.camera.x)
        py = int(self.player.y - self.camera.y)
        pygame.draw.circle(fog, (0, 0, 0, 0), (px, py), 260)
        self.screen.blit(fog, (0, 0))

    def draw(self):
        if self.state == "title":
            self._draw_title()
        else:
            self._draw_world_with_fov_darken()

            # Ключи, панели, выход
            for k in self.keys:
                k.draw(self.screen, int(self.camera.x), int(self.camera.y))
            for p in self.panels:
                p.draw(self.screen, int(self.camera.x), int(self.camera.y))
            self.exit.draw(self.screen, int(self.camera.x), int(self.camera.y),
                          self.player.keys_collected)

            # Враги
            for e in self.enemies:
                e.draw(self.screen, int(self.camera.x), int(self.camera.y))

            # Игрок
            self.player.draw(self.screen, int(self.camera.x), int(self.camera.y))

            # HUD
            self.hud._play_time = self.play_time
            self.hud.draw(self.screen, self.player.keys_collected,
                          KEYS_REQUIRED, self.alert_level,
                          self.lights_off_timer)

            # Подсказка E
            for p in self.panels:
                if not p.used and p.dist_to(self.player) < 50:
                    self.hud.draw_interact_hint(self.screen, p.kind)
                    break

            # Оверлеи
            if self.state == "caught":
                self.hud.draw_overlay(self.screen, "ОБНАРУЖЕН",
                                     "Система опознала тебя", ALERT)
            elif self.state == "win":
                best_str = f"Лучшее: {int(self.best_time)}с" if self.best_time else ""
                t_str = f"Время: {int(self.play_time)}с   {best_str}"
                self.hud.draw_overlay(self.screen, "ПРОНИКНОВЕНИЕ",
                                     t_str, OK)

        pygame.display.flip()

    def _draw_title(self):
        self.screen.fill(BG)
        t = self.font_big.render("BUNNY", True, (120, 200, 255))
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 140))
        t2 = self.font_big.render("PROTOCOL", True, (255, 80, 140))
        self.screen.blit(t2, (WIDTH // 2 - t2.get_width() // 2, HEIGHT // 2 - 60))

        s = self.font.render("проникновение · стелс · данные", True, TEXT_DIM)
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 40))

        if int(self.timer * 2) % 2 == 0:
            h = self.font.render("ENTER — начать", True, TEXT)
            self.screen.blit(h, (WIDTH // 2 - h.get_width() // 2,
                                HEIGHT // 2 + 110))

        ctrl = [
            "WASD / стрелки — движение",
            "Shift — бег",
            "E — хакерская панель (отключить свет)",
            "Собери 3 ключа и дойди до выхода",
            "Esc — выход",
        ]
        for i, line in enumerate(ctrl):
            ct = self.font_small.render(line, True, TEXT_DIM)
            self.screen.blit(ct, (WIDTH // 2 - ct.get_width() // 2,
                                   HEIGHT - 160 + i * 22))

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            for e in pygame.event.get():
                self.handle_event(e)
            self.update(dt)
            self.draw()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    Game().run()
