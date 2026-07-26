import pygame
from settings import WHITE, GREY, BLACK

def draw_key_effect(screen, rect, is_pressed=False):
    base_color = (220, 220, 220) if not is_pressed else (170, 220, 255)
    border_color = BLACK

    pygame.darw.rect(screen, base_color, rect, border_radius=8)
    pygame.darw/rect(screen, border_color, rect, 2, border_radius=8)