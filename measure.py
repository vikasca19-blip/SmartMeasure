import cv2
import os
import json
import math
import numpy as np
from datetime import datetime
from flask import send_from_directory
from flask import (
    render_template,
    Response,
    jsonify,
    request
)

from vision.report import generate_report
from vision.shape_detector import detect_wall_corner_and_axes
from vision.capture_analyzer import analyze_capture
from vision.measurement import (
    detect_a4,
    get_pixels_per_cm
)
from vision.camera import (
    start_camera,
    get_frame,
    get_raw_frame,
    get_latest_measurement,
    get_latest_detection,
    get_latest_frame,
    get_pixels_scale,
    set_three_d_mode,
    set_current_mode,
    save_current_frame,
    calculate_distance_cm,
    stop_scan,
    update_camera_settings,
    get_camera_settings,
    calibrate_a4_scale,
    clear_a4_calibration,
    is_a4_calibrated
)

# Global dictionary to store user-clicked wall corner position
wall_corner_click = {"x": None, "y": None}


def register_measure_routes(app):


    @app.route("/reset_scan", methods=["POST"])
    def reset_scan():

        stop_scan()

        return jsonify({
            "success": True
        })

    # ---------------------------------------
    # Main Measurement Page Route
    # ---------------------------------------
    @app.route("/measure")
    def measure():
        global wall_corner_click
        mode = request.args.get("mode", "ai")

        # Reset wall click origin when opening page or switching modes
        wall_corner_click = {"x": None, "y": None}

        set_current_mode(mode)

        return render_template(
            "measure.html",
            mode=mode
        )

    @app.route("/capture_image/<filename>")
    def capture_image(filename):

        return send_from_directory(
            "outputs",
            filename
        )
    
    # ---------------------------------------
    # Settings Page Route
    # ---------------------------------------
    @app.route("/settings")
    def settings_page():
        return render_template("settings.html")

    # ---------------------------------------
    # Processed Camera Stream Feed
    # ---------------------------------------
    @app.route("/video_feed")
    def video_feed():

        start_camera(1)

        def generate():

            while True:

                frame = get_frame()

                if frame is None:
                    continue

                yield (
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n'
                    + frame +
                    b'\r\n'
                )

        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )

# ---------------------------------------
# Lock A4 Calibration for 2D Measurement
# ---------------------------------------
    @app.route("/calibrate_a4", methods=["POST"])
    def calibrate_a4():

        # Make sure the camera is running
        start_camera(1)

        scale = calibrate_a4_scale()

        if scale is None:

            return jsonify({
                "success": False,
                "message": "A4 sheet not detected. Place the A4 sheet clearly in view."
            })

        return jsonify({
            "success": True,
            "pixels_per_cm": round(scale, 2),
            "message": "A4 calibration locked successfully."
        })


# ---------------------------------------
# Clear A4 Calibration
# ---------------------------------------
    @app.route("/clear_calibration", methods=["POST"])
    def clear_calibration():

        clear_a4_calibration()

        return jsonify({
            "success": True,
            "message": "A4 calibration cleared."
        })


    # ---------------------------------------
    # Set Wall Corner Position via Mouse Click
    # ---------------------------------------
    @app.route("/set_wall_corner", methods=["POST"])
    def set_wall_corner():
        global wall_corner_click
        data = request.get_json()
        wall_corner_click["x"] = data.get("x")
        wall_corner_click["y"] = data.get("y")
        return jsonify({"success": True})

    # ---------------------------------------
    # Wall Height & 3D Axis Video Stream Feed
    # ---------------------------------------
    @app.route("/wall_feed")
    def wall_feed():

        start_camera(1)

        def generate():
            while True:
                raw_frame = get_raw_frame()

                if raw_frame is None:
                    continue

                try:

                    annotated_img, wall_height = detect_wall_corner_and_axes(
                        raw_frame,
                        click_x=wall_corner_click["x"],
                        click_y=wall_corner_click["y"]
                    )

                    ret, jpeg = cv2.imencode('.jpg', annotated_img, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                    if not ret:
                        continue

                    yield (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n'
                        + jpeg.tobytes() +
                        b'\r\n'
                    )
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    continue

        return Response(
            generate(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    # ---------------------------------------
    # Capture & Save Measurement Data
    # ---------------------------------------
    @app.route("/capture", methods=["POST"])
    def capture():

        frame = get_latest_frame()

        detection = get_latest_detection()

        pixels_per_cm = get_pixels_scale()

        if frame is None:

            return jsonify({
                "success": False,
                "message": "No camera frame available."
            })

        if detection is None:

           return jsonify({
                "success": False,
                "message": "No object detected."
            })

        result = analyze_capture(

            frame,

            detection["label"],

            detection["confidence"],

            detection["bbox"],

            pixels_per_cm

        )

        history_file = "outputs/history.json"

        if os.path.exists(history_file):

            with open(history_file, "r") as f:
                history = json.load(f)

        else:

            history = []

        data = {

            "success": True,

            "object": result["object"],

            "shape": result["shape"],

            "width": f'{result["width"]:.2f} cm',

            "height": f'{result["height"]:.2f} cm',

            "depth": f'{result["depth"]:.2f} cm',

            "area": f'{result["area"]:.2f} cm²',

            "volume": "--" if result["volume"] is None else f'{result["volume"]:.2f} cm³',

            "confidence": f'{result["confidence"]*100:.1f}%',

            "image": result["image"],

            "time": datetime.now().strftime("%d-%m-%Y %H:%M:%S")

        }

        history.insert(0, data)

        with open(history_file, "w") as f:

            json.dump(history, f, indent=4)

        return jsonify(data)

    # ---------------------------------------
    # Toggle 3D Mode
    # ---------------------------------------
    @app.route("/toggle3d", methods=["POST"])
    def toggle3d():

        data = request.get_json()

        enabled = data.get("enabled", False)

        set_three_d_mode(enabled)

        return jsonify({
            "success": True
        })

    # ---------------------------------------
    # Calculate Point-to-Point Distance
    # ---------------------------------------
    @app.route("/calculate_distance", methods=["POST"])
    def calculate_distance():

        data = request.get_json()

        x1 = int(data["x1"])
        y1 = int(data["y1"])
        x2 = int(data["x2"])
        y2 = int(data["y2"])

        ref_mode = data.get("ref_mode", "a4")

        if ref_mode == "a4":
            distance = calculate_distance_cm(
                x1,
                y1,
                x2,
                y2
            )

            if distance is None:

                return jsonify({
                    "success": False,
                    "message": "A4 calibration required."
                })
        else:
            pixel_distance = math.hypot(x2 - x1, y2 - y1)
            cm_per_pixel = 0.05 
            distance = round(pixel_distance * cm_per_pixel, 2)

        return jsonify({
            "success": True,
            "distance": distance
        })

    # ---------------------------------------
    # Settings API (Fetch & Save User Settings)
    # ---------------------------------------
    @app.route("/api/settings", methods=["GET", "POST"])
    def settings_api():
        if request.method == "POST":
            data = request.get_json()
            updated = {
                "preset": data.get("preset", "fast"),
                "jpeg_quality": int(data.get("jpeg_quality", 70)),
                "enable_mesh": bool(data.get("enable_mesh", True)),
                "enable_glow": bool(data.get("enable_glow", True))
            }
            update_camera_settings(updated)
            return jsonify({"success": True, "settings": get_camera_settings()})

        return jsonify(get_camera_settings())