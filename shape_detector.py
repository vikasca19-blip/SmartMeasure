import math
import cv2
import numpy as np
import time


def detect_shape(label, width, height):
    """
    Detect the geometric shape of an object based on YOLO label and dimensions.

    Parameters
    ----------
    label : str
        YOLO detected object label.
    width : float
        Width in centimeters.
    height : float
        Height in centimeters.

    Returns
    -------
    dict
        {
            "shape": "...",
            "depth_ratio": float,
            "formula": "..."
        }
    """

    label = label.lower()

    # --------------------------
    # Bottle
    # --------------------------
    if label == "bottle":

        return {
            "shape": "Cylinder",
            "depth_ratio": 1.0,
            "formula": "cylinder"
        }

    # --------------------------
    # Book
    # --------------------------
    elif label == "book":

        return {
            "shape": "Cuboid",
            "depth_ratio": 0.12,
            "formula": "cuboid"
        }

    # --------------------------
    # Cell Phone
    # --------------------------
    elif label in ["cell phone", "mobile phone"]:

        return {
            "shape": "Cuboid",
            "depth_ratio": 0.08,
            "formula": "cuboid"
        }

    # --------------------------
    # Laptop
    # --------------------------
    elif label == "laptop":

        return {
            "shape": "Cuboid",
            "depth_ratio": 0.05,
            "formula": "cuboid"
        }

    # --------------------------
    # Remote
    # --------------------------
    elif label == "remote":

        return {
            "shape": "Cuboid",
            "depth_ratio": 0.10,
            "formula": "cuboid"
        }

    # --------------------------
    # Mouse
    # --------------------------
    elif label == "mouse":

        return {
            "shape": "Rounded Cuboid",
            "depth_ratio": 0.45,
            "formula": "cuboid"
        }

    # --------------------------
    # Sports Ball
    # --------------------------
    elif label == "sports ball":

        return {
            "shape": "Sphere",
            "depth_ratio": 1.0,
            "formula": "sphere"
        }

    # --------------------------
    # Cup
    # --------------------------
    elif label == "cup":

        return {
            "shape": "Cylinder",
            "depth_ratio": 1.0,
            "formula": "cylinder"
        }

    # --------------------------
    # Can
    # --------------------------
    elif label == "can":

        return {
            "shape": "Cylinder",
            "depth_ratio": 1.0,
            "formula": "cylinder"
        }

    # --------------------------
    # Box
    # --------------------------
    elif label in ["box", "package"]:

        return {
            "shape": "Cuboid",
            "depth_ratio": 0.65,
            "formula": "cuboid"
        }

    # --------------------------
    # Default
    # --------------------------
    return {
        "shape": "Unknown",
        "depth_ratio": 0.50,
        "formula": "cuboid"
    }


def estimate_depth(width, info):
    """
    Estimate object depth using shape depth ratios.

    Parameters
    ----------
    width : float
        Width in centimeters.
    info : dict
        Shape information dictionary from detect_shape.

    Returns
    -------
    float
        Estimated depth in centimeters.
    """

    return round(
        width * info["depth_ratio"],
        2
    )


# =====================================================================
# Wall Height & 3D Spatial Axis System (Click-Triggered)
# =====================================================================

def detect_wall_corner_and_axes(frame, click_x=None, click_y=None, focal_length_px=1500, estimated_distance_mm=2500):
    """
    Projects X, Y, Z spatial axes and calculates wall height ONLY after user clicks a corner point.
    """
    output_frame = frame.copy()
    h, w, _ = frame.shape

    # 1. If user has NOT clicked yet, show instruction prompt and return clean feed
    if click_x is None or click_y is None:
        prompt_text = "Click anywhere on the wall corner to project 3D Axes"

        # Semi-transparent instruction banner at top
        cv2.rectangle(output_frame, (20, 20), (w - 20, 65), (20, 20, 20), -1)
        cv2.rectangle(output_frame, (20, 20), (w - 20, 65), (0, 255, 255), 1)
        cv2.putText(output_frame, prompt_text, (35, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        return output_frame, 0.0

    # 2. Set origin directly from user mouse click
    origin = (int(click_x), int(click_y))
    corner_x = origin[0]
    corner_y_bottom = origin[1]
    corner_y_top = max(10, corner_y_bottom - int(h * 0.7))

    axis_len = 180  # Vector line length in pixels

    # 3. Draw Projected 3D Axis Vectors (RGB = XYZ)
    # Z-Axis (Vertical - Wall Seam) -> Blue Line
    z_end = (origin[0], max(0, origin[1] - axis_len))
    cv2.arrowedLine(output_frame, origin, z_end, (255, 0, 0), 4, tipLength=0.12)
    cv2.putText(output_frame, "Z (Height)", (z_end[0] + 10, z_end[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 0, 0), 2)

    # X-Axis (Left Floor Boundary) -> Red Line
    x_end = (max(0, origin[0] - int(axis_len * 0.86)), min(h, origin[1] + int(axis_len * 0.5)))
    cv2.arrowedLine(output_frame, origin, x_end, (0, 0, 255), 4, tipLength=0.12)
    cv2.putText(output_frame, "X (Left)", (x_end[0] - 80, x_end[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # Y-Axis (Right Floor Boundary) -> Green Line
    y_end = (min(w, origin[0] + int(axis_len * 0.86)), min(h, origin[1] + int(axis_len * 0.5)))
    cv2.arrowedLine(output_frame, origin, y_end, (0, 255, 0), 4, tipLength=0.12)
    cv2.putText(output_frame, "Y (Right)", (y_end[0] + 10, y_end[1]),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Highlight origin vertex
    cv2.circle(output_frame, origin, 7, (0, 255, 255), -1)

    # 4. Height Calculation Along Z-Axis
    pixel_height = corner_y_bottom - corner_y_top
    wall_height_mm = (pixel_height * estimated_distance_mm) / focal_length_px
    wall_height_meters = wall_height_mm / 1000.0

    # Vertical Seam Guide Line
    cv2.line(output_frame, (corner_x, corner_y_top), (corner_x, corner_y_bottom), (0, 255, 255), 2)

    # HUD Metric Display Box
    label_text = f"Wall Height: {wall_height_meters:.2f} m ({wall_height_mm:.0f} mm)"
    cv2.rectangle(output_frame, (corner_x + 15, corner_y_top + 15),
                  (corner_x + 380, corner_y_top + 60), (20, 20, 20), -1)
    cv2.rectangle(output_frame, (corner_x + 15, corner_y_top + 15),
                  (corner_x + 380, corner_y_top + 60), (0, 255, 255), 1)
    cv2.putText(output_frame, label_text, (corner_x + 25, corner_y_top + 45),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 255), 2)

    return output_frame, wall_height_meters


# =====================================================================
# Laser-Scan Cyan Mesh Wireframe
# =====================================================================

def draw_laser_cyan_mesh(frame, x1, y1, x2, y2):
    """
    Draws a dynamic futuristic cyan wireframe mesh grid 
    and animated laser scan line across the detected object bounding box.
    """
    overlay = frame.copy()
    
    # 1. Bounding Box & Grid Setup
    color_cyan = (255, 255, 0) # BGR Cyan
    grid_spacing = 15
    
    # Draw internal horizontal and vertical gridlines across object ROI
    for x in range(x1, x2, grid_spacing):
        cv2.line(overlay, (x, y1), (x, y2), color_cyan, 1)
        
    for y in range(y1, y2, grid_spacing):
        cv2.line(overlay, (x1, y), (x2, y), color_cyan, 1)

    # 2. Animated Laser Sweep Line
    box_height = max(1, y2 - y1)
    sweep_speed = 3.0 # sweeps per second
    progress = (math.sin(time.time() * sweep_speed * math.pi) + 1) / 2.0
    laser_y = int(y1 + progress * box_height)
    print(laser_y)
    
    # Glowing laser beam
    cv2.line(overlay, (x1, laser_y), (x2, laser_y), (255, 255, 255), 3)
    cv2.line(overlay, (x1, laser_y), (x2, laser_y), (255, 255, 0), 6)

    # Blend overlay with transparent glow effect
    alpha = 0.35
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    # 3. Outer Glowing Corner Laser Box
    corner_len = 15
    # Top-Left
    cv2.line(frame, (x1, y1), (x1 + corner_len, y1), color_cyan, 2)
    cv2.line(frame, (x1, y1), (x1, y1 + corner_len), color_cyan, 2)
    # Top-Right
    cv2.line(frame, (x2, y1), (x2 - corner_len, y1), color_cyan, 2)
    cv2.line(frame, (x2, y1), (x2, y1 + corner_len), color_cyan, 2)
    # Bottom-Left
    cv2.line(frame, (x1, y2), (x1 + corner_len, y2), color_cyan, 2)
    cv2.line(frame, (x1, y2), (x1, y2 - corner_len), color_cyan, 2)
    # Bottom-Right
    cv2.line(frame, (x2, y2), (x2 - corner_len, y2), color_cyan, 2)
    cv2.line(frame, (x2, y2), (x2, y2 - corner_len), color_cyan, 2)

    return frame