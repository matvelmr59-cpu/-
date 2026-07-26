from pygame import mixer
def load_sounds(keys):
    sounds = {}
    for key, filename in keys.items():
        sounds[keys] = mixer.Sound(f"assets/sounds/{filename}")
    return sounds
