# mouse_controller.py
import time
import math
import random
from ctypes import windll, Structure, c_long, byref
import win32api, win32con  # Do myszki
import keyboard  # Do klawiatury


class POINT(Structure):
    _fields_ = [("x", c_long), ("y", c_long)]


def get_cursor_pos():
    pt = POINT()
    windll.user32.GetCursorPos(byref(pt))
    return pt.x, pt.y


def set_cursor_pos(x, y):
    windll.user32.SetCursorPos(x, y)


class MouseController:
    def __init__(self):
        self.screen_width = 1920
        self.screen_height = 1080

    def _bezier_curve(self, t, p0, p1, p2, p3):
        return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ^ 2 * p2 + t ** 3 * p3

    def move_to(self, target_x, target_y, duration=0.5):
        start_x, start_y = get_cursor_pos()
        if (start_x, start_y) == (target_x, target_y): return

        dist = math.hypot(target_x - start_x, target_y - start_y)
        offset = dist * 0.2

        p1_x = start_x + (target_x - start_x) * 0.3 + random.uniform(-offset, offset)
        p1_y = start_y + (target_y - start_y) * 0.3 + random.uniform(-offset, offset)
        p2_x = start_x + (target_x - start_x) * 0.7 + random.uniform(-offset, offset)
        p2_y = start_y + (target_y - start_y) * 0.7 + random.uniform(-offset, offset)

        # Mniej kroków = mniejsze obciążenie CPU przy ruchu
        steps = int(duration * 40)
        if steps < 1: steps = 1

        path = []
        for i in range(steps + 1):
            t = i / steps
            # cubic bezier calculation... (uproszczone dla czytelnosci w tym bloku)
            bx = (1 - t) ** 3 * start_x + 3 * (1 - t) ** 2 * t * p1_x + 3 * (1 - t) * t ** 2 * p2_x + t ** 3 * target_x
            by = (1 - t) ** 3 * start_y + 3 * (1 - t) ** 2 * t * p1_y + 3 * (1 - t) * t ** 2 * p2_y + t ** 3 * target_y
            path.append((int(bx), int(by)))

        for point in path:
            set_cursor_pos(point[0], point[1])
            time.sleep(duration / steps)

    def click(self, button='left'):
        if button == 'left':
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            time.sleep(random.uniform(0.05, 0.1))
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif button == 'right':
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            time.sleep(random.uniform(0.05, 0.1))
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)

    def press(self, key):
        """Nowa funkcja: Naciśnij klawisz na klawiaturze"""
        keyboard.press(key)
        time.sleep(random.uniform(0.05, 0.1))
        keyboard.release(key)