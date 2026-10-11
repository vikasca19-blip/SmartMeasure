from flask import render_template


def register_auth_routes(app):

    @app.route("/")
    def landing():
        return render_template("landing.html")

    @app.route("/login")
    def login():
        return render_template("login.html")

    @app.route("/register")
    def register():
        return render_template("register.html")