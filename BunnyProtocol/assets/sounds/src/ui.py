import pygame

class Button:
    def __init__(self, rect, text, font, audio, callback,
                 color=(30, 60, 90), hover_color=(50, 100, 150)):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.audio = audio
        self.callback = callback
        self.color = color
        self.hover_color = hover_color
        self.hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.audio.play("click")
                self.callback()
                return True
        return False

    def update(self, mouse_pos):
        hovered = self.rect.collidepoint(mouse_pos)
        if hovered and not self.hovered:
            self.audio.play("hover", 0.5)
        self.hovered = hovered

    def draw(self, surface):
        color = self.hover_color if self.hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        pygame.draw.rect(surface, (200, 220, 255), self.rect, 2, border_radius=10)
        text = self.font.render(self.text, True, (240, 245, 255))
        surface.blit(text, text.get_rect(center=self.rect.center))
