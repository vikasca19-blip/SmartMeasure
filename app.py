from flask import Flask

from routes.auth import register_auth_routes
from routes.dashboard import register_dashboard_routes
from routes.measure import register_measure_routes

app = Flask(__name__)

# Register all routes
register_auth_routes(app)
register_dashboard_routes(app)
register_measure_routes(app)

if __name__ == "__main__":
    app.run(debug=True)