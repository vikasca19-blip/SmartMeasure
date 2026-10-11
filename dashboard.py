from flask import render_template
import json
import os


def register_dashboard_routes(app):

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")


    @app.route("/history")
    def history():

        history_file = "outputs/history.json"

        if os.path.exists(history_file):

            with open(history_file, "r") as f:
                history = json.load(f)

        else:

            history = []

        return render_template(
            "history.html",
            history=history
        )


    @app.route("/settings")
    def settings():
        return render_template("settings.html")