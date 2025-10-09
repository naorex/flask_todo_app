"""Security utilities for input validation and sanitization."""

import html
import re
from typing import Optional


def sanitize_input(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize user input by removing dangerous characters and normalizing whitespace.

    Args:
        text (str): The input text to sanitize
        max_length (int, optional): Maximum allowed length

    Returns:
        str: Sanitized text
    """
    if not text:
        return ""

    # Strip whitespace and normalize
    text = text.strip()

    # HTML escape to prevent XSS
    text = html.escape(text)

    # Remove null bytes and control characters (except newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", text)

    # Normalize whitespace (replace multiple spaces with single space)
    text = re.sub(r"\s+", " ", text)

    # Truncate if max_length is specified
    if max_length and len(text) > max_length:
        text = text[:max_length]

    return text


def validate_username_format(username: str) -> bool:
    """
    Validate username format using regex.

    Args:
        username (str): Username to validate

    Returns:
        bool: True if valid format, False otherwise
    """
    if not username:
        return False

    # Username must be 3-80 characters, alphanumeric and underscore only
    pattern = r"^[a-zA-Z0-9_]{3,80}$"
    return bool(re.match(pattern, username))


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password strength requirements.

    Args:
        password (str): Password to validate

    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"

    if len(password) < 6:
        return False, "Password must be at least 6 characters long"

    if len(password) > 128:
        return False, "Password must be no more than 128 characters long"

    # Check for at least one letter and one number (optional but recommended)
    has_letter = bool(re.search(r"[a-zA-Z]", password))
    has_number = bool(re.search(r"\d", password))

    if not (has_letter and has_number):
        # This is a warning, not a hard requirement
        pass

    return True, ""


def sanitize_todo_description(description: str) -> str:
    """
    Sanitize todo description with specific rules.

    Args:
        description (str): Todo description to sanitize

    Returns:
        str: Sanitized description
    """
    return sanitize_input(description, max_length=200)


def is_safe_redirect_url(url: str) -> bool:
    """
    Check if a redirect URL is safe (prevents open redirect attacks).

    Args:
        url (str): URL to validate

    Returns:
        bool: True if safe, False otherwise
    """
    if not url:
        return False

    # Only allow relative URLs or URLs to the same domain
    if url.startswith("/") and not url.startswith("//"):
        return True

    # Reject absolute URLs to prevent open redirects
    return False


def rate_limit_key(identifier: str) -> str:
    """
    Generate a rate limiting key for an identifier.

    Args:
        identifier (str): User identifier (IP, username, etc.)

    Returns:
        str: Rate limiting key
    """
    return f"rate_limit:{sanitize_input(identifier, max_length=50)}"


def log_security_event(event_type: str, details: dict, user_id: Optional[int] = None):
    """
    Log security-related events for monitoring.

    Args:
        event_type (str): Type of security event
        details (dict): Event details
        user_id (int, optional): User ID if applicable
    """
    from flask import current_app, request

    log_data = {
        "event_type": event_type,
        "details": details,
        "user_id": user_id,
        "ip_address": request.remote_addr if request else None,
        "user_agent": request.headers.get("User-Agent") if request else None,
    }

    current_app.logger.warning(f"Security Event: {event_type}", extra=log_data)


def handle_database_error(
    operation: str, error: Exception, user_id: Optional[int] = None
):
    """
    Handle database errors with proper logging and user feedback.

    Args:
        operation (str): Description of the operation that failed
        error (Exception): The exception that occurred
        user_id (int, optional): User ID if applicable

    Returns:
        str: User-friendly error message
    """
    from flask import current_app

    from app import db

    # Rollback the session
    try:
        db.session.rollback()
    except Exception:
        pass  # Ignore rollback errors

    # Log the error
    current_app.logger.error(
        f"Database error during {operation}: {error}",
        extra={
            "operation": operation,
            "user_id": user_id,
            "error_type": type(error).__name__,
        },
    )

    # Return user-friendly message
    return f"An error occurred while {operation}. Please try again."


def handle_validation_error(field: str, error: str, user_id: Optional[int] = None):
    """
    Handle validation errors with proper logging.

    Args:
        field (str): Field that failed validation
        error (str): Validation error message
        user_id (int, optional): User ID if applicable

    Returns:
        str: User-friendly error message
    """
    from flask import current_app

    current_app.logger.info(
        f"Validation error for {field}: {error}",
        extra={"field": field, "user_id": user_id},
    )

    return error


def log_user_action(action: str, details: dict, user_id: int):
    """
    Log user actions for audit trail.

    Args:
        action (str): Action performed
        details (dict): Action details
        user_id (int): User ID
    """
    from datetime import datetime

    from flask import current_app, request

    log_data = {
        "action": action,
        "details": details,
        "user_id": user_id,
        "ip_address": request.remote_addr if request else None,
        "timestamp": datetime.now().isoformat(),
    }

    current_app.logger.info(f"User Action: {action}", extra=log_data)
