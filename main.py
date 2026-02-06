# main.py
import cv2
import time
import keyboard
import win32api
import numpy as np
from vision import Vision
from mouse_controller import MouseController
from bot_logic import LogicController, BotState
from config import DEBUG_MODE, SHOW_FPS, UNIT_Y_OFFSET, WALK_TO_LANE_TIME, DEBUG_RENDER_SKIP


def main():
    print("--- League Bot v1.1 (Keybind Fix) ---")
    vision = Vision()
    mouse = MouseController()
    logic = LogicController(vision.monitor['width'], vision.monitor['height'])

    print("INSTRUKCJA:")
    print("1. 'M' - Najedź na MINIMAPĘ (mid) i wciśnij, by zapisać cel.")
    print("2. 'S' - Ustaw kotwicę (tam gdzie stoisz).")
    print("3. ']' - START GRY (Idź na linię).")
    print("4. 'Q' - Wyjście.")

    time.sleep(1)
    loop_time = time.time()
    bot_active = True
    frame_counter = 0

    while True:
        frame_counter += 1

        # --- INPUT ---

        # 1. Kalibracja Minimapy (Klawisz M)
        if keyboard.is_pressed('m'):
            mx, my = win32api.GetCursorPos()
            # Przeliczamy na koordynaty okna gry
            gx = mx - vision.monitor['left']
            gy = my - vision.monitor['top']
            logic.set_minimap_target(gx, gy)
            print(f"CEL MINIMAPY ZAPISANY: {gx}, {gy}")
            time.sleep(0.5)

        # 2. Ustawienie Kotwicy (Klawisz S)
        if keyboard.is_pressed('s'):
            mx, my = win32api.GetCursorPos()
            logic.set_anchor(mx - vision.monitor['left'], my - vision.monitor['top'])
            print("KOTWICA USTAWIONA.")
            time.sleep(0.5)

        # 3. Start Gry (Klawisz ])
        if keyboard.is_pressed(']'):
            if logic.lane_minimap_pos is None:
                print("BŁĄD: Najpierw ustaw cel minimapy (Klawisz M)!")
            else:
                print("START - Idę na linię...")
                logic.state = BotState.WALKING_TO_LANE
                logic.lane_arrival_time = time.time() + WALK_TO_LANE_TIME
            time.sleep(0.5)

        # --- VISION ---
        frame = vision.get_frame()
        player_bar, player_mask = vision.find_player_health_bar(frame)
        enemy_bar, enemy_mask = vision.find_closest_enemy(frame, player_bar)

        # --- LOGIC ---
        decision = logic.decide_action(player_bar, enemy_bar)

        if decision and bot_active:
            action, t_x, t_y, param = decision

            # Przeliczamy na ekran
            screen_x = t_x + vision.monitor['left']
            screen_y = t_y + vision.monitor['top']

            if action == "ATTACK_COMBO":
                mouse.move_to(screen_x, screen_y, duration=0.05)
                if param: mouse.press(param)
                # mouse.click('right') # Odkomentuj dla auto-ataku

            elif action == "MOVE_CLICK":
                mouse.move_to(screen_x, screen_y, duration=0.15)
                mouse.click('right')

            elif action == "CAST_SPELL":
                # Tylko klawisz
                mouse.press(param)

            elif action == "MOVE_MINIMAP":
                # Koordynaty z kalibracji 'M' + offset okna
                final_x = t_x + vision.monitor['left']
                final_y = t_y + vision.monitor['top']

                print("Klikam Minimapę...")
                mouse.move_to(final_x, final_y, duration=0.2)
                mouse.click('right')

        # --- DEBUG ---
        if DEBUG_MODE and (frame_counter % DEBUG_RENDER_SKIP == 0):
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)

            # Rysuj cel minimapy (Fioletowe koło)
            if logic.lane_minimap_pos:
                mx, my = logic.lane_minimap_pos
                cv2.circle(small_frame, (mx // 2, my // 2), 5, (255, 0, 255), -1)
                cv2.putText(small_frame, "MAP TARGET", (mx // 2 - 20, my // 2 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                            (255, 0, 255), 1)

            if player_bar:
                px, py, pw, ph = player_bar
                cv2.rectangle(small_frame, (px // 2, py // 2), ((px + pw) // 2, (py + ph) // 2), (0, 255, 0), 1)

            if enemy_bar:
                ex, ey, ew, eh = enemy_bar
                cv2.rectangle(small_frame, (ex // 2, ey // 2), ((ex + ew) // 2, (ey + eh) // 2), (0, 0, 255), 1)

            cv2.putText(small_frame, f"State: {logic.state.name}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 255, 255), 1)

            if logic.state == BotState.WALKING_TO_LANE:
                rem = int(logic.lane_arrival_time - time.time())
                cv2.putText(small_frame, f"Walk: {rem}s", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 255), 1)

            cv2.imshow('Bot Lite', small_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        if keyboard.is_pressed('q'):
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()