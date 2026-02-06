# bot_logic.py
import time
import random
import math
from enum import Enum
from config import *


class BotState(Enum):
    IDLE = 0
    ROAM = 1
    RETREAT = 2
    ATTACK_INIT = 3
    ATTACK_MOVE = 4
    RECALLING = 5
    WALKING_TO_LANE = 6


class LogicController:
    def __init__(self, screen_width, screen_height):
        self.state = BotState.IDLE
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.last_action_time = 0
        self.next_attack_time = 0
        self.windup_end_time = 0
        self.recall_finish_time = 0
        self.lane_arrival_time = 0

        self.anchor_pos = None
        self.lane_minimap_pos = None

    def set_anchor(self, x, y):
        self.anchor_pos = (x, y)

    def set_minimap_target(self, x, y):
        self.lane_minimap_pos = (x, y)

    def decide_action(self, player_bar, enemy_bar):
        current_time = time.time()

        if self.state == BotState.IDLE: return None

        # 1. Marsz na linię
        if self.state == BotState.WALKING_TO_LANE:
            if current_time > self.lane_arrival_time:
                print("[LOGIC] Dotarlem. Ustawiam Anchor.")
                self.set_anchor(self.screen_width // 2, self.screen_height // 2)
                self.state = BotState.ROAM
                return None
            else:
                if current_time - self.last_action_time > 2.0:
                    self.last_action_time = current_time
                    if self.lane_minimap_pos:
                        return "MOVE_MINIMAP", self.lane_minimap_pos[0], self.lane_minimap_pos[1], None
                return None

        # 2. Recall
        if self.state == BotState.RECALLING:
            if current_time > self.recall_finish_time:
                print("[LOGIC] Recall done. Wracam.")
                if self.lane_minimap_pos:
                    self.state = BotState.WALKING_TO_LANE
                    self.lane_arrival_time = current_time + WALK_TO_LANE_TIME
                else:
                    self.state = BotState.ROAM
            return None

        if current_time < self.windup_end_time: return None
        if current_time - self.last_action_time < 0.1: return None

        if not player_bar: return None

        px, py, pw, ph = player_bar
        player_center = (px + pw // 2, py + ph // 2)
        safe_point = self.anchor_pos if self.anchor_pos else player_center

        # --- LOGIKA DECYZYJNA ---

        # 1. SPRAWDZANIE HP (Priorytet absolutny)
        if pw < CRITICAL_HP_WIDTH:
            # Debugowanie szerokości paska w konsoli
            if int(current_time * 5) % 10 == 0:
                print(f"[PANIC CHECK] Current HP Width: {pw}px (Threshold: {CRITICAL_HP_WIDTH})")

            dist_to_base = math.hypot(player_center[0] - BASE_POS_X, player_center[1] - BASE_POS_Y)
            if dist_to_base < 200:
                self.state = BotState.RECALLING
                self.recall_finish_time = current_time + RECALL_CHANNEL_TIME
                return "CAST_SPELL", 0, 0, 'b'
            else:
                self.state = BotState.RETREAT
                return None  # Zwracamy None tutaj, żeby ruch wykonał się w sekcji "Wykonanie" na dole

        # 2. WALKA (Z ochroną przed wieżą)
        elif enemy_bar:
            ex, ey, ew, eh = enemy_bar
            enemy_center = (ex + ew // 2, ey + eh // 2)

            # --- FIX: OCHRONA PRZED WIEŻĄ (SMYCZ) ---
            # Sprawdzamy, jak daleko wróg jest od naszej bezpiecznej Kotwicy.
            # Jeśli nie mamy kotwicy, używamy gracza jako punktu odniesienia.
            ref_point = self.anchor_pos if self.anchor_pos else player_center
            dist_enemy_to_anchor = math.hypot(enemy_center[0] - ref_point[0], enemy_center[1] - ref_point[1])

            if dist_enemy_to_anchor > MAX_CHASE_DISTANCE:
                # Wróg jest za daleko (pewnie pod wieżą). Ignorujemy go!
                # print("Wróg zbyt daleko - odpuszczam")
                self.state = BotState.ROAM
            else:
                # Wróg jest blisko - Walczymy
                if current_time >= self.next_attack_time:
                    self.state = BotState.ATTACK_INIT
                else:
                    self.state = BotState.ATTACK_MOVE

        # 3. ROAM
        else:
            self.state = BotState.ROAM

        # --- WYKONANIE RUCHU ---

        if self.state == BotState.RETREAT:
            target_x = BASE_POS_X + random.randint(-20, 20)
            target_y = BASE_POS_Y + random.randint(-20, 20)
            if current_time - self.last_action_time > 0.3:
                self.last_action_time = current_time
                print(f"[ACTION] RETREATING! HP Width: {pw}")
                return "MOVE_CLICK", target_x, target_y, None

        elif self.state == BotState.ATTACK_INIT:
            ex, ey, ew, eh = enemy_bar
            center_x = ex + ew // 2
            center_y = ey + eh // 2
            target_x = center_x + random.randint(-5, 5)
            target_y = center_y + UNIT_Y_OFFSET + random.randint(-5, 5)

            self.windup_end_time = current_time + ATTACK_WINDUP
            self.next_attack_time = current_time + ATTACK_COOLDOWN
            self.last_action_time = current_time
            return "ATTACK_COMBO", target_x, target_y, 'q'

        elif self.state == BotState.ATTACK_MOVE:
            if current_time - self.last_action_time < MOVE_COOLDOWN: return None
            dx = safe_point[0] - player_center[0]
            dy = safe_point[1] - player_center[1]
            dist = math.hypot(dx, dy)
            if dist < 150: return None  # Zmniejszony dystans powrotu
            step = 100
            scale = step / dist if dist > 0 else 0
            target_x = player_center[0] + dx * scale + random.randint(-20, 20)
            target_y = player_center[1] + dy * scale + random.randint(-20, 20)
            self.last_action_time = current_time
            return "MOVE_CLICK", target_x, target_y, None

        elif self.state == BotState.ROAM:
            # Roamuj tylko jeśli jesteś blisko kotwicy. Jak za daleko - wracaj.
            dist_to_anchor = math.hypot(player_center[0] - safe_point[0], player_center[1] - safe_point[1])

            if dist_to_anchor > 300:
                # Wracaj do bazy (kotwicy)
                target_x = safe_point[0]
                target_y = safe_point[1]
            else:
                # Kręć się
                offset_x = random.randint(-200, 200)
                offset_y = random.randint(-200, 200)
                target_x = safe_point[0] + offset_x
                target_y = safe_point[1] + offset_y

            if current_time - self.last_action_time > 2.5:
                self.last_action_time = current_time
                return "MOVE_CLICK", target_x, target_y, None

        return None