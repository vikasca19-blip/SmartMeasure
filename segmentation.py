import cv2
import numpy as np


def extract_object(frame, box):
    """
    Improved object extraction using GrabCut segmentation.

    Returns:
        contour
        mask
        cropped image
    """

    x1, y1, x2, y2 = map(int, box)

    # Keep coordinates inside image
    h, w = frame.shape[:2]

    x1 = max(0, x1)
    y1 = max(0, y1)
    x2 = min(w, x2)
    y2 = min(h, y2)

    crop = frame[y1:y2, x1:x2]

    if crop.size == 0:
        return None, None, None

    # -----------------------------
    # GrabCut Segmentation
    # -----------------------------

    mask = np.zeros(crop.shape[:2], np.uint8)

    bgModel = np.zeros((1, 65), np.float64)
    fgModel = np.zeros((1, 65), np.float64)

    rect = (
        5,
        5,
        max(1, crop.shape[1] - 10),
        max(1, crop.shape[0] - 10)
    )

    try:

        cv2.grabCut(
            crop,
            mask,
            rect,
            bgModel,
            fgModel,
            5,
            cv2.GC_INIT_WITH_RECT
        )

    except Exception:
        return None, None, crop

    # Foreground mask
    mask = np.where(
        (mask == 2) | (mask == 0),
        0,
        255
    ).astype("uint8")

    # -----------------------------
    # Clean Mask
    # -----------------------------

    kernel = np.ones((5, 5), np.uint8)

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_OPEN,
        kernel,
        iterations=1
    )

    mask = cv2.morphologyEx(
        mask,
        cv2.MORPH_CLOSE,
        kernel,
        iterations=2
    )

    # -----------------------------
    # Find Largest Contour
    # -----------------------------

    contours, _ = cv2.findContours(
        mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE
    )

    if not contours:
        return None, mask, crop

    contour = max(
        contours,
        key=cv2.contourArea
    )

    # Ignore tiny contours
    if cv2.contourArea(contour) < 300:
        return None, mask, crop

    return contour, mask, crop