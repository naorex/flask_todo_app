"""
Flask Todo App - Main Application Entry Point

This file serves as the main entry point for the Flask todo application.
The actual Flask app factory and configuration will be implemented in app/__init__.py
"""

if __name__ == "__main__":
    # Import and run the Flask application
    # The app factory will be implemented in task 2.1
    from app import create_app

    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True)
