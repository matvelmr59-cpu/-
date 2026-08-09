from pygame import Rect, mouse, MOUSEBUTTONDOWN, draw

class ToggleSwitch:
    def __init__(self, x, y, width=120, height=36, label="Генерація рандомних звуків", initial=False, on_change=None):
        self.rect = Rect(x, y, width, height)
        self.label = label
        self.value = bool(initial)
        self.on_change = on_change
        self._knob_margin = 4

        # стилі
        self.bg_off = (200, 200, 200)
        self.bg_on  = (120, 200, 160)
        self.border = (0, 0, 0)
        self.knob   = (255, 255, 255)
        self.text   = (0, 0, 0)

    def draw(self, screen, font):
        r = self.rect
        bg = self.bg_on if self.value else self.bg_off
        draw.rect(screen, bg, r, border_radius=r.h // 2)
        draw.rect(screen, self.border, r, 2, border_radius=r.h // 2)

        knob_d = r.h - self._knob_margin * 2
        knob_x = r.x + self._knob_margin if not self.value else r.right - self._knob_margin - knob_d
        knob_rect = Rect(knob_x, r.y + self._knob_margin, knob_d, knob_d)
        draw.ellipse(screen, self.knob, knob_rect)
        draw.ellipse(screen, self.border, knob_rect, 1)

        if self.label:
            text = f"{self.label}: {'ON' if self.value else 'OFF'}"
            ts = font.render(text, True, self.text)
            screen.blit(ts, (r.right + 10, r.y + (r.h - ts.get_height()) // 2))

    def handle_event(self, event):
        if event.type == MOUSEBUTTONDOWN and self.rect.collidepoint(mouse.get_pos()):
            self.value = not self.value
            if self.on_change:
                self.on_change(self.value)
