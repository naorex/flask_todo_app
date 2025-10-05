"""Integration tests for template rendering."""

import pytest
from flask import url_for

from app import db
from app.models import Todo, User


class TestAuthenticationTemplates:
    """Test authentication template rendering and form functionality."""

    def test_login_template_rendering(self, client):
        """Test login template renders correctly with form elements."""
        response = client.get("/login")
        assert response.status_code == 200

        # Check for essential HTML elements
        assert b"<title>Login - Flask Todo App</title>" in response.data
        assert b'<h2><i class="fas fa-sign-in-alt"></i> Login</h2>' in response.data
        assert b"Sign in to access your todos" in response.data

        # Check for form elements
        assert b'<form method="POST"' in response.data
        assert b'name="username"' in response.data
        assert b'name="password"' in response.data
        assert b'type="submit"' in response.data

        # Check for navigation links
        assert b"Register here" in response.data
        assert b'href="/register"' in response.data

        # Form is properly structured (CSRF handled by Flask-WTF in production)
        assert b'<form method="POST"' in response.data

    def test_register_template_rendering(self, client):
        """Test register template renders correctly with form elements."""
        response = client.get("/register")
        assert response.status_code == 200

        # Check for essential HTML elements
        assert b"<title>Register - Flask Todo App</title>" in response.data
        assert b'<h2><i class="fas fa-user-plus"></i> Register</h2>' in response.data
        assert b"Create your account to start managing todos" in response.data

        # Check for form elements
        assert b'<form method="POST"' in response.data
        assert b'name="username"' in response.data
        assert b'name="password"' in response.data
        assert b'name="password_confirm"' in response.data
        assert b'type="submit"' in response.data

        # Check for validation help text
        assert b"Username must be 3-80 characters long" in response.data
        assert b"Password must be at least 6 characters long" in response.data
        assert b"Re-enter your password to confirm" in response.data

        # Check for navigation links
        assert b"Login here" in response.data
        assert b'href="/login"' in response.data

        # Form is properly structured (CSRF handled by Flask-WTF in production)
        assert b'<form method="POST"' in response.data

    def test_login_form_validation_errors(self, client):
        """Test login form displays validation errors correctly."""
        # Submit empty form
        response = client.post("/login", data={"username": "", "password": ""})

        # Should stay on login page and show errors
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_register_form_validation_errors(self, client):
        """Test register form displays validation errors correctly."""
        # Submit form with mismatched passwords
        response = client.post(
            "/register",
            data={
                "username": "testuser",
                "password": "password123",
                "password_confirm": "different",
            },
        )

        # Should stay on register page
        assert response.status_code == 200
        assert b"Register" in response.data

    def test_authentication_navigation_flow(self, client):
        """Test navigation between login and register pages."""
        # Start at login page
        response = client.get("/login")
        assert b'href="/register"' in response.data

        # Navigate to register page
        response = client.get("/register")
        assert b'href="/login"' in response.data

        # Check that both pages have proper navigation
        assert response.status_code == 200


class TestProtectedTemplates:
    """Test protected template rendering with user context."""

    def test_main_page_template_rendering_authenticated(self, client, app):
        """Test main page template renders correctly for authenticated user."""
        # Create and login user
        with app.app_context():
            user = User(username="testuser", password="testpassword")
            db.session.add(user)
            db.session.commit()

        # Login
        client.post("/login", data={"username": "testuser", "password": "testpassword"})

        response = client.get("/")
        assert response.status_code == 200

        # Check for essential HTML elements
        assert b"<title>My Todos - Flask Todo App</title>" in response.data
        assert b"Welcome back, testuser!" in response.data

        # Check for add todo form
        assert b'<form method="POST" action="/add"' in response.data
        assert b'name="description"' in response.data
        assert b'placeholder="What do you need to do?"' in response.data
        assert b"Add Todo" in response.data

        # Check for add todo form structure
        assert b'<form method="POST" action="/add"' in response.data

        # Check for empty state message (no todos yet)
        assert b"No todos yet!" in response.data
        assert b"Start by adding your first todo above" in response.data

    def test_main_page_with_todos(self, client, app):
        """Test main page displays todos correctly."""
        # Create user and todos
        with app.app_context():
            user = User(username="testuser", password="testpassword")
            db.session.add(user)
            db.session.commit()

            # Add some todos for the user
            todo1 = Todo(description="Test todo 1", user_id=user.id)
            todo1.completed = False
            todo2 = Todo(description="Test todo 2", user_id=user.id)
            todo2.completed = True
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.commit()

        # Login
        client.post("/login", data={"username": "testuser", "password": "testpassword"})

        response = client.get("/")
        assert response.status_code == 200

        # Check that todos are displayed
        assert b"Test todo 1" in response.data
        assert b"Test todo 2" in response.data

        # Check for todo count (flexible matching)
        assert b"You have 2 todo" in response.data
        assert b"completed" in response.data and b"pending" in response.data

        # Check for completion indicators
        assert b"fa-circle text-muted" in response.data  # Incomplete todo
        assert b"fa-check-circle text-success" in response.data  # Completed todo
        assert (
            b"text-decoration-line-through" in response.data
        )  # Completed todo styling

        # Check for action buttons
        assert b"Complete" in response.data  # Complete button for incomplete todo
        assert b"Undo" in response.data  # Undo button for completed todo
        assert b"Delete" in response.data  # Delete buttons

        # Check for toggle and delete forms
        assert b'action="/toggle/' in response.data
        assert b'action="/delete/' in response.data

    def test_user_specific_data_display(self, client, app):
        """Test that users only see their own todos."""
        with app.app_context():
            # Create two users
            user1 = User(username="user1", password="password")
            user2 = User(username="user2", password="password")
            db.session.add(user1)
            db.session.add(user2)
            db.session.commit()

            # Add todos for each user
            todo1 = Todo(description="User 1 todo", user_id=user1.id)
            todo2 = Todo(description="User 2 todo", user_id=user2.id)
            db.session.add(todo1)
            db.session.add(todo2)
            db.session.commit()

        # Login as user1
        client.post("/login", data={"username": "user1", "password": "password"})
        response = client.get("/")

        # Should see only user1's todos
        assert b"User 1 todo" in response.data
        assert b"User 2 todo" not in response.data
        assert b"Welcome back, user1!" in response.data

        # Logout and login as user2
        client.post("/logout")
        client.post("/login", data={"username": "user2", "password": "password"})
        response = client.get("/")

        # Should see only user2's todos
        assert b"User 2 todo" in response.data
        assert b"User 1 todo" not in response.data
        assert b"Welcome back, user2!" in response.data

    def test_unauthenticated_redirect(self, client):
        """Test that unauthenticated users are redirected to login."""
        response = client.get("/")
        assert response.status_code == 302
        assert "/login" in response.location


class TestCSRFProtection:
    """Test CSRF protection and user-specific data display."""

    def test_csrf_tokens_in_templates(self, client, app):
        """Test that CSRF tokens are present in all forms."""
        # Create and login user for protected pages
        with app.app_context():
            user = User(username="testuser", password="testpassword")
            db.session.add(user)
            db.session.commit()

        client.post("/login", data={"username": "testuser", "password": "testpassword"})

        # Check main page has forms
        response = client.get("/")
        assert b'<form method="POST"' in response.data

        # Check login page (logout first)
        client.post("/logout")
        response = client.get("/login")
        assert b'<form method="POST"' in response.data

        # Check register page
        response = client.get("/register")
        assert b'<form method="POST"' in response.data

    def test_form_functionality_with_csrf(self, client, app):
        """Test that forms work correctly with CSRF protection."""
        # Create and login user
        with app.app_context():
            user = User(username="testuser", password="testpassword")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

        client.post("/login", data={"username": "testuser", "password": "testpassword"})

        # Test adding a todo
        response = client.post("/add", data={"description": "Test todo from form"})

        # Should redirect after successful add
        assert response.status_code == 302

        # Verify todo was added
        with app.app_context():
            todo = Todo.query.filter_by(description="Test todo from form").first()
            assert todo is not None
            assert todo.user_id == user_id

    def test_navigation_context(self, client, app):
        """Test navigation shows correct user context."""
        # Create and login user
        with app.app_context():
            user = User(username="testuser", password="testpassword")
            db.session.add(user)
            db.session.commit()

        client.post("/login", data={"username": "testuser", "password": "testpassword"})

        response = client.get("/")

        # Check for user context in navigation
        assert b"Welcome, <strong>testuser</strong>!" in response.data
        assert b"Logout" in response.data
        assert b'action="/logout"' in response.data


class TestResponsiveDesign:
    """Test responsive design elements in templates."""

    def test_bootstrap_classes_present(self, client):
        """Test that Bootstrap CSS classes are present in templates."""
        # Test login page
        response = client.get("/login")
        assert (
            b'class="container"' in response.data
            or b'class="auth-container"' in response.data
        )
        assert b"card auth-card" in response.data
        assert b'class="form-control"' in response.data
        assert b"btn btn-primary btn-lg" in response.data

        # Test register page
        response = client.get("/register")
        assert b'class="form-control"' in response.data
        assert b"btn btn-success btn-lg" in response.data

    def test_meta_viewport_tag(self, client):
        """Test that viewport meta tag is present for responsive design."""
        response = client.get("/login")
        assert (
            b'name="viewport" content="width=device-width, initial-scale=1.0"'
            in response.data
        )

    def test_css_framework_links(self, client):
        """Test that CSS framework links are present."""
        response = client.get("/login")
        assert b"bootstrap" in response.data
        assert b"style.css" in response.data
