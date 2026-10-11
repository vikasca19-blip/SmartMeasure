import cv2
import os

from vision.segmentation import extract_object
from vision.camera import(
    start_scan,
    get_current_mode
    )
from vision.shape_detector import (
    detect_shape,
    estimate_depth,
    draw_laser_cyan_mesh
)
from vision.volume import calculate_volume
from vision.measurement import pixels_to_cm
from datetime import datetime

print("USING:", __file__)


def analyze_capture(
    frame,
    label,
    confidence,
    bbox,
    pixels_per_cm
):
    """
    Heavy analysis performed ONLY after the
    user presses Capture.
    """

    x1, y1, x2, y2 = bbox

    processed = frame.copy()

    # ---------------------------------------
    # Object Width / Height
    # ---------------------------------------

    width_px = x2 - x1
    height_px = y2 - y1

    if pixels_per_cm:

        width = pixels_to_cm(
            width_px,
            pixels_per_cm
        )

        height = pixels_to_cm(
            height_px,
            pixels_per_cm
        )

    else:

        width = width_px
        height = height_px

    area = width * height

    # ---------------------------------------
    # GrabCut Segmentation
    # ---------------------------------------

    contour, mask, crop = extract_object(
        processed,
        (x1, y1, x2, y2)
    )

    # ---------------------------------------
    # Cyan Laser Mesh
    # ---------------------------------------

    draw_laser_cyan_mesh(
        processed,
        x1,
        y1,
        x2,
        y2
    )

    # ---------------------------------------
    # Draw Cyan Laser Mesh
    # ---------------------------------------


    overlay = processed.copy()

    if contour is not None:

        cv2.drawContours(
            overlay,
            [contour],
            -1,
            (255,255,0),
            10
        )

        overlay = cv2.GaussianBlur(
            overlay,
            (21,21),
            0
        )

        cv2.addWeighted(
            overlay,
            0.45,
            processed,
            0.55,
            0,
            processed
        )

    # ---------------------------------------
    # Draw Bounding Box
    # ---------------------------------------

    cv2.rectangle(
        processed,
        (x1, y1),
        (x2, y2),
        (0, 255, 0),
        2
    )

    # ---------------------------------------
    # Shape Detection
    # ---------------------------------------

    shape_info = detect_shape(
        label,
        width,
        height
    )

    shape = shape_info["shape"]

    # ---------------------------------------
    # Depth Estimation
    # ---------------------------------------

    depth = estimate_depth(
        width,
        shape_info
    )

    # ---------------------------------------
    # Volume
    # ---------------------------------------

    volume = calculate_volume(
        shape,
        width,
        height,
        depth
    )

    # ---------------------------------------
    # Measurement Overlay
    # ---------------------------------------

    cv2.putText(
        processed,
        f"{label}",
        (x1, y1 - 15),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0,255,0),
        2
    )

    cv2.putText(
        processed,
        f"W : {width:.2f} cm",
        (x1, y2 + 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255,255,255),
        2
    )

    cv2.putText(
        processed,
        f"H : {height:.2f} cm",
        (x1, y2 + 45),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255,255,255),
        2
    )

    cv2.putText(
        processed,
        f"D : {depth:.2f} cm",
        (x1, y2 + 70),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255,255,255),
        2
    )

    if volume is not None:

        cv2.putText(
            processed,
            f"V : {volume:.2f} cm3",
            (x1, y2 + 95),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0,255,255),
            2
        )

    # ---------------------------------------
    # Save Processed Image
    # ---------------------------------------

    os.makedirs("outputs", exist_ok=True)

    filename = datetime.now().strftime(
        "capture_%Y%m%d_%H%M%S.jpg"
    )

    filepath = os.path.join(
        "outputs",
        filename
    )

    cv2.imwrite(
        filepath,
        processed
    )

    result = {

        "object": label,

        "shape": shape,

        "width": width,

        "height": height,

        "depth": depth,

        "area": area,

        "volume": volume,

        "confidence": confidence,

        "image": filepath

    }

    # ---------------------------------------
    # Start Frozen 3D Scanner
    # ---------------------------------------

    measurements = {
        "object": label,
        "shape": shape,
        "width": width,
        "height": height,
        "depth": depth,
        "area": area,
        "volume": volume
    }

    if get_current_mode() == "3d":

        start_scan(
            processed,
            (x1, y1, x2, y2),
            contour,
            measurements
        )

    return result