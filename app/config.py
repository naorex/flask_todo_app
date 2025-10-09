"""
Configuration module for Flask Todo App.

This module provides configuration classes for different environments
and documents all available environment variables.
"""

import os


class Config:
    """Base configuration class with common settings."""

    # Flask core settings
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///todo.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Security settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

    # CSRF settings
    WTF_CSRF_TIME_LIMIT = 3600  # CSRF token expires in 1 hour
    WTF_CSRF_SSL_STRICT = False

    # Request limits
    MAX_CONTENT_LENGTH = 16 * 1024  # 16KB max request size


class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False

    # Development-specific security settings
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False


class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False

    # Production security settings
    SESSION_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True

    def __init__(self):
        super().__init__()
        # Override with stronger defaults for production
        secret_key = os.environ.get("SECRET_KEY")
        if not secret_key:
            raise ValueError(
                "SECRET_KEY environment variable must be set in production"
            )
        self.SECRET_KEY = secret_key


class TestingConfig(Config):
    """Testing environment configuration."""

    DEBUG = False
    TESTING = True

    # Use in-memory database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Security settings for testing
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_SSL_STRICT = False


# Configuration mapping
config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}


def get_config(environment=None):
    """Get configuration class for the specified environment."""
    if environment is None:
        environment = os.environ.get("FLASK_ENV", "development")

    return config.get(environment, config["default"])


# Environment Variables Documentation
ENVIRONMENT_VARIABLES = {
    "FLASK_ENV": {
        "description": "Flask environment (development, production, testing)",
        "default": "development",
        "required": False,
    },
    "SECRET_KEY": {
        "description": "Secret key for session encryption and CSRF protection",
        "default": "dev-secret-key-change-in-production (development only)",
        "required": True,  # Required in production
        "security": "CRITICAL - Must be random and secret in production",
    },
    "DATABASE_URL": {
        "description": "Database connection URL",
        "default": "sqlite:///todo.db",
        "required": False,
        "examples": [
            "sqlite:///todo.db",
            "postgresql://user:pass@localhost/todoapp",
            "mysql://user:pass@localhost/todoapp",
        ],
    },
    "FLASK_HOST": {
        "description": "Host address to bind the Flask server",
        "default": "127.0.0.1 (development), 0.0.0.0 (container)",
        "required": False,
    },
    "FLASK_PORT": {
        "description": "Port number for the Flask server",
        "default": "5000",
        "required": False,
    },
    "CONTAINER": {
        "description": "Set to 'true' to indicate running in container",
        "default": "false",
        "required": False,
    },
}
