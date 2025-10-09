import os

from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name=None):
    """Create and configure the Flask application."""
    # Explicitly set static folder path for container compatibility
    app = Flask(__name__, static_folder="../static", static_url_path="/static")

    # Load configuration
    from app.config import get_config

    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development")

    config_class = get_config(config_name)
    app.config.from_object(config_class)

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
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        # Enhanced Content Security Policy
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "script-src 'self' https://cdn.jsdelivr.net https://kit.fontawesome.com; "
            "img-src 'self' data:; "
            "font-src 'self' https://cdn.jsdelivr.net https://ka-f.fontawesome.com; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Add HSTS header for production
        if os.environ.get("FLASK_ENV") == "production":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        return response

    # Configure logging
    configure_logging(app)

    # Register error handlers
    register_error_handlers(app)

    # Initialize database
    init_database(app)

    # Register blueprints
    from app.routes import auth, main

    app.register_blueprint(auth)
    app.register_blueprint(main)

    return app


def init_database(app):
    """Initialize database tables and constraints."""
    with app.app_context():
        import os

        from app.migrations import migration_manager
        from app.models import Todo, User

        # Initialize migration manager
        migration_manager.init_app(app)

        # Get database file path from URI
        db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
        if db_uri.startswith("sqlite:///"):
            db_path = db_uri.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)

            # Create database directory if it doesn't exist
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, mode=0o755)
                app.logger.info(f"Created database directory: {db_dir}")

        # Create all database tables
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")

            # Apply any pending migrations
            migration_manager.apply_migrations()

            # Verify database constraints (only for persistent databases)
            if not db_uri.startswith("sqlite:///:memory:"):
                migration_manager.check_database_constraints()

            # Set proper file permissions for SQLite database
            if db_uri.startswith("sqlite:///"):
                if os.path.exists(db_path):
                    try:
                        os.chmod(db_path, 0o600)  # Read/write for owner only
                        app.logger.info(f"Set database file permissions: {db_path}")
                    except (OSError, PermissionError) as e:
                        app.logger.warning(
                            f"Could not set database file permissions ({e}), continuing anyway"
                        )

        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")
            raise


def configure_logging(app):
    """Configure application logging."""
    import logging
    from logging.handlers import RotatingFileHandler

    if not app.debug and not app.testing:
        # Try to configure file logging, fall back to console if it fails
        import os

        try:
            # Create logs directory if it doesn't exist
            if not os.path.exists("logs"):
                os.makedirs("logs", mode=0o755, exist_ok=True)

            # Configure file handler with rotation
            file_handler = RotatingFileHandler(
                "logs/todo_app.log", maxBytes=10240000, backupCount=10  # 10MB
            )
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            app.logger.info("File logging configured successfully")
        except (OSError, PermissionError) as e:
            # Fall back to console logging if file logging fails
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            console_handler.setLevel(logging.INFO)
            app.logger.addHandler(console_handler)
            app.logger.warning(f"File logging failed ({e}), using console logging")

        app.logger.setLevel(logging.INFO)
        app.logger.info("Todo App startup")


def register_error_handlers(app):
    """Register custom error handlers."""
    from flask import render_template, request
    from flask_login import current_user

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        app.logger.warning(
            f"Unauthorized access attempt: {request.url} from {request.remote_addr}"
        )
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        user_info = (
            f"user_id={current_user.id}"
            if current_user.is_authenticated
            else "anonymous"
        )
        app.logger.warning(
            f"Forbidden access attempt: {request.url} by {user_info} from {request.remote_addr}"
        )
        return (
            render_template("errors/401.html"),
            403,
        )  # Use 401 template for consistency

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        app.logger.info(f"Page not found: {request.url} from {request.remote_addr}")
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors."""
        from app import db

        db.session.rollback()
        user_info = (
            f"user_id={current_user.id}"
            if current_user.is_authenticated
            else "anonymous"
        )
        app.logger.error(
            f"Server Error: {error} for {request.url} by {user_info} from {request.remote_addr}"
        )
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle 413 Request Entity Too Large errors."""
        app.logger.warning(
            f"Request too large: {request.url} from {request.remote_addr}"
        )
        from flask import flash, redirect, url_for

        flash("Request too large. Please try with less data.", "error")
        return redirect(
            url_for("main.index")
            if current_user.is_authenticated
            else url_for("auth.login")
        )

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Too Many Requests errors."""
        app.logger.warning(
            f"Rate limit exceeded: {request.url} from {request.remote_addr}"
        )
        from flask import flash, redirect, url_for

        flash("Too many requests. Please try again later.", "error")
        return redirect(
            url_for("main.index")
            if current_user.is_authenticated
            else url_for("auth.login")
        )
