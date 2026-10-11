import cv2
import numpy as np

# A4 paper size (cm)
A4_WIDTH = 21.0
A4_HEIGHT = 29.7


def get_pixels_per_cm(contour):
    """
    Returns pixels per centimeter using detected A4 paper.
    """

    rect = cv2.minAreaRect(contour)

    (_, _), (w, h), _ = rect

    if w == 0 or h == 0:
        return None

    pixel_width = max(w, h)

    pixels_per_cm = pixel_width / A4_HEIGHT

    return pixels_per_cm


def pixels_to_cm(px, pixels_per_cm):

    return round(px / pixels_per_cm, 2)

def detect_a4(frame):

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(blur, 75, 200)

    contours, _ = cv2.findContours(
        edges,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    biggest = None
    max_area = 0

    for cnt in contours:

        area = cv2.contourArea(cnt)

        if area < 5000:
            continue

        peri = cv2.arcLength(cnt, True)

        approx = cv2.approxPolyDP(
            cnt,
            0.02 * peri,
            True
        )

        if len(approx) == 4:

            if area > max_area:
                biggest = approx
                max_area = area

    return biggest