from flask import Flask
from routes import register_blueprints
from scheduler import start_scheduler


app = Flask(__name__)
register_blueprints(app)

if __name__ == "__main__":
    start_scheduler()
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
