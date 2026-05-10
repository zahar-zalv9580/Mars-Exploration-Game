import pygame
import random
import os

MENU_MUSIC = "assets/audio/menu.ogg"
GAME_TRACKS = [
    "assets/audio/game1.ogg",
    "assets/audio/game2.ogg",
    "assets/audio/game3.ogg",
    "assets/audio/game4.ogg",
    "assets/audio/game5.ogg",
]

MUSIC_END_EVENT = pygame.USEREVENT + 1

_current_music_type = None  # може бути 'menu' і 'game'
_game_tracks = []
_current_track_index = -1

# Звукові ефекти
_sounds = {}

def init_audio():
    pygame.mixer.init()
    pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
    _load_tracks()
    _load_sounds()

def _load_tracks():
    global _game_tracks
    _game_tracks = [f for f in GAME_TRACKS if os.path.exists(f)]
    if not _game_tracks:
        print("Увага: Не знайдено файлів музики!")

def _load_sounds():
    sound_files = {
        'build': "assets/audio/build.wav",
        'collect': "assets/audio/collect.wav",
        'jammer_start': "assets/audio/jammer_start.wav"
    }
    for name, path in sound_files.items():
        if os.path.exists(path):
            _sounds[name] = pygame.mixer.Sound(path)
        else:
            _sounds[name] = None

def play_sound(name):
    s = _sounds.get(name)
    if s:
        s.play()

def set_sfx_volume(volume):
    for s in _sounds.values():
        if s:
            s.set_volume(volume)

def play_menu_music():
    global _current_music_type
    if not os.path.exists(MENU_MUSIC):
        return
    stop_music(fadeout_ms=200)
    pygame.mixer.music.load(MENU_MUSIC)
    pygame.mixer.music.play(-1)
    _current_music_type = 'menu'

def play_game_music():
    global _current_music_type, _current_track_index
    if not _game_tracks:
        return
    stop_music(fadeout_ms=300)
    _current_track_index = random.randrange(len(_game_tracks))
    pygame.mixer.music.load(_game_tracks[_current_track_index])
    pygame.mixer.music.play()
    _current_music_type = 'game'

def play_next_game_track():
    global _current_track_index
    if not _game_tracks:
        return
    if len(_game_tracks) == 1:
        next_index = 0
    else:
        next_index = _current_track_index
        while next_index == _current_track_index:
            next_index = random.randrange(len(_game_tracks))
    _current_track_index = next_index
    pygame.mixer.music.load(_game_tracks[_current_track_index])
    pygame.mixer.music.play()

def stop_music(fadeout_ms=500):
    pygame.mixer.music.fadeout(fadeout_ms)
    global _current_music_type
    _current_music_type = None

def set_music_volume(volume):
    pygame.mixer.music.set_volume(volume)