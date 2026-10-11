/* =========================================================
   A4 CALIBRATION
========================================================= */

async function calibrateA4() {

    const status = document.getElementById("calibrationStatus");

    if (status) {
        status.innerText = "⏳ Calibrating A4...";
    }

    try {

        const response = await fetch("/calibrate_a4", {
            method: "POST"
        });

        const data = await response.json();

        if (data.success) {

            if (status) {
                status.innerText =
                    "✅ A4 Calibrated — " +
                    data.pixels_per_cm +
                    " px/cm";
            }

            console.log(
                "A4 calibration successful:",
                data.pixels_per_cm,
                "px/cm"
            );

        } else {

            if (status) {
                status.innerText =
                    "❌ " +
                    (data.message || "A4 calibration failed.");
            }

            console.warn(
                "A4 calibration failed:",
                data.message
            );
        }

    } catch (error) {

        console.error("Calibration request failed:", error);

        if (status) {
            status.innerText =
                "❌ Calibration request failed.";
        }
    }
}


/* =========================================================
   CLEAR / RECALIBRATE A4
========================================================= */

async function clearCalibration() {

    const status = document.getElementById("calibrationStatus");

    try {

        const response = await fetch("/clear_calibration", {
            method: "POST"
        });

        const data = await response.json();

        if (data.success) {

            if (status) {
                status.innerText = "❌ Not Calibrated";
            }

            console.log("A4 calibration cleared.");

            // Reset point-to-point measurement
            resetPointMeasurement();

        } else {

            if (status) {
                status.innerText =
                    "❌ Unable to clear calibration.";
            }
        }

    } catch (error) {

        console.error(
            "Clear calibration request failed:",
            error
        );
    }
}


/* =========================================================
   CAPTURE MEASUREMENT
========================================================= */

async function captureMeasurement() {

    try {

        const response = await fetch("/capture", {
            method: "POST"
        });

        const data = await response.json();

        if (!data.success) {

            console.warn(
                "Capture failed:",
                data.message
            );

            return;
        }

        const cam = document.getElementById("cameraFeed");

        if (cam) {
            cam.src = "/video_feed?" + Date.now();
        }

        const objName = document.getElementById("objName");
        const objWidth = document.getElementById("objWidth");
        const objHeight = document.getElementById("objHeight");
        const objArea = document.getElementById("objArea");
        const objConfidence =
            document.getElementById("objConfidence");

        if (objName) {
            objName.innerText = data.object || "--";
        }

        if (objWidth) {
            objWidth.innerText = data.width || "--";
        }

        if (objHeight) {
            objHeight.innerText = data.height || "--";
        }

        if (objArea) {
            objArea.innerText = data.area || "--";
        }

        if (objConfidence) {
            objConfidence.innerText =
                data.confidence || "--";
        }


        /* Warning */

        const warningBox =
            document.getElementById("warningBox");

        if (warningBox) {

            if (data.warning) {

                warningBox.style.display = "block";
                warningBox.innerText = data.warning;

            } else {

                warningBox.style.display = "none";
            }
        }


        /* Shape */

        const shape =
            document.getElementById("objShape");

        if (shape) {
            shape.innerText = data.shape || "--";
        }


        /* Volume */

        const volume =
            document.getElementById("objVolume");

        if (volume) {
            volume.innerText = data.volume || "--";
        }


        /* History */

        const table =
            document.getElementById("historyTable");

        if (table) {

            const row = table.insertRow(0);

            const now = new Date();

            const time =
                now.toLocaleDateString() +
                " " +
                now.toLocaleTimeString();

            row.insertCell(0).innerText = time;
            row.insertCell(1).innerText =
                data.object || "--";
            row.insertCell(2).innerText =
                data.width || "--";
            row.insertCell(3).innerText =
                data.height || "--";
            row.insertCell(4).innerText =
                data.area || "--";
            row.insertCell(5).innerText =
                data.volume || "--";
            row.insertCell(6).innerText =
                data.confidence || "--";
        }

    } catch (error) {

        console.error(
            "Capture request failed:",
            error
        );
    }
}


/* =========================================================
   RESET MEASUREMENT
========================================================= */

async function resetMeasurement() {

    try {

        await fetch("/reset_scan", {
            method: "POST"
        });

    } catch (error) {

        console.error(
            "Reset scan request failed:",
            error
        );
    }


    const objName =
        document.getElementById("objName");

    const objWidth =
        document.getElementById("objWidth");

    const objHeight =
        document.getElementById("objHeight");

    const objArea =
        document.getElementById("objArea");

    const objConfidence =
        document.getElementById("objConfidence");


    if (objName) {
        objName.innerText = "Waiting...";
    }

    if (objWidth) {
        objWidth.innerText = "--";
    }

    if (objHeight) {
        objHeight.innerText = "--";
    }

    if (objArea) {
        objArea.innerText = "--";
    }

    if (objConfidence) {
        objConfidence.innerText = "--";
    }


    const shape =
        document.getElementById("objShape");

    if (shape) {
        shape.innerText = "--";
    }


    const volume =
        document.getElementById("objVolume");

    if (volume) {
        volume.innerText = "--";
    }


    const table =
        document.getElementById("historyTable");

    if (table) {
        table.innerHTML = "";
    }


    resetPointMeasurement();


    /* Restart live camera */

    const cam =
        document.getElementById("cameraFeed");

    if (cam) {

        const params =
            new URLSearchParams(
                window.location.search
            );

        const mode =
            params.get("mode");

        if (mode === "wall") {

            cam.src =
                "/wall_feed?" +
                Date.now();

        } else {

            cam.src =
                "/video_feed?" +
                Date.now();
        }
    }
}


/* =========================================================
   3D TOGGLE
========================================================= */

const toggle =
    document.getElementById("threeDMode");

const volumeSection =
    document.getElementById("volumeSection");

const badge =
    document.getElementById("modeBadge");


if (toggle) {

    toggle.addEventListener(
        "change",
        async function () {

            try {

                await fetch("/toggle3d", {

                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        enabled: this.checked
                    })
                });

            } catch (error) {

                console.error(
                    "3D toggle failed:",
                    error
                );

                return;
            }


            if (volumeSection) {

                volumeSection.style.display =
                    this.checked
                        ? "block"
                        : "none";
            }


            if (badge) {

                badge.style.display =
                    this.checked
                        ? "block"
                        : "none";
            }


            const cam =
                document.getElementById(
                    "cameraFeed"
                );

            if (cam) {

                cam.src =
                    "/video_feed?" +
                    Date.now();
            }
        }
    );
}


/* =========================================================
   POINT-TO-POINT MEASUREMENT
========================================================= */

let startPoint = null;
let endPoint = null;

const img =
    document.getElementById("cameraFeed");

const line =
    document.getElementById("measureLine");


/* ---------------------------------------------------------
   Reset point measurement
--------------------------------------------------------- */

function resetPointMeasurement() {

    startPoint = null;
    endPoint = null;


    const p1 =
        document.getElementById("point1");

    const p2 =
        document.getElementById("point2");


    if (p1) {
        p1.style.display = "none";
    }

    if (p2) {
        p2.style.display = "none";
    }

    if (line) {
        line.style.display = "none";
    }
}


/* ---------------------------------------------------------
   Camera click
--------------------------------------------------------- */

if (img) {

    img.addEventListener(
        "click",
        async function (e) {

            const params =
                new URLSearchParams(
                    window.location.search
                );

            const currentMode =
                params.get("mode");


            /* Wall mode */

            if (currentMode === "wall") {

                const rect =
                    img.getBoundingClientRect();

                const displayX =
                    e.clientX - rect.left;

                const displayY =
                    e.clientY - rect.top;

                const actualWidth =
                    img.naturalWidth ||
                    rect.width;

                const actualHeight =
                    img.naturalHeight ||
                    rect.height;


                const x =
                    Math.round(
                        displayX *
                        actualWidth /
                        rect.width
                    );

                const y =
                    Math.round(
                        displayY *
                        actualHeight /
                        rect.height
                    );


                try {

                    await fetch(
                        "/set_wall_corner",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                x: x,
                                y: y
                            })
                        }
                    );

                    console.log(
                        "Wall corner locked:",
                        x,
                        y
                    );

                } catch (error) {

                    console.error(
                        "Wall corner request failed:",
                        error
                    );
                }

                return;
            }


            /* Point-to-point only in 2D */

            if (currentMode !== "2d") {
                return;
            }


            const rect =
                img.getBoundingClientRect();

            const displayX =
                e.clientX - rect.left;

            const displayY =
                e.clientY - rect.top;


            const displayWidth =
                rect.width;

            const displayHeight =
                rect.height;


            const actualWidth =
                img.naturalWidth ||
                displayWidth;

            const actualHeight =
                img.naturalHeight ||
                displayHeight;


            /*
             Convert displayed coordinates
             back to actual camera coordinates.
            */

            const x =
                Math.round(
                    displayX *
                    actualWidth /
                    displayWidth
                );

            const y =
                Math.round(
                    displayY *
                    actualHeight /
                    displayHeight
                );


            /* =========================================
               FIRST POINT
            ========================================= */

            if (startPoint === null) {

                startPoint = {
                    x: x,
                    y: y
                };


                const p1 =
                    document.getElementById(
                        "point1"
                    );

                if (p1) {

                    p1.style.display = "block";

                    p1.style.left =
                        (displayX - 7) +
                        "px";

                    p1.style.top =
                        (displayY - 7) +
                        "px";
                }


                const p2 =
                    document.getElementById(
                        "point2"
                    );

                if (p2) {
                    p2.style.display = "none";
                }


                if (line) {
                    line.style.display = "none";
                }


                console.log(
                    "Point 1:",
                    startPoint
                );

                return;
            }


            /* =========================================
               SECOND POINT
            ========================================= */

            if (endPoint === null) {

                endPoint = {
                    x: x,
                    y: y
                };


                const p2 =
                    document.getElementById(
                        "point2"
                    );

                if (p2) {

                    p2.style.display = "block";

                    p2.style.left =
                        (displayX - 7) +
                        "px";

                    p2.style.top =
                        (displayY - 7) +
                        "px";
                }


                /* Draw measurement line */

                if (line) {

                    const startDisplayX =
                        startPoint.x *
                        displayWidth /
                        actualWidth;

                    const startDisplayY =
                        startPoint.y *
                        displayHeight /
                        actualHeight;


                    const dx =
                        displayX -
                        startDisplayX;

                    const dy =
                        displayY -
                        startDisplayY;


                    const length =
                        Math.sqrt(
                            dx * dx +
                            dy * dy
                        );


                    const angle =
                        Math.atan2(
                            dy,
                            dx
                        ) *
                        180 /
                        Math.PI;


                    line.style.display =
                        "block";

                    line.style.left =
                        startDisplayX +
                        "px";

                    line.style.top =
                        startDisplayY +
                        "px";

                    line.style.width =
                        length +
                        "px";

                    line.style.transform =
                        "rotate(" +
                        angle +
                        "deg)";
                }


                /* =====================================
                   SEND TO BACKEND
                ===================================== */

                try {

                    const response =
                        await fetch(
                            "/calculate_distance",
                            {
                                method: "POST",

                                headers: {
                                    "Content-Type":
                                        "application/json"
                                },

                                body: JSON.stringify({

                                    x1:
                                        startPoint.x,

                                    y1:
                                        startPoint.y,

                                    x2:
                                        endPoint.x,

                                    y2:
                                        endPoint.y,

                                    ref_mode:
                                        "a4"
                                })
                            }
                        );


                    const data =
                        await response.json();


                    if (data.success) {

                        console.log(
                            "Measured distance:",
                            data.distance,
                            "cm"
                        );


                        /*
                         Show point-to-point result
                         in Width field.
                        */

                        const width =
                            document.getElementById(
                                "objWidth"
                            );

                        if (width) {

                            width.innerText =
                                data.distance +
                                " cm";
                        }


                        const objectName =
                            document.getElementById(
                                "objName"
                            );

                        if (objectName) {

                            objectName.innerText =
                                "Point-to-Point";
                        }


                        const confidence =
                            document.getElementById(
                                "objConfidence"
                            );

                        if (confidence) {

                            confidence.innerText =
                                "A4 Calibrated";
                        }


                    } else {

                        console.warn(
                            data.message ||
                            "Measurement failed."
                        );


                        alert(
                            data.message ||
                            "Measurement failed."
                        );
                    }

                } catch (error) {

                    console.error(
                        "Distance calculation failed:",
                        error
                    );

                    alert(
                        "Unable to calculate distance."
                    );
                }


                console.log(
                    "Point 2:",
                    endPoint
                );

                return;
            }


            /* =========================================
               THIRD CLICK = START NEW MEASUREMENT
            ========================================= */

            resetPointMeasurement();


            startPoint = {
                x: x,
                y: y
            };


            const p1 =
                document.getElementById(
                    "point1"
                );

            if (p1) {

                p1.style.display = "block";

                p1.style.left =
                    (displayX - 7) +
                    "px";

                p1.style.top =
                    (displayY - 7) +
                    "px";
            }


            console.log(
                "New Point 1:",
                startPoint
            );
        }
    );
}


/* =========================================================
   INITIALIZATION
========================================================= */

console.log(
    "SmartMeasure measurement.js loaded successfully."
);