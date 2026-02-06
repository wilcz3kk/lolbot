# hsv_tuner.py
import cv2
import numpy as np
import mss
import time
import win32gui


def nothing(x):
    pass


# Ustawienia początkowe (zaczynamy od szerokiego zakresu czerwieni)
cv2.namedWindow("Kalibracja HSV")
cv2.createTrackbar("L_H", "Kalibracja HSV", 0, 179, nothing)
cv2.createTrackbar("L_S", "Kalibracja HSV", 100, 255, nothing)
cv2.createTrackbar("L_V", "Kalibracja HSV", 100, 255, nothing)

cv2.createTrackbar("U_H", "Kalibracja HSV", 10, 179, nothing)
cv2.createTrackbar("U_S", "Kalibracja HSV", 255, 255, nothing)
cv2.createTrackbar("U_V", "Kalibracja HSV", 255, 255, nothing)

# Pobieranie okna gry
sct = mss.mss()
GAME_WINDOW_TITLE = "League of Legends (TM) Client"

print("Instrukcja:")
print("1. Ustaw grę i bota obok siebie.")
print("2. Przesuwaj suwaki, aż pasek zdrowia wroga będzie BIAŁY, a tło CZARNE.")
print("3. Zapisz wyświetlone wartości do config.py.")

while True:
    hwnd = win32gui.FindWindow(None, GAME_WINDOW_TITLE)
    monitor = sct.monitors[1]
    if hwnd:
        rect = win32gui.GetWindowRect(hwnd)
        monitor = {'top': rect[1], 'left': rect[0], 'width': rect[2] - rect[0], 'height': rect[3] - rect[1]}

    screenshot = sct.grab(monitor)
    frame = np.array(screenshot)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

    # Pobierz wartości z suwaków
    l_h = cv2.getTrackbarPos("L_H", "Kalibracja HSV")
    l_s = cv2.getTrackbarPos("L_S", "Kalibracja HSV")
    l_v = cv2.getTrackbarPos("L_V", "Kalibracja HSV")
    u_h = cv2.getTrackbarPos("U_H", "Kalibracja HSV")
    u_s = cv2.getTrackbarPos("U_S", "Kalibracja HSV")
    u_v = cv2.getTrackbarPos("U_V", "Kalibracja HSV")

    lower_color = np.array([l_h, l_s, l_v])
    upper_color = np.array([u_h, u_s, u_v])

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_color, upper_color)

    # Wyświetlanie wyniku
    # Zmniejszamy obraz dla wygody
    result = cv2.bitwise_and(frame, frame, mask=mask)
    preview = np.hstack([cv2.resize(frame, (0, 0), fx=0.5, fy=0.5),
                         cv2.resize(result, (0, 0), fx=0.5, fy=0.5)])

    cv2.imshow("Kalibracja HSV", preview)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        print(f"\n--- TWOJE NOWE WARTOŚCI ---")
        print(f"LOWER_RED = np.array([{l_h}, {l_s}, {l_v}])")
        print(f"UPPER_RED = np.array([{u_h}, {u_s}, {u_v}])")
        break

cv2.destroyAllWindows()