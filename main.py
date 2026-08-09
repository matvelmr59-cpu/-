from random import choice
from pygame import *
from settings import *

from sounds import load_sounds
from keys import draw_keys, create_key_rects
from buttons import Button
from ui.settings_menu import SettingsMenu
from ui.toggle_switch import ToggleSwitch
from soundgen import generate_random_bank

init()
display.set_caption("Piano Game")


sounds = load_sounds(KEYS)
all_sounds_list = list(sounds.values()) # №3 для рандомного режиму
GEN_DIR = "assets/data/sounds"     # куди пишемо синтетичні wav
generated_sounds = {}              # key -> Sound (коли тумблер ON)


key_rects = create_key_rects(len(KEYS))
keys_list = list(KEYS.keys())
my_font = font.SysFont("Arial", 24)
pressed_keys = set()

screen_mode = "main"
settings_menu = None
random_toggle = None  # №3
use_random_sounds = False # №3

current_volume = 1.0
for s in sounds.values():
    try:
        s.set_volume(current_volume)
    except Exception:
        pass

num_keys = len(KEYS)

keys_list = list(KEYS.keys())[:num_keys]
key_rects = create_key_rects(num_keys)


def _on_toggle_random(value: bool):
    global use_random_sounds, generated_sounds
    use_random_sounds = bool(value)

    if use_random_sounds:
        # 1) генеруємо рівно len(KEYS) звуків у GEN_DIR
        paths = generate_random_bank(GEN_DIR, len(KEYS))
        # 2) завантажуємо і розкладаємо по клавішах у порядку KEYS
        generated_sounds = {}
        for key_name, path in zip(KEYS.keys(), paths):
            try:
                snd = mixer.Sound(path)
                snd.set_volume(current_volume)
                generated_sounds[key_name] = snd
            except Exception:
                pass
    else:
        # повертаємось до твоєї мапи
        generated_sounds = {}


def apply_settings(volume: float, key_count: int):
    global current_volume, num_keys, keys_list, key_rects, pressed_keys
    current_volume = float(max(0.0, min(1.0, volume)))
    for s in sounds.values():
        try:
            s.set_volume(current_volume)
        except Exception:
            pass

    for s in generated_sounds.values():
        try:
            s.set_volume(current_volume)
        except Exception:
            pass

    key_count = max(1, min(len(KEYS), int(key_count)))
    if key_count != num_keys:
        num_keys = key_count
        keys_list = list(KEYS.keys())[:num_keys]
        key_rects = create_key_rects(num_keys)
        pressed_keys = {i for i in pressed_keys if i < num_keys}

def open_settings():
    global screen_mode, settings_menu, random_toggle
    screen_mode = "settings"
    settings_menu = SettingsMenu(
        screen.get_rect(),
        initial_volume=current_volume,
        initial_keys=num_keys,
        min_keys=1,
        max_keys=len(KEYS),
        on_change=apply_settings,
        on_back=lambda: _back_to_main(),
    )
    r = screen.get_rect()  # 3
    random_toggle = ToggleSwitch(
        x=r.x + 200, y=r.y + 290, width=100, height=36,
        initial=use_random_sounds,
        on_change=_on_toggle_random
    )  # 3


def _back_to_main():
    global screen_mode, settings_menu
    screen_mode = "main"
    settings_menu = None


def _play_for_key_name(k: str):
    if use_random_sounds and all_sounds_list:
        choice(all_sounds_list).play()
    else:
        snd = sounds.get(k)
        if snd:
            snd.play()

def _play_for_index(i: int):
    if 0 <= i < len(keys_list):
        k = keys_list[i]
        _play_for_key_name(k)


def _play_for_key_name(k: str):
    snd = None
    if use_random_sounds:
        snd = generated_sounds.get(k)
    if snd is None:
        snd = sounds.get(k)  # запасний варіант: твій оригінальний звук
    if snd:
        snd.play()


def exit_game(): quit()

SETTINGS_IDLE = transform.scale(
    image.load('assets/images/buttons/settings_unhover.png'), (50, 50)
)
SETTINGS_HOVER = transform.scale(
    image.load('assets/images/buttons/settings_hover.png'), (50, 50)
)

buttons = [
    Button(
        60, 20, 50, 50,
        "",
        open_settings,
        img_idle=SETTINGS_IDLE,
        img_hover=SETTINGS_HOVER
    )
]

running = True
while running:
    screen.fill(WHITE)
    if screen_mode == "settings" and settings_menu:
        settings_menu.draw(screen, my_font)
        if random_toggle:
            random_toggle.draw(screen, my_font)
    else:
        for button in buttons:
            button.draw(screen, my_font)
        draw_keys(screen, key_rects, pressed_keys)


    display.flip()

    for e in event.get():
        if e.type == QUIT:
            running = False
        if screen_mode == "settings" and settings_menu:
            settings_menu.handle_event(e)
            if random_toggle:
                random_toggle.handle_event(e)
            continue
        for button in buttons:
            button.handle_event(e)
        if e.type == KEYDOWN:
            k = key.name(e.key)
            if k in sounds and k in keys_list:
                _play_for_key_name(k)
                idx = keys_list.index(k)
                pressed_keys.add(idx)

        if e.type == KEYUP:
            k = key.name(e.key)
            if k in sounds and k in keys_list:
                idx = keys_list.index(k)
                if idx in pressed_keys:
                    pressed_keys.remove(idx)

        if e.type == MOUSEBUTTONDOWN:
            pos = e.pos
            for i, rect in enumerate(key_rects):
                if rect.collidepoint(pos):
                    _play_for_index(i)
                    pressed_keys.add(i)

        if e.type == MOUSEBUTTONUP:
            pos = e.pos
            for i, rect in enumerate(key_rects):
                if i in pressed_keys and rect.collidepoint(pos):
                    pressed_keys.remove(i)
