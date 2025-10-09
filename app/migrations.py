"""
Database migration utilities for Flask Todo App.

This module provides simple database migration support for future schema updates.
"""

import os
import sqlite3
from datetime import datetime, timezone

from flask import current_app

from app import db


class MigrationManager:
    """Simple migration manager for database schema updates."""

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize migration manager with Flask app."""
        self.app = app

    def get_db_version(self):
        """Get current database schema version."""
        try:
            # Check if migration table exists
            db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
            if db_uri.startswith("sqlite:///"):
                db_path = db_uri.replace("sqlite:///", "")

                if not os.path.exists(db_path):
                    return 0

                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()

                # Check if migration_version table exists
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name='migration_version'
                """
                )

                if not cursor.fetchone():
                    # Create migration_version table
                    cursor.execute(
                        """
                        CREATE TABLE migration_version (
                            id INTEGER PRIMARY KEY,
                            version INTEGER NOT NULL,
                            applied_at DATETIME NOT NULL,
                            description TEXT
                        )
                    """
                    )
                    cursor.execute(
                        """
                        INSERT INTO migration_version (version, applied_at, description)
                        VALUES (1, ?, 'Initial schema')
                    """,
                        (datetime.now(timezone.utc).isoformat(),),
                    )
                    conn.commit()
                    conn.close()
                    return 1

                # Get current version
                cursor.execute("SELECT MAX(version) FROM migration_version")
                result = cursor.fetchone()
                conn.close()

                return result[0] if result[0] is not None else 0

        except Exception as e:
            current_app.logger.error(f"Error getting database version: {e}")
            return 0

    def apply_migrations(self):
        """Apply any pending migrations."""
        current_version = self.get_db_version()
        target_version = self.get_target_version()

        if current_version < target_version:
            current_app.logger.info(
                f"Applying migrations from version {current_version} to {target_version}"
            )

            # Apply migrations sequentially
            for version in range(current_version + 1, target_version + 1):
                self.apply_migration(version)

        elif current_version > target_version:
            current_app.logger.warning(
                f"Database version {current_version} is newer than application version {target_version}"
            )

    def get_target_version(self):
        """Get the target schema version for this application version."""
        # For now, we only have version 1 (initial schema)
        # Future versions would be added here
        return 1

    def apply_migration(self, version):
        """Apply a specific migration version."""
        try:
            if version == 1:
                # Version 1: Initial schema (already handled by create_all)
                self.record_migration(
                    version, "Initial schema with User and Todo models"
                )

            # Future migrations would be added here
            # elif version == 2:
            #     self.apply_migration_v2()

            current_app.logger.info(f"Applied migration version {version}")

        except Exception as e:
            current_app.logger.error(
                f"Failed to apply migration version {version}: {e}"
            )
            raise

    def record_migration(self, version, description):
        """Record a migration as applied."""
        db_uri = current_app.config["SQLALCHEMY_DATABASE_URI"]
        if db_uri.startswith("sqlite:///"):
            db_path = db_uri.replace("sqlite:///", "")

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Ensure migration_version table exists
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS migration_version (
                    id INTEGER PRIMARY KEY,
                    version INTEGER NOT NULL,
                    applied_at DATETIME NOT NULL,
                    description TEXT
                )
            """
            )

            cursor.execute(
                """
                INSERT OR REPLACE INTO migration_version (version, applied_at, description)
                VALUES (?, ?, ?)
            """,
                (version, datetime.now(timezone.utc).isoformat(), description),
            )

            conn.commit()
            conn.close()

    def check_database_constraints(self):
        """Verify that database constraints are properly set up."""
        try:
            # Use SQLAlchemy inspector to check table structure
            from sqlalchemy import inspect

            from app import db
            from app.models import Todo, User

            inspector = inspect(db.engine)

            # Check if tables exist
            tables = inspector.get_table_names()
            current_app.logger.info(f"Database tables: {tables}")

            if "user" not in tables:
                raise ValueError("User table not found in database")

            if "todo" not in tables:
                raise ValueError("Todo table not found in database")

            # Check User table columns
            user_columns = inspector.get_columns("user")
            user_column_names = [col["name"] for col in user_columns]
            current_app.logger.info(f"User table columns: {user_column_names}")

            required_user_columns = ["id", "username", "password_hash", "created_at"]
            for col in required_user_columns:
                if col not in user_column_names:
                    raise ValueError(f"Missing required column '{col}' in user table")

            # Check Todo table columns
            todo_columns = inspector.get_columns("todo")
            todo_column_names = [col["name"] for col in todo_columns]
            current_app.logger.info(f"Todo table columns: {todo_column_names}")

            required_todo_columns = [
                "id",
                "description",
                "completed",
                "created_at",
                "user_id",
            ]
            for col in required_todo_columns:
                if col not in todo_column_names:
                    raise ValueError(f"Missing required column '{col}' in todo table")

            # Check foreign key constraints
            fk_constraints = inspector.get_foreign_keys("todo")
            user_fk_exists = any(
                fk["referred_table"] == "user"
                and "user_id" in fk["constrained_columns"]
                for fk in fk_constraints
            )

            if not user_fk_exists:
                current_app.logger.warning(
                    "Foreign key constraint from todo.user_id to user.id not found"
                )

            current_app.logger.info("Database constraints verified successfully")

        except Exception as e:
            current_app.logger.error(f"Database constraint check failed: {e}")
            raise


# Global migration manager instance
migration_manager = MigrationManager()
