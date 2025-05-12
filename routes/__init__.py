from .reminder import reminder_bp
from .todo import todo_bp
from .timer import timer_bp
from .materials import materials_bp
from .study_log import study_log_bp

def register_blueprints(app):
    app.register_blueprint(reminder_bp)
    app.register_blueprint(todo_bp)
    app.register_blueprint(timer_bp)
    app.register_blueprint(materials_bp)
    app.register_blueprint(study_log_bp)
