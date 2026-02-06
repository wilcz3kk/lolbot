# vision.py
import cv2
import mss
import numpy as np
import win32gui
import math
from config import *


class Vision:
    def __init__(self):
        self.sct = mss.mss()
        self.monitor = self._get_window_geometry()

    def _get_window_geometry(self):
        hwnd = win32gui.FindWindow(None, GAME_WINDOW_TITLE)
        if not hwnd:
            return self.sct.monitors[1]

        rect = win32gui.GetWindowRect(hwnd)
        x, y, x2, y2 = rect
        w = x2 - x
        h = y2 - y
        return {'top': y, 'left': x, 'width': w, 'height': h}

    def get_frame(self):
        screenshot = self.sct.grab(self.monitor)
        frame = np.array(screenshot)
        return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    def find_player_health_bar(self, frame):
        """Szuka paska gracza (zielony)."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, LOWER_GREEN, UPPER_GREEN)

        # Lekka dylatacja dla gracza
        kernel = np.ones((3, 15), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        best_bar = None
        screen_center_x = frame.shape[1] // 2
        screen_center_y = frame.shape[0] // 2
        min_dist_to_center = float('inf')

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            if w > 30 and h > 2:
                center_x = x + w // 2
                center_y = y + h // 2
                dist = math.hypot(center_x - screen_center_x, center_y - screen_center_y)

                # Gracz zazwyczaj jest blisko środka
                if dist < 500 and dist < min_dist_to_center:
                    min_dist_to_center = dist
                    best_bar = (x, y, w, h)

        return best_bar, mask

    def find_closest_enemy(self, frame, player_pos):
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        mask1 = cv2.inRange(hsv, LOWER_RED_1, UPPER_RED_1)
        mask2 = cv2.inRange(hsv, LOWER_RED_2, UPPER_RED_2)
        mask = cv2.bitwise_or(mask1, mask2)

        # --- OPTYMALIZACJA FPS: Mniejszy Kernel ---
        # Zmniejszyłem kernel z 40 na 25. Mniej liczenia, a nadal skleja.
        kernel = np.ones((4, 25), np.uint8)
        mask = cv2.dilate(mask, kernel, iterations=1)

        # --- FIX: PLAYER BLACKOUT (IGNOROWANIE SIEBIE) ---
        # To jest kluczowe! Malujemy czarny prostokąt tam, gdzie jest gracz.
        if player_pos:
            px, py, pw, ph = player_pos
            # Powiększamy obszar wycięcia o 10px z każdej strony dla pewności
            cv2.rectangle(mask, (px - 10, py - 10), (px + pw + 10, py + ph + 10), 0, -1)
        else:
            # Fallback: Jeśli nie znaleziono gracza, wycinamy środek ekranu (zakładamy locked camera)
            cx, cy = frame.shape[1] // 2, frame.shape[0] // 2
            cv2.rectangle(mask, (cx - 60, cy - 60), (cx + 60, cy + 60), 0, -1)
        # -------------------------------------------------

        if player_pos:
            px, py, pw, ph = player_pos
            player_center = (px + pw // 2, py + ph // 2)
        else:
            player_center = (frame.shape[1] // 2, frame.shape[0] // 2)

        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        closest_enemy = None
        min_dist = float('inf')

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)

            if w > 30 and h > 2:
                enemy_center = (x + w // 2, y + h // 2)
                dist = math.hypot(enemy_center[0] - player_center[0], enemy_center[1] - player_center[1])

                # Dodatkowe zabezpieczenie: Nie atakuj niczego co jest BARDZO blisko (poniżej 80px)
                # To eliminuje bugi, gdzie bot atakuje własną broń/efekty cząsteczkowe
                if 80 < dist < ATTACK_RANGE and dist < min_dist:
                    min_dist = dist
                    closest_enemy = (x, y, w, h)

        return closest_enemy, mask