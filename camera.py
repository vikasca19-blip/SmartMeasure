import cv2
import math
from ultralytics import YOLO
import os
from datetime import datetime

from vision.measurement import (
    detect_a4,
    get_pixels_per_cm,
    pixels_to_cm
)

from vision.shape_detector import (
    detect_shape,
    estimate_depth,
    draw_laser_cyan_mesh
)

from vision.volume import (
    calculate_volume
)

from vision.segmentation import extract_object

# ---------------------------------------
# Load YOLO & Settings
# ---------------------------------------

model = YOLO("yolov8n.pt")

camera = None
latest_frame = None
latest_detection = None
frame_counter = 0
last_results = None

three_d_mode = False

current_mode = "ai"

current_pixels_per_cm = None

# ==========================================
# Locked 2D A4 Calibration
# ==========================================

calibrated_pixels_per_cm = None

# =====================================
# 2D Calibration State
# =====================================

is_calibrated = False

stored_pixels_per_cm = None

# Global Camera & Performance Settings
camera_settings = {
    "preset": "fast",
    "ai_fps_skip": 1,
    "jpeg_quality": 65,
    "enable_mesh": True,
    "enable_glow": True
}

latest_measurement = {
    "object": "Waiting...",
    "shape": "--",
    "width": "--",
    "height": "--",
    "depth": "--",
    "area": "--",
    "volume": "--",
    "confidence": "--",
    "quality": "Waiting...",
    "warning": ""
}

# ==========================================
# Frozen Scan State
# ==========================================

scan_mode = False

frozen_frame = None
frozen_bbox = None
frozen_contour = None

scan_measurements = {}


def stop_scan():

    global scan_mode
    global frozen_frame
    global frozen_bbox
    global frozen_contour
    global scan_measurements

    scan_mode = False
    frozen_frame = None
    frozen_bbox = None
    frozen_contour = None
    scan_measurements = {}

# ---------------------------------------
# Camera & Settings Management
# ---------------------------------------

def start_camera(index=1):

    global camera

    if camera is None:
        camera = cv2.VideoCapture(index)

    return camera


def get_latest_measurement():
    return latest_measurement

def get_latest_detection():
    global latest_detection
    return latest_detection


def get_latest_frame():
    global latest_frame
    return latest_frame


def get_pixels_scale():
    global current_pixels_per_cm
    return current_pixels_per_cm


def get_calibrated_pixels_scale():
    global calibrated_pixels_per_cm
    return calibrated_pixels_per_cm


def calibrate_a4_scale():
    """
    Lock the currently detected A4 scale for 2D measurements.
    Returns the pixels-per-cm value if A4 is currently detected.
    """

    global calibrated_pixels_per_cm
    global current_pixels_per_cm

    if current_pixels_per_cm is None:
        return None

    calibrated_pixels_per_cm = current_pixels_per_cm

    return calibrated_pixels_per_cm


def clear_a4_calibration():
    """
    Clear the locked 2D A4 calibration.
    """

    global calibrated_pixels_per_cm

    calibrated_pixels_per_cm = None


def is_a4_calibrated():
    global calibrated_pixels_per_cm

    return calibrated_pixels_per_cm is not None

# =====================================
# 2D Calibration Helpers
# =====================================

def set_calibration(scale):

    global stored_pixels_per_cm
    global is_calibrated
    global current_pixels_per_cm

    stored_pixels_per_cm = scale
    current_pixels_per_cm = scale
    is_calibrated = True


def clear_calibration():

    global stored_pixels_per_cm
    global is_calibrated
    global current_pixels_per_cm

    stored_pixels_per_cm = None
    current_pixels_per_cm = None
    is_calibrated = False


def get_calibration():

    return stored_pixels_per_cm


def calibration_ready():

    return is_calibrated

def set_current_mode(mode):
    global current_mode
    current_mode = mode

def get_current_mode():
    global current_mode
    return current_mode

    
def save_current_frame():

    global latest_frame

    if latest_frame is None:
        return None

    os.makedirs("outputs", exist_ok=True)

    filename = datetime.now().strftime(
        "measurement_%Y%m%d_%H%M%S.jpg"
    )

    filepath = os.path.join("outputs", filename)

    cv2.imwrite(filepath, latest_frame)

    return filename

def analyze_capture():

    global latest_frame
    global current_pixels_per_cm

    if latest_frame is None:
        return None

    frame = latest_frame.copy()

    # ---------------------------------------
    # Resize for YOLO
    # ---------------------------------------

    small_frame = cv2.resize(frame, (640, 360))

    results = model(
        small_frame,
        verbose=False
    )

    return {
        "frame": frame,
        "results": results
    }


def set_three_d_mode(enabled):

    global three_d_mode
    three_d_mode = enabled


def get_three_d_mode():
    return three_d_mode


def update_camera_settings(new_settings):
    """Updates runtime performance and visual overlay settings."""
    global camera_settings
    camera_settings.update(new_settings)


def get_camera_settings():
    return camera_settings


def get_raw_frame():
    """Safely retrieves raw NumPy frame array from camera without drawing overlays."""
    global camera, latest_frame

    if camera is None:
        return None

    success, frame = camera.read()

    if not success or frame is None:
        return None

    latest_frame = frame.copy()
    return frame


# ---------------------------------------
# Point-to-Point Distance
# ---------------------------------------

def calculate_distance_cm(x1, y1, x2, y2):

    global calibrated_pixels_per_cm

    # 2D measurement requires A4 calibration
    if calibrated_pixels_per_cm is None:
        return None

    pixel_distance = math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )

    distance_cm = (
        pixel_distance /
        calibrated_pixels_per_cm
    )

    return round(distance_cm, 2)

# ---------------------------------------
# Simple Volume Estimation
# ---------------------------------------

def estimate_volume(label, width, height):

    label = label.lower()

    # Cylinder
    if label in [
        "bottle",
        "cup",
        "can",
        "vase"
    ]:

        radius = width / 2

        volume = math.pi * radius * radius * height

        return "Cylinder", round(volume, 2)

    # Cube
    elif label in [
        "book",
        "box",
        "laptop"
    ]:

        depth = width

        volume = width * height * depth

        return "Cuboid", round(volume, 2)

    # Sphere
    elif label in [
        "sports ball",
        "orange",
        "apple"
    ]:

        radius = width / 2

        volume = (4 / 3) * math.pi * radius ** 3

        return "Sphere", round(volume, 2)

    else:

        return "Unknown", None


# ---------------------------------------
# HUD Drawing Utilities
# ---------------------------------------

def draw_laser_box(frame, x1, y1, x2, y2,
                   color=(255, 180, 0),
                   thickness=2):

    corner = 22

    # Top Left
    cv2.line(frame, (x1, y1), (x1 + corner, y1), color, thickness)
    cv2.line(frame, (x1, y1), (x1, y1 + corner), color, thickness)

    # Top Right
    cv2.line(frame, (x2, y1), (x2 - corner, y1), color, thickness)
    cv2.line(frame, (x2, y1), (x2, y1 + corner), color, thickness)

    # Bottom Left
    cv2.line(frame, (x1, y2), (x1 + corner, y2), color, thickness)
    cv2.line(frame, (x1, y2), (x1, y2 - corner), color, thickness)

    # Bottom Right
    cv2.line(frame, (x2, y2), (x2 - corner, y2), color, thickness)
    cv2.line(frame, (x2, y2), (x2, y2 - corner), color, thickness)


def draw_label(frame, text, x, y):

    (w, h), _ = cv2.getTextSize(
        text,
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        2
    )

    cv2.rectangle(
        frame,
        (x, y-h-8),
        (x+w+10, y+5),
        (40,40,40),
        -1
    )

    cv2.putText(
        frame,
        text,
        (x+5, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0,255,255),
        2
    )


def draw_glowing_contour(frame, contour):

    if contour is None:
        return

    # Check user setting for contour glow
    if camera_settings.get("enable_glow", True):
        overlay = frame.copy()
        glow_color = (255, 180, 0)

        # Draw contour on overlay
        cv2.drawContours(overlay, [contour], -1, glow_color, 8)

        # Fast Gaussian bloom (15x15 kernel for high FPS)
        overlay = cv2.GaussianBlur(overlay, (15, 15), 0)

        # Blend glow
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

    # Bright contour
    cv2.drawContours(frame, [contour], -1, (255, 255, 255), 2)
    cv2.drawContours(frame, [contour], -1, (255, 220, 0), 2)


# ---------------------------------------
# Main Camera
# ---------------------------------------

def get_frame():

    global camera
    global latest_frame
    global current_pixels_per_cm
    global frame_counter
    global last_results
    global latest_detection

    if camera is None:
        return None

    success, frame = camera.read()

    if not success:
        return None

    latest_frame = frame.copy()
    h_orig, w_orig = frame.shape[:2]

    # =====================================
    # Frozen 3D Scanner
    # =====================================

    global scan_mode
    global frozen_frame
    global frozen_bbox

    if (
        scan_mode
        and current_mode == "3d"
        and frozen_frame is not None
    ):

        frame = frozen_frame.copy()

        x1, y1, x2, y2 = frozen_bbox

        draw_laser_cyan_mesh(
             frame,
            x1,
            y1,
            x2,
            y2
        )

        cv2.putText(
            frame,
            "3D LASER SCANNING...",
            (25,45),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255,255,0),
            2
        )

        quality = camera_settings.get("jpeg_quality",75)

        _, buffer = cv2.imencode(
            ".jpg",
            frame,
            [int(cv2.IMWRITE_JPEG_QUALITY), quality]
        )

        return buffer.tobytes()


    # ---------------------------------------
    # Draw XYZ Axes
    # ---------------------------------------

    if three_d_mode:

        origin = (100, frame.shape[0] - 100)

        cv2.circle(
            frame,
            origin,
            6,
            (255, 255, 255),
            -1
        )

        # X

        cv2.arrowedLine(
            frame,
            origin,
            (200, frame.shape[0] - 100),
            (0, 0, 255),
            4,
            tipLength=0.2
        )

        cv2.putText(
            frame,
            "X",
            (210, frame.shape[0] - 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        # Y

        cv2.arrowedLine(
            frame,
            origin,
            (100, frame.shape[0] - 200),
            (0, 255, 0),
            4,
            tipLength=0.2
        )

        cv2.putText(
            frame,
            "Y",
            (80, frame.shape[0] - 215),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        # Z

        cv2.arrowedLine(
            frame,
            origin,
            (40, frame.shape[0] - 40),
            (255, 120, 0),
            4,
            tipLength=0.2
        )

        cv2.putText(
            frame,
            "Z",
            (15, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 120, 0),
            2
        )

        cv2.rectangle(
            frame,
            (15, 10),
            (180, 45),
            (40, 40, 40),
            -1
        )

        cv2.putText(
            frame,
            "3D ACTIVE",
            (25, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 255, 255),
            2
        )

    # ---------------------------------------
    # Detect A4
    # ---------------------------------------

    pixels_per_cm = None

    paper = detect_a4(frame)

    # Default: no warning
    latest_measurement["warning"] = ""

    if (
        paper is not None
        and len(paper) >= 4
    ):

        cv2.drawContours(frame, [paper], -1, (255, 0, 0), 3)

        try:
            pixels_per_cm = get_pixels_per_cm(paper)

            current_pixels_per_cm = pixels_per_cm

            latest_measurement["warning"] = ""

        except Exception:

            pixels_per_cm = None

            latest_measurement["warning"] = (
                "⚠ Unable to calculate A4 scale."
            )

    else:

        pixels_per_cm = None

        latest_measurement["warning"] = (
            "⚠ A4 reference not detected. Measurements are shown in pixels."
        )

        
    # ---------------------------------------
    # Fast Fast-Inference YOLO Detection
    # ---------------------------------------

    small_frame = cv2.resize(frame, (640, 360))
    scale_x = w_orig / 640.0
    scale_y = h_orig / 360.0

    frame_counter += 1

    if frame_counter % 3 == 0 or last_results is None:

        last_results = model(
            small_frame,
            verbose=False
        )

    results = last_results

    for result in results:

        for box in result.boxes:

            sx1, sy1, sx2, sy2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])

            # Upscale bounding box back to full frame resolution
            x1, x2 = int(sx1 * scale_x), int(sx2 * scale_x)
            y1, y2 = int(sy1 * scale_y), int(sy2 * scale_y)

            # ----------------------------
            # Measurement Quality
            # ----------------------------

            if confidence >= 0.90:
                quality = "🟢 Excellent"

            elif confidence >= 0.75:
                quality = "🟡 Good"

            else:
                quality = "🔴 Low"

            label = model.names[int(box.cls[0])]

            latest_detection = {

                "label": label,

                "confidence": confidence,

                "bbox": (
                    x1,
                    y1,
                    x2,
                    y2
                ),

                "pixels_per_cm": pixels_per_cm

            }

            contour = None
            

            # Default object size from YOLO bounding box
            object_width = x2 - x1
            object_height = y2 - y1

            # Convert contour from ROI coordinates to full-frame coordinates
            if contour is not None:

                contour = contour.copy()
                contour[:, :, 0] += x1
                contour[:, :, 1] += y1

                # Use contour size if available
                _, _, w, h = cv2.boundingRect(contour)

                object_width = w
                object_height = h

            # ----------------------------
            # Defaults (prevents UnboundLocalError)
            # ----------------------------

            shape = "--"
            depth = None
            volume = None

            width_text = f"W : {object_width}px"
            height_text = f"H : {object_height}px"

            depth_text = None
            area_text = None
            volume_text = None

            # ----------------------------
            # Real Measurements
            # ----------------------------

            if pixels_per_cm is not None:

                width = pixels_to_cm(
                    object_width,
                    pixels_per_cm
                )

                height = pixels_to_cm(
                    object_height,
                    pixels_per_cm
                )

                area = round(width * height, 2)

                width_text = f"W : {width:.2f} cm"
                height_text = f"H : {height:.2f} cm"
                area_text = f"Area : {area:.2f} cm²"

                if three_d_mode:

                    shape_info = detect_shape(
                        label,
                        width,
                        height
                    )

                    shape = shape_info["shape"]

                    # Estimate depth
                    depth = estimate_depth(
                        width,
                        shape_info
                    )

                    # Calculate volume
                    volume = calculate_volume(
                        shape,
                        width,
                        height,
                        depth
                    )

                    depth_text = f"Depth : {depth:.2f} cm"

                    if volume is not None:
                        volume_text = f"Vol : {volume:.2f} cm³"

                latest_measurement["object"] = label
                latest_measurement["shape"] = shape
                latest_measurement["width"] = f"{width:.2f} cm"
                latest_measurement["height"] = f"{height:.2f} cm"
                latest_measurement["area"] = f"{area:.2f} cm²"
                latest_measurement["confidence"] = f"{confidence*100:.1f}%"

                if volume is not None:
                    latest_measurement["volume"] = f"{volume:.2f} cm³"
                else:
                    latest_measurement["volume"] = "--"

            else:

                latest_measurement["object"] = label
                latest_measurement["shape"] = "--"
                latest_measurement["width"] = f"{object_width}px"
                latest_measurement["height"] = f"{object_height}px"
                latest_measurement["area"] = "--"
                latest_measurement["volume"] = "--"
                latest_measurement["confidence"] = f"{confidence*100:.1f}%"

            # ----------------------------
            # Draw Bounding Box & Cyan Mesh
            # ----------------------------

            # Mesh will be drawn only after Capture
            pass

            pass

            draw_label(
                frame,
                f"{label.upper()}  {confidence*100:.1f}%",
                x1,
                y1 - 5
            )

            cv2.putText(
                frame,
                width_text,
                (x1, y2 + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

            cv2.putText(
                frame,
                height_text,
                (x1, y2 + 45),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

            if area_text is not None:

                cv2.putText(
                    frame,
                    area_text,
                    (x1, y2 + 70),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 255, 255),
                    2
                )

            if volume_text is not None:

                cv2.putText(
                    frame,
                    volume_text,
                    (x1, y2 + 95),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 100, 255),
                    2
                )

            if three_d_mode:

                cv2.putText(
                    frame,
                    f"Shape : {shape}",
                    (x1, y2 + 120),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 180, 255),
                    2
                )

    quality = camera_settings.get("jpeg_quality", 75)
    _, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])

    return buffer.tobytes()

def start_scan(frame, bbox, contour, measurements):
    global scan_mode
    global frozen_frame
    global frozen_bbox
    global frozen_contour
    global scan_measurements

    scan_mode = True

    frozen_frame = frame.copy()
    frozen_bbox = bbox
    frozen_contour = contour
    scan_measurements = measurements


def stop_scan():
    global scan_mode

    scan_mode = False


def is_scan_mode():
    return scan_mode