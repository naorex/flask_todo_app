"""
Flask Todo App - Main Application Entry Point

This file serves as the main entry point for the Flask todo application.
It configures the application for different environments and starts the server
with appropriate settings for development and production deployment.
"""

import os
import sys


def get_environment_config():
    """Determine and configure environment settings."""
    # Detect environment
    flask_env = os.environ.get("FLASK_ENV", "development").lower()
    debug_mode = flask_env == "development"

    # Container environment detection
    is_container = (
        os.path.exists("/.dockerenv") or os.environ.get("CONTAINER") == "true"
    )

    # Host configuration
    if is_container:
        # In container, bind to all interfaces
        host = "0.0.0.0"
    else:
        # Local development, bind to localhost only
        host = os.environ.get("FLASK_HOST", "127.0.0.1")

    # Port configuration
    port = int(os.environ.get("FLASK_PORT", "5000"))

    return {
        "host": host,
        "port": port,
        "debug": debug_mode,
        "environment": flask_env,
        "is_container": is_container,
    }


def configure_production_logging():
    """Configure logging for production environment."""
    import logging

    # Set up basic logging configuration
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]",
        handlers=[
            logging.StreamHandler(sys.stdout),
            (
                logging.FileHandler("logs/todo_app.log")
                if os.path.exists("logs")
                else logging.StreamHandler(sys.stdout)
            ),
        ],
    )


def main():
    """Main application entry point."""
    try:
        # Import Flask app factory
        from app import create_app

        # Get environment configuration
        config = get_environment_config()

        # Create Flask application
        app = create_app()

        # Configure production logging if not in debug mode
        if not config["debug"]:
            configure_production_logging()

        # Log startup information
        app.logger.info(f"Starting Flask Todo App")
        app.logger.info(f"Environment: {config['environment']}")
        app.logger.info(f"Debug mode: {config['debug']}")
        app.logger.info(f"Container mode: {config['is_container']}")
        app.logger.info(f"Listening on {config['host']}:{config['port']}")

        # Verify Flask-Login is properly initialized
        if not hasattr(app, "login_manager"):
            app.logger.error("Flask-Login not properly initialized")
            sys.exit(1)

        # Verify database is accessible
        with app.app_context():
            from app import db

            try:
                # Test database connection
                with db.engine.connect() as connection:
                    connection.execute(db.text("SELECT 1"))
                app.logger.info("Database connection verified")
            except Exception as e:
                app.logger.error(f"Database connection failed: {e}")
                sys.exit(1)

        # Start the Flask development server
        if config["debug"]:
            app.run(
                host=config["host"],
                port=config["port"],
                debug=config["debug"],
                use_reloader=True,
                use_debugger=True,
            )
        else:
            # Production mode - recommend using a proper WSGI server
            app.logger.warning(
                "Running in production mode with Flask development server. "
                "Consider using a production WSGI server like Gunicorn."
            )
            app.run(
                host=config["host"],
                port=config["port"],
                debug=False,
                use_reloader=False,
                use_debugger=False,
            )

    except ImportError as e:
        print(f"Failed to import Flask application: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Failed to start application: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
