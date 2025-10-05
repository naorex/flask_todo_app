import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Configuration from environment variables
    app.config["SECRET_KEY"] = os.environ.get(
        "SECRET_KEY", "dev-secret-key-change-in-production"
    )
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
        "DATABASE_URL", "sqlite:///todo.db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Security configurations
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("FLASK_ENV") == "production"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["PERMANENT_SESSION_LIFETIME"] = 3600  # 1 hour

    # Initialize extensions with app
    db.init_app(app)
    csrf.init_app(app)

    # Configure Flask-Login
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "info"
    login_manager.session_protection = "strong"

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User

        return User.query.get(int(user_id))

    # Security headers
    @app.after_request
    def set_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'"
        )
        return response

    # Register blueprints (will be implemented in later tasks)
    # from app.routes import main
    # app.register_blueprint(main)

    return app
