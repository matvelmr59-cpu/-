from __future__ import annotations

from pathlib import Path

from kivy import platform
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty,
    NumericProperty,
    ObjectProperty,
    StringProperty,
)
from kivy.uix.image import Image

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import MDSnackbar


BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"


def load_sound(relative_path: str):
    """Завантажує звук. Якщо файла немає, гра продовжить працювати без нього."""
    path = ASSETS_DIR / relative_path
    if not path.exists():
        return None
    return SoundLoader.load(str(path))


def play_sound(sound, *, volume: float | None = None) -> None:
    """Безпечно відтворює звук."""
    app = MDApp.get_running_app()
    if not app or not app.sound_enabled or sound is None:
        return

    if volume is not None:
        sound.volume = volume
    sound.play()


class Menu(MDScreen):
    def go_game(self, *args) -> None:
        self.manager.transition.direction = "left"
        self.manager.current = "game"

    def go_settings(self, *args) -> None:
        self.manager.transition.direction = "up"
        self.manager.current = "settings"

    def exit_app(self, *args) -> None:
        MDApp.get_running_app().stop()


class Settings(MDScreen):
    def go_menu(self, *args) -> None:
        self.manager.transition.direction = "down"
        self.manager.current = "menu"


class RotatedImage(Image):
    angle = NumericProperty(0)


class Fish(RotatedImage):
    """Риба: приймає кліки, програє анімації та повідомляє екран про HP."""

    game_screen = ObjectProperty(None, allownone=True)

    anim_play = BooleanProperty(False)
    interaction_block = BooleanProperty(True)
    fish_current = StringProperty("")
    fish_index = NumericProperty(0)
    hp_current = NumericProperty(0)

    COEF_MULT = 1.35

    click_sound = load_sound("audios/bubble01.mp3")
    defeated_sound = load_sound("audios/fish_def.ogg")

    def new_fish(self, *args) -> None:
        app = MDApp.get_running_app()
        level_fishes = app.LEVELS[app.LEVEL]

        self.fish_current = level_fishes[self.fish_index]
        fish_data = app.FISHES[self.fish_current]

        self.source = app.asset(fish_data["source"])
        self.hp_current = fish_data["hp"]

        self.angle = 0
        self.size = dp(200), dp(200)
        self.opacity = 1
        self.anim_play = False
        self.interaction_block = True

        self.game_screen.set_fish_health(
            current=self.hp_current,
            maximum=fish_data["hp"],
        )
        self.swim()

    def swim(self) -> None:
        """Риба випливає зліва та зупиняється в центрі ігрової області."""
        if self.parent is None:
            return

        self.x = -self.width
        self.center_y = self.parent.height / 2

        swim_animation = Animation(
            x=self.parent.width / 2 - self.width / 2,
            duration=1,
            transition="out_quad",
        )
        swim_animation.bind(
            on_complete=lambda *_: setattr(self, "interaction_block", False)
        )
        swim_animation.start(self)

    def defeated(self) -> None:
        """Анімація перемоги над рибою."""
        self.interaction_block = True
        self.game_screen.set_fish_health(current=0, maximum=1)

        old_size = self.size[:]
        old_pos = self.pos[:]

        new_size = (
            self.width * self.COEF_MULT * 2.2,
            self.height * self.COEF_MULT * 2.2,
        )
        new_pos = (
            self.x - (new_size[0] - self.width) / 2,
            self.y - (new_size[1] - self.height) / 2,
        )

        animation = Animation(angle=self.angle + 360, duration=0.8, transition="in_cubic")
        animation &= (
            Animation(size=new_size, duration=0.45, transition="out_back")
            + Animation(size=old_size, duration=0)
        )
        animation &= (
            Animation(pos=new_pos, duration=0.45, transition="out_back")
            + Animation(pos=old_pos, duration=0)
        )
        animation &= Animation(opacity=0, duration=0.75)
        animation.start(self)

        play_sound(self.defeated_sound)

    def on_touch_down(self, touch):
        if (
            not self.collide_point(*touch.pos)
            or self.anim_play
            or self.interaction_block
        ):
            return super().on_touch_down(touch)

        self.hp_current -= 1
        self.game_screen.score += 1
        self.game_screen.set_fish_health(
            current=self.hp_current,
            maximum=MDApp.get_running_app().FISHES[self.fish_current]["hp"],
        )
        play_sound(self.click_sound)

        if self.hp_current > 0:
            self.play_click_animation()
        else:
            self.defeated()
            app = MDApp.get_running_app()
            level_fishes = app.LEVELS[app.LEVEL]

            if self.fish_index + 1 < len(level_fishes):
                self.fish_index += 1
                Clock.schedule_once(self.new_fish, 1.2)
            else:
                Clock.schedule_once(self.game_screen.level_complete, 1.2)

        return True

    def play_click_animation(self) -> None:
        """Коротке збільшення риби після вдалого кліку."""
        old_size = self.size[:]
        old_pos = self.pos[:]

        new_size = (
            self.width * self.COEF_MULT,
            self.height * self.COEF_MULT,
        )
        new_pos = (
            self.x - (new_size[0] - self.width) / 2,
            self.y - (new_size[1] - self.height) / 2,
        )

        zoom = (
            Animation(size=new_size, duration=0.06)
            + Animation(size=old_size, duration=0.06)
        )
        zoom &= (
            Animation(pos=new_pos, duration=0.06)
            + Animation(pos=old_pos, duration=0.06)
        )

        self.anim_play = True
        zoom.bind(on_complete=lambda *_: setattr(self, "anim_play", False))
        zoom.start(self)


class Game(MDScreen):
    score = NumericProperty(0)
    fish_hp = NumericProperty(0)
    fish_hp_max = NumericProperty(1)
    fish_hp_percent = NumericProperty(0)

    background_sound = load_sound("audios/Black_Swan_part.mp3")
    level_complete_sound = load_sound("audios/level_complete.ogg")

    if background_sound is not None:
        background_sound.loop = True

    def on_pre_enter(self, *args):
        app = MDApp.get_running_app()
        app.LEVEL = 0

        self.score = 0
        self.fish_hp = 0
        self.fish_hp_max = 1
        self.fish_hp_percent = 0

        fish = self.ids.fish
        fish.fish_index = 0
        fish.opacity = 0
        fish.interaction_block = True

        complete_label = self.ids.level_complete
        complete_label.opacity = 0
        complete_label.font_size = dp(30)

        level_title = self.ids.level_title
        level_title.opacity = 0
        level_title.y = dp(80)

        return super().on_pre_enter(*args)

    def on_enter(self, *args):
        title = self.ids.level_title

        title_animation = (
            Animation(
                y=(self.ids.game_window.height - title.height) / 2 + dp(60),
                opacity=1,
                duration=0.7,
            )
            + Animation(y=self.ids.game_window.height, opacity=0, duration=0.8)
        )
        title_animation.bind(on_complete=self.start_game)
        title_animation.start(title)

        if self.background_sound is not None:
            self.background_sound.stop()
        play_sound(self.background_sound, volume=0.35)

        return super().on_enter(*args)

    def start_game(self, *args) -> None:
        self.ids.fish.new_fish()

    def set_fish_health(self, *, current: int, maximum: int) -> None:
        self.fish_hp = max(0, current)
        self.fish_hp_max = max(1, maximum)
        self.fish_hp_percent = self.fish_hp / self.fish_hp_max * 100

    def level_complete(self, *args) -> None:
        label = self.ids.level_complete
        animation = Animation(font_size=dp(54), opacity=1, duration=0.35)
        animation.start(label)

        if self.background_sound is not None:
            self.background_sound.volume = 0.15
        play_sound(self.level_complete_sound)

        MDApp.get_running_app().show_message(
            f"Рівень завершено! Результат: {self.score}"
        )

    def go_home(self) -> None:
        self.ids.fish.interaction_block = True
        Animation(opacity=0, duration=0.1).start(self.ids.fish)

        if self.background_sound is not None:
            self.background_sound.stop()

        self.manager.transition.direction = "right"
        self.manager.current = "menu"


class ClickerApp(MDApp):
    LEVEL = 0

    sound_enabled = BooleanProperty(True)
    dark_theme = BooleanProperty(False)

    FISHES = {
        "fish1": {"source": "images/fish_01.png", "hp": 10},
        "fish2": {"source": "images/fish_02.png", "hp": 20},
    }

    LEVELS = [
        ["fish1", "fish1", "fish2"],
    ]

    def asset(self, relative_path: str) -> str:
        """Повертає абсолютний шлях до ресурсу з папки assets."""
        return str(ASSETS_DIR / relative_path)

    def build(self):
        self.title = "Underwater Clicker"

        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "600"
        self.theme_cls.accent_palette = "Amber"
        self.theme_cls.material_style = "M2"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.theme_style_switch_animation = True
        self.theme_cls.theme_style_switch_animation_duration = 0.35

        Builder.load_file(str(BASE_DIR / "clicker.kv"))

        manager = MDScreenManager()
        manager.add_widget(Menu(name="menu"))
        manager.add_widget(Game(name="game"))
        manager.add_widget(Settings(name="settings"))
        return manager

    def set_theme(self, dark: bool) -> None:
        self.dark_theme = bool(dark)
        self.theme_cls.theme_style = "Dark" if self.dark_theme else "Light"

    def set_sound(self, enabled: bool) -> None:
        self.sound_enabled = bool(enabled)
        if not self.sound_enabled and Game.background_sound is not None:
            Game.background_sound.stop()

    def show_message(self, text: str) -> None:
        MDSnackbar(
            MDLabel(
                text=text,
                theme_text_color="Custom",
                text_color=(1, 1, 1, 1),
                adaptive_height=True,
            ),
            duration=2.5,
            y=dp(12),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.94,
        ).open()


if platform != "android":
    Window.size = (450, 900)


if __name__ == "__main__":
    ClickerApp().run()
