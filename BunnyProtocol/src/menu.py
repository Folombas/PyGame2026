import pygame
from .ui import Button


class MainMenu:
    def __init__(self, screen, audio):
        self.screen = screen
        self.audio = audio
        self.action = None

        self.title_font = pygame.font.SysFont("consolas", 58, bold=True)
        self.font = pygame.font.SysFont("consolas", 30, bold=True)
        self.small_font = pygame.font.SysFont("consolas", 20)

        w, h = screen.get_size()
        self.sound_button = Button(
            pygame.Rect(w // 2 - 180, h // 2 + 50, 360, 58),
            "SOUND: ON",
            self.font,
            audio,
            self.toggle_sound,
        )
        self.buttons = [
            Button(
                pygame.Rect(w // 2 - 180, h // 2 - 30, 360, 58),
                "START",
                self.font,
                audio,
                lambda: self.set_action("start"),
            ),
            self.sound_button,
            Button(
                pygame.Rect(w // 2 - 180, h // 2 + 130, 360, 58),
                "QUIT",
                self.font,
                audio,
                lambda: self.set_action("quit"),
            ),
        ]

    def set_action(self, action):
        self.action = action

    def reset(self):
        self.action = None

    def toggle_sound(self):
        enabled = self.audio.toggle_mute()
        self.sound_button.text = "SOUND: ON" if enabled else "SOUND: OFF"

    def handle_event(self, event):
        for button in self.buttons:
            button.handle_event(event)

    def update(self, dt):
        mouse_pos = pygame.mouse.get_pos()
        for button in self.buttons:
            button.update(mouse_pos)

    def draw(self):
        w, h = self.screen.get_size()
        self.screen.fill((8, 12, 20))

        for x in range(0, w, 48):
            pygame.draw.line(self.screen, (18, 28, 44), (x, 0), (x, h))
        for y in range(0, h, 48):
            pygame.draw.line(self.screen, (18, 28, 44), (0, y), (w, y))

        title = self.title_font.render("UNIX RABBIT", True, (130, 220, 255))
        subtitle = self.small_font.render("TERMINAL ARSENAL", True, (180, 200, 230))
        self.screen.blit(title, title.get_rect(center=(w // 2, h // 4)))
        self.screen.blit(subtitle, subtitle.get_rect(center=(w // 2, h // 4 + 55)))

        for button in self.buttons:
            button.draw(self.screen)

        hint = self.small_font.render("WASD move | Mouse shoot | 1/2 weapons | ESC menu", True, (120, 140, 170))
        self.screen.blit(hint, hint.get_rect(center=(w // 2, h - 40)))
