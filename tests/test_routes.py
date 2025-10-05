"""Tests for authentication and todo routes."""

import pytest
from flask import url_for
from flask_login import current_user

from app import db
from app.models import Todo, User


class TestAuthenticationRoutes:
    """Test authentication flows and session management."""

    def test_login_required_redirects_to_login(self, client):
        """Test that unauthenticated users are redirected to login page."""
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_login_with_valid_credentials(self, client, app):
        """Test successful login with valid credentials."""
        with app.app_context():
            # Create a test user
            user = User("testuser", "testpass123")
            db.session.add(user)
            db.session.commit()

        # Attempt login
        response = client.post(
            "/login",
            data={"username": "testuser", "password": "testpass123"},
            follow_redirects=True,
        )

        assert response.status_code == 200
        assert b"Welcome back, testuser!" in response.data

    def test_login_with_invalid_credentials(self, client, app):
        """Test login failure with invalid credentials."""
        with app.app_context():
            # Create a test user
            user = User("testuser", "testpass123")
            db.session.add(user)
            db.session.commit()

        # Attempt login with wrong password
        response = client.post(
            "/login", data={"username": "testuser", "password": "wrongpass"}
        )

        assert response.status_code == 200
        assert b"Invalid username or password" in response.data

    def test_logout_ends_session(self, client, app):
        """Test that logout ends user session."""
        with app.app_context():
            # Create and login user
            user = User("testuser", "testpass123")
            db.session.add(user)
            db.session.commit()

        # Login
        client.post("/login", data={"username": "testuser", "password": "testpass123"})

        # Logout
        response = client.post("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"You have been logged out" in response.data

        # Verify access to protected route is denied
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.location


class TestProtectedRouteAccess:
    """Test protected route access control."""

    def test_index_requires_authentication(self, client):
        """Test that index route requires authentication."""
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_add_todo_requires_authentication(self, client):
        """Test that add todo route requires authentication."""
        response = client.post("/add", data={"description": "Test todo"})
        assert response.status_code == 302
        assert "/login" in response.location

    def test_toggle_todo_requires_authentication(self, client):
        """Test that toggle todo route requires authentication."""
        response = client.post("/toggle/1")
        assert response.status_code == 302
        assert "/login" in response.location

    def test_delete_todo_requires_authentication(self, client):
        """Test that delete todo route requires authentication."""
        response = client.post("/delete/1")
        assert response.status_code == 302
        assert "/login" in response.location


class TestUserSpecificTodoOperations:
    """Test user-specific todo operations and data isolation."""

    def create_and_login_user(
        self, client, app, username="testuser", password="testpass123"
    ):
        """Helper method to create and login a user."""
        with app.app_context():
            user = User(username, password)
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post("/login", data={"username": username, "password": password})

        return user_id

    def test_index_shows_only_user_todos(self, client, app):
        """Test that index page shows only current user's todos."""
        # Create two users
        user1_id = self.create_and_login_user(client, app, "user1", "pass123")

        with app.app_context():
            # Create todos for user1
            todo1 = Todo("User 1 Todo 1", user1_id)
            todo2 = Todo("User 1 Todo 2", user1_id)
            db.session.add_all([todo1, todo2])
            db.session.commit()

        # Create second user and their todos
        client.post("/logout")
        user2_id = self.create_and_login_user(client, app, "user2", "pass456")

        with app.app_context():
            todo3 = Todo("User 2 Todo 1", user2_id)
            db.session.add(todo3)
            db.session.commit()

        # Check that user2 only sees their own todos
        response = client.get("/")
        assert response.status_code == 200
        assert b"User 2 Todo 1" in response.data
        assert b"User 1 Todo 1" not in response.data
        assert b"User 1 Todo 2" not in response.data

    def test_add_todo_creates_user_specific_todo(self, client, app):
        """Test that adding a todo associates it with current user."""
        user_id = self.create_and_login_user(client, app)

        # Add a todo
        response = client.post(
            "/add", data={"description": "My new todo"}, follow_redirects=True
        )

        assert response.status_code == 200
        assert b"Todo added successfully!" in response.data
        assert b"My new todo" in response.data

        # Verify todo is associated with correct user
        with app.app_context():
            todo = Todo.query.filter_by(description="My new todo").first()
            assert todo is not None
            assert todo.user_id == user_id

    def test_add_todo_validates_input(self, client, app):
        """Test that add todo validates input."""
        self.create_and_login_user(client, app)

        # Try to add empty todo
        response = client.post("/add", data={"description": ""}, follow_redirects=True)

        assert response.status_code == 200
        assert b"Todo description is required" in response.data

    def test_toggle_todo_ownership_verification(self, client, app):
        """Test that users can only toggle their own todos."""
        # Create user1 and their todo
        user1_id = self.create_and_login_user(client, app, "user1", "pass123")

        with app.app_context():
            todo1 = Todo("User 1 Todo", user1_id)
            db.session.add(todo1)
            db.session.commit()
            todo1_id = todo1.id

        # Create user2
        client.post("/logout")
        self.create_and_login_user(client, app, "user2", "pass456")

        # Try to toggle user1's todo as user2
        response = client.post(f"/toggle/{todo1_id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"Todo not found or you don&#39;t have permission" in response.data

    def test_delete_todo_ownership_verification(self, client, app):
        """Test that users can only delete their own todos."""
        # Create user1 and their todo
        user1_id = self.create_and_login_user(client, app, "user1", "pass123")

        with app.app_context():
            todo1 = Todo("User 1 Todo", user1_id)
            db.session.add(todo1)
            db.session.commit()
            todo1_id = todo1.id

        # Create user2
        client.post("/logout")
        self.create_and_login_user(client, app, "user2", "pass456")

        # Try to delete user1's todo as user2
        response = client.post(f"/delete/{todo1_id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"Todo not found or you don&#39;t have permission" in response.data

    def test_toggle_todo_success(self, client, app):
        """Test successful todo toggle operation."""
        user_id = self.create_and_login_user(client, app)

        with app.app_context():
            todo = Todo("Test todo", user_id)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id
            initial_status = todo.completed

        # Toggle the todo
        response = client.post(f"/toggle/{todo_id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"Todo marked as" in response.data

        # Verify status changed
        with app.app_context():
            updated_todo = db.session.get(Todo, todo_id)
            assert updated_todo.completed != initial_status

    def test_delete_todo_success(self, client, app):
        """Test successful todo deletion."""
        user_id = self.create_and_login_user(client, app)

        with app.app_context():
            todo = Todo("Test todo to delete", user_id)
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id

        # Delete the todo
        response = client.post(f"/delete/{todo_id}", follow_redirects=True)
        assert response.status_code == 200
        assert b"Todo deleted successfully!" in response.data

        # Verify todo is deleted
        with app.app_context():
            deleted_todo = db.session.get(Todo, todo_id)
            assert deleted_todo is None

    def test_nonexistent_todo_operations(self, client, app):
        """Test operations on nonexistent todos."""
        self.create_and_login_user(client, app)

        # Try to toggle nonexistent todo
        response = client.post("/toggle/999", follow_redirects=True)
        assert response.status_code == 200
        assert b"Todo not found" in response.data

        # Try to delete nonexistent todo
        response = client.post("/delete/999", follow_redirects=True)
        assert response.status_code == 200
        assert b"Todo not found" in response.data
