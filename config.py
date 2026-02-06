# config.py
import numpy as np

# --- SYSTEMOWE ---
GAME_WINDOW_TITLE = "League of Legends (TM) Client"
DEBUG_MODE = True
SHOW_FPS = True
DEBUG_RENDER_SKIP = 3

# --- KOLORY ---
LOWER_GREEN = np.array([40, 100, 100])
UPPER_GREEN = np.array([80, 255, 255])
LOWER_RED_1 = np.array([0, 100, 100])
UPPER_RED_1 = np.array([10, 255, 255])
LOWER_RED_2 = np.array([170, 100, 100])
UPPER_RED_2 = np.array([180, 255, 255])

# --- GEOMETRIA ---
MIN_HP_BAR_WIDTH = 25
MIN_HP_BAR_HEIGHT = 3
MAX_HP_BAR_HEIGHT = 25
ATTACK_RANGE = 750

# --- LOGIKA WALKI ---
UNIT_Y_OFFSET = 75

# FIX 1: Zwiększamy próg ucieczki.
# Wcześniej 30px było za mało. Przy 45px bot szybciej uzna, że jest źle.
CRITICAL_HP_WIDTH = 45

ATTACK_WINDUP = 0.5
ATTACK_COOLDOWN = 2.0
MOVE_COOLDOWN = 0.5

# FIX 2: Ochrona przed wieżą (Smycz)
# Bot zaatakuje wroga TYLKO, jeśli wróg jest bliżej niż 500px od Kotwicy.
# Jeśli wróg jest dalej (np. pod wieżą), bot go zignoruje.
MAX_CHASE_DISTANCE = 500

# --- LOGIKA MAPY ---
RECALL_CHANNEL_TIME = 9.0
WALK_TO_LANE_TIME = 28.0
BASE_POS_X = 100
BASE_POS_Y = 900