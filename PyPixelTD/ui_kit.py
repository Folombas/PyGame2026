"""UI-кит: 9-patch окна, кнопки, панели — из темы Wood."""
import pygame
import assets


def draw_9patch(surface, rect, patch, corner=4):
    """Рисует 9-patch: углы не растягиваются, края и центр — тянутся.
    patch — Surface 16×16 (или больше), corner — размер угла в исходнике."""
    pw, ph = patch.get_size()
    x, y, w, h = rect.x, rect.y, rect.w, rect.h
    c = corner

    # Углы (не растягиваются)
    surface.blit(patch, (x, y), pygame.Rect(0, 0, c, c))                                     # TL
    surface.blit(patch, (x + w - c, y), pygame.Rect(pw - c, 0, c, c))                        # TR
    surface.blit(patch, (x, y + h - c), pygame.Rect(0, ph - c, c, c))                        # BL
    surface.blit(patch, (x + w - c, y + h - c), pygame.Rect(pw - c, ph - c, c, c))           # BR

    # Края (растягиваем в одном направлении)
    mid_w = pw - 2 * c
    mid_h = ph - 2 * c
    # верх
    top = pygame.transform.scale(patch.subsurface(pygame.Rect(c, 0, mid_w, c)), (w - 2 * c, c))
    surface.blit(top, (x + c, y))
    # низ
    bot = pygame.transform.scale(patch.subsurface(pygame.Rect(c, ph - c, mid_w, c)), (w - 2 * c, c))
    surface.blit(bot, (x + c, y + h - c))
    # лево
    left = pygame.transform.scale(patch.subsurface(pygame.Rect(0, c, c, mid_h)), (c, h - 2 * c))
    surface.blit(left, (x, y + c))
    # право
    right = pygame.transform.scale(patch.subsurface(pygame.Rect(pw - c, c, c, mid_h)), (c, h - 2 * c))
    surface.blit(right, (x + w - c, y + c))
    # центр
    center = pygame.transform.scale(
        patch.subsurface(pygame.Rect(c, c, mid_w, mid_h)),
        (w - 2 * c, h - 2 * c))
    surface.blit(center, (x + c, y + c))


# ============ КЕШ СПРАЙТОВ ============
_cache = {}


def get(name, scale=1):
    """Загружает PNG из assets/ui/theme/."""
    key = (name, scale)
    if key in _cache:
        return _cache[key]
    img = assets.load_image(f"ui/theme/{name}.png")
    if img is not None and scale != 1:
        img = pygame.transform.scale_by(img, scale)
    _cache[key] = img
    return img


def draw_window(surface, rect):
    """Окно в стиле Wood."""
    panel = get("nine_path_panel", scale=1)
    if panel is None:
        # fallback — процедурный
        pygame.draw.rect(surface, (240, 235, 220), rect)
        pygame.draw.rect(surface, (60, 40, 30), rect, 2)
        return
    draw_9patch(surface, rect, panel, corner=4)


def draw_panel(surface, rect):
    """Внутренняя панель (контент окна) — фон."""
    bg = get("nine_path_bg", scale=1)
    if bg is None:
        pygame.draw.rect(surface, (245, 240, 225), rect)
        return
    draw_9patch(surface, rect, bg, corner=4)


def draw_button(surface, rect, state="normal"):
    """Кнопка в стиле Wood. state: normal | hover | pressed."""
    name = {
        "normal": "button_normal",
        "hover": "button_hover",
        "pressed": "button_pressed",
        "checked": "button_checked",
    }.get(state, "button_normal")
    btn = get(name, scale=1)
    if btn is None:
        col = (200, 180, 150) if state == "normal" else (220, 200, 170)
        pygame.draw.rect(surface, col, rect, border_radius=3)
        return
    draw_9patch(surface, rect, btn, corner=4)


def draw_cell(surface, rect):
    """Ячейка инвентаря."""
    cell = get("inventory_cell", scale=1)
    if cell is None:
        pygame.draw.rect(surface, (60, 50, 40), rect)
        pygame.draw.rect(surface, (150, 130, 100), rect, 1)
        return
    draw_9patch(surface, rect, cell, corner=4)


def draw_tab(surface, rect, selected=False):
    """Вкладка."""
    name = "tab_selected" if selected else "tab"
    tab = get(name, scale=1)
    if tab is None:
        pygame.draw.rect(surface, (200, 180, 150), rect)
        return
    draw_9patch(surface, rect, tab, corner=4)
