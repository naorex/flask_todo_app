"""Authentication utilities for the Flask Todo App."""

from functools import wraps

from flask import current_app, flash, redirect, url_for
from flask_login import current_user

from app import db
from app.models import User


def load_user(user_id):
    """
    User loader function for Flask-Login.

    This function is called by Flask-Login to reload the user object
    from the user ID stored in the session.

    Args:
        user_id (str): The user ID stored in the session

    Returns:
        User: The user object or None if not found
    """
    try:
        return User.query.get(int(user_id))
    except (TypeError, ValueError):
        return None


def authenticate_user(username, password):
    """
    Authenticate a user with username and password.

    Args:
        username (str): The username to authenticate
        password (str): The password to verify

    Returns:
        User: The authenticated user object or None if authentication fails
    """
    if not username or not password:
        return None

    # Find user by username (case-insensitive)
    user = User.query.filter(User.username.ilike(username.strip())).first()

    if user and user.check_password(password):
        return user

    return None


def create_user(username, password, password_confirm=None):
    """
    Create a new user account with validation.

    Args:
        username (str): The desired username
        password (str): The password
        password_confirm (str, optional): Password confirmation

    Returns:
        tuple: (User object or None, error message or None)
    """
    try:
        # Validate password confirmation if provided
        if password_confirm is not None and password != password_confirm:
            return None, "Passwords do not match"

        # Check if username already exists (case-insensitive)
        existing_user = User.query.filter(User.username.ilike(username.strip())).first()
        if existing_user:
            return None, "Username already exists"

        # Create new user (User.__init__ handles validation)
        user = User(username=username, password=password)

        # Save to database
        db.session.add(user)
        db.session.commit()

        return user, None

    except ValueError as e:
        # Handle validation errors from User model
        return None, str(e)
    except Exception as e:
        # Handle database errors
        db.session.rollback()
        current_app.logger.error(f"Error creating user: {e}")
        return None, "An error occurred while creating the account"


def login_required_with_message(f):
    """
    Decorator that requires login and shows a custom message.

    This is an alternative to Flask-Login's @login_required decorator
    that allows for custom flash messages.

    Args:
        f: The function to decorate

    Returns:
        The decorated function
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Please log in to access this page.", "info")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def get_current_user():
    """
    Get the current authenticated user.

    Returns:
        User: The current user object or None if not authenticated
    """
    if current_user.is_authenticated:
        return current_user
    return None


def is_user_authenticated():
    """
    Check if the current user is authenticated.

    Returns:
        bool: True if user is authenticated, False otherwise
    """
    return current_user.is_authenticated


def validate_user_ownership(user_id):
    """
    Validate that the current user matches the given user_id.

    This is useful for ensuring users can only access their own resources.

    Args:
        user_id (int): The user ID to validate against

    Returns:
        bool: True if current user owns the resource, False otherwise
    """
    if not current_user.is_authenticated:
        return False

    return current_user.id == user_id


def get_user_by_id(user_id):
    """
    Get a user by their ID.

    Args:
        user_id (int): The user ID to look up

    Returns:
        User: The user object or None if not found
    """
    try:
        return User.query.get(int(user_id))
    except (TypeError, ValueError):
        return None


def get_user_by_username(username):
    """
    Get a user by their username (case-insensitive).

    Args:
        username (str): The username to look up

    Returns:
        User: The user object or None if not found
    """
    if not username:
        return None

    return User.query.filter(User.username.ilike(username.strip())).first()
