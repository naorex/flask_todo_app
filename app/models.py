"""Database models for the Flask Todo App."""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

# Import the db instance from the app package
from app import db


class User(UserMixin, db.Model):
    """User model for authentication and todo ownership."""

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationship to todos with cascade delete
    todos = db.relationship(
        "Todo", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def __init__(self, username, password):
        """Initialize user with username and hashed password."""
        self.username = self.validate_username(username)
        self.set_password(password)

    def set_password(self, password):
        """Hash and set the user's password."""
        if not password or len(password.strip()) < 6:
            raise ValueError("Password must be at least 6 characters long")
        self.password_hash = generate_password_hash(password.strip())

    def check_password(self, password):
        """Check if provided password matches the stored hash."""
        if not password:
            return False
        return check_password_hash(self.password_hash, password.strip())

    @staticmethod
    def validate_username(username):
        """Validate username format and requirements."""
        if not username:
            raise ValueError("Username is required")

        username = username.strip()

        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters long")

        if len(username) > 80:
            raise ValueError("Username must be no more than 80 characters long")

        # Check for valid characters (alphanumeric and underscore only)
        if not username.replace("_", "").isalnum():
            raise ValueError(
                "Username can only contain letters, numbers, and underscores"
            )

        return username

    def __repr__(self):
        """String representation of User object."""
        return f"<User {self.username}>"


class Todo(db.Model):
    """Todo model for task management."""

    __tablename__ = "todo"

    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=False, index=True
    )

    def __init__(self, description, user_id):
        """Initialize todo with description and user association."""
        self.description = self.validate_description(description)
        self.user_id = user_id
        self.completed = False

    @staticmethod
    def validate_description(description):
        """Validate todo description format and requirements."""
        if not description:
            raise ValueError("Todo description is required")

        description = description.strip()

        if not description:
            raise ValueError("Todo description cannot be empty or only whitespace")

        if len(description) > 200:
            raise ValueError(
                "Todo description must be no more than 200 characters long"
            )

        return description

    def toggle_completion(self):
        """Toggle the completion status of the todo."""
        self.completed = not self.completed

    def __repr__(self):
        """String representation of Todo object."""
        status = "✓" if self.completed else "○"
        return f'<Todo {self.id}: {status} {self.description[:30]}{"..." if len(self.description) > 30 else ""}>'
