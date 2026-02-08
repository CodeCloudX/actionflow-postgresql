from flask import Flask
from config import Config
from model import db
from flask_migrate import Migrate
from services.complaint_service import init_scheduler

def create_app():
    """Creates and configures the Flask application."""
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)  # Initialize Flask-Migrate

    # Import and register blueprints
    from app.auth import auth_bp
    from app.admin_dashboard import admin_bp
    from app.user_dashboard import user_bp

    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')

    # Initialize the background scheduler
    init_scheduler(app)

    return app
