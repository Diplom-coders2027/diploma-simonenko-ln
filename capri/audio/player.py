# audio/player.py — воспроизведение звуков
import os
import threading

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")

try:
    import pygame
    pygame.mixer.init()
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


def play(sound_name: str):
    """Воспроизвести звук по имени (без расширения)."""
    if not PYGAME_AVAILABLE:
        return
    sound_path = os.path.join(ASSETS_DIR, "sounds", f"{sound_name}.wav")
    if not os.path.exists(sound_path):
        return
    try:
        sound = pygame.mixer.Sound(sound_path)
        sound.play()
    except Exception as e:
        print(f"Audio error: {e}")


def play_async(sound_name: str):
    """Воспроизвести звук в отдельном потоке."""
    t = threading.Thread(target=play, args=(sound_name,), daemon=True)
    t.start()