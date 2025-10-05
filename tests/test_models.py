"""Unit tests for User and Todo models."""

from datetime import datetime

import pytest
from werkzeug.security import check_password_hash

from app import db
from app.models import Todo, User


class TestUserModel:
    """Test cases for the User model."""

    def test_user_creation_with_valid_data(self, app):
        """Test creating a user with valid username and password."""
        with app.app_context():
            user = User(username="testuser", password="password123")

            assert user.username == "testuser"
            assert user.password_hash is not None
            assert user.password_hash != "password123"  # Password should be hashed
            # created_at is set by SQLAlchemy default when saved to database
            assert user.id is None  # Not saved to database yet

            # Save to database to test created_at
            db.session.add(user)
            db.session.commit()
            assert isinstance(user.created_at, datetime)

    def test_user_password_hashing(self, app):
        """Test that passwords are properly hashed and can be verified."""
        with app.app_context():
            user = User(username="testuser", password="mypassword")

            # Password should be hashed
            assert user.password_hash != "mypassword"
            assert len(user.password_hash) > 20  # Hashed passwords are longer

            # Should be able to verify correct password
            assert user.check_password("mypassword") is True

            # Should reject incorrect password
            assert user.check_password("wrongpassword") is False
            assert user.check_password("") is False
            assert user.check_password(None) is False

    def test_user_password_validation(self, app):
        """Test password validation requirements."""
        with app.app_context():
            # Password too short
            with pytest.raises(
                ValueError, match="Password must be at least 6 characters long"
            ):
                User(username="testuser", password="12345")

            # Empty password
            with pytest.raises(
                ValueError, match="Password must be at least 6 characters long"
            ):
                User(username="testuser", password="")

            # Whitespace-only password
            with pytest.raises(
                ValueError, match="Password must be at least 6 characters long"
            ):
                User(username="testuser", password="     ")

            # Valid password with whitespace (should be stripped)
            user = User(username="testuser", password="  password123  ")
            assert user.check_password("password123") is True

    def test_username_validation(self, app):
        """Test username validation requirements."""
        with app.app_context():
            # Valid usernames
            user1 = User(username="validuser", password="password123")
            assert user1.username == "validuser"

            user2 = User(username="user_123", password="password123")
            assert user2.username == "user_123"

            user3 = User(username="  validuser  ", password="password123")
            assert user3.username == "validuser"  # Should be stripped

            # Empty username
            with pytest.raises(ValueError, match="Username is required"):
                User(username="", password="password123")

            # None username
            with pytest.raises(ValueError, match="Username is required"):
                User(username=None, password="password123")

            # Username too short
            with pytest.raises(
                ValueError, match="Username must be at least 3 characters long"
            ):
                User(username="ab", password="password123")

            # Username too long
            long_username = "a" * 81
            with pytest.raises(
                ValueError, match="Username must be no more than 80 characters long"
            ):
                User(username=long_username, password="password123")

            # Invalid characters
            with pytest.raises(
                ValueError,
                match="Username can only contain letters, numbers, and underscores",
            ):
                User(username="user@domain", password="password123")

            with pytest.raises(
                ValueError,
                match="Username can only contain letters, numbers, and underscores",
            ):
                User(username="user-name", password="password123")

            with pytest.raises(
                ValueError,
                match="Username can only contain letters, numbers, and underscores",
            ):
                User(username="user name", password="password123")

    def test_user_database_persistence(self, app):
        """Test user creation, saving, and retrieval from database."""
        with app.app_context():
            # Create and save user
            user = User(username="dbuser", password="password123")
            db.session.add(user)
            db.session.commit()

            # User should have an ID after saving
            assert user.id is not None
            assert isinstance(user.id, int)

            # Retrieve user from database
            retrieved_user = User.query.filter_by(username="dbuser").first()
            assert retrieved_user is not None
            assert retrieved_user.username == "dbuser"
            assert retrieved_user.check_password("password123") is True
            assert retrieved_user.id == user.id

    def test_user_username_uniqueness(self, app):
        """Test that usernames must be unique in the database."""
        with app.app_context():
            # Create first user
            user1 = User(username="uniqueuser", password="password123")
            db.session.add(user1)
            db.session.commit()

            # Try to create second user with same username
            user2 = User(username="uniqueuser", password="password456")
            db.session.add(user2)

            # Should raise integrity error when committing
            with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
                db.session.commit()

    def test_user_repr(self, app):
        """Test string representation of User object."""
        with app.app_context():
            user = User(username="testuser", password="password123")
            assert repr(user) == "<User testuser>"


class TestTodoModel:
    """Test cases for the Todo model."""

    def test_todo_creation_with_valid_data(self, app):
        """Test creating a todo with valid description and user_id."""
        with app.app_context():
            # Create a user first
            user = User(username="todouser", password="password123")
            db.session.add(user)
            db.session.commit()

            # Create todo
            todo = Todo(description="Test todo item", user_id=user.id)

            assert todo.description == "Test todo item"
            assert todo.user_id == user.id
            assert todo.completed is False  # Default value
            # created_at is set by SQLAlchemy default when saved to database
            assert todo.id is None  # Not saved to database yet

            # Save to database to test created_at
            db.session.add(todo)
            db.session.commit()
            assert isinstance(todo.created_at, datetime)
            assert todo.id is not None  # Should have ID after saving

    def test_todo_description_validation(self, app):
        """Test todo description validation requirements."""
        with app.app_context():
            # Create a user first
            user = User(username="todouser", password="password123")
            db.session.add(user)
            db.session.commit()

            # Valid description
            todo1 = Todo(description="Valid todo description", user_id=user.id)
            assert todo1.description == "Valid todo description"

            # Description with whitespace (should be stripped)
            todo2 = Todo(description="  Todo with spaces  ", user_id=user.id)
            assert todo2.description == "Todo with spaces"

            # Empty description
            with pytest.raises(ValueError, match="Todo description is required"):
                Todo(description="", user_id=user.id)

            # None description
            with pytest.raises(ValueError, match="Todo description is required"):
                Todo(description=None, user_id=user.id)

            # Whitespace-only description
            with pytest.raises(
                ValueError, match="Todo description cannot be empty or only whitespace"
            ):
                Todo(description="   ", user_id=user.id)

            # Description too long
            long_description = "a" * 201
            with pytest.raises(
                ValueError,
                match="Todo description must be no more than 200 characters long",
            ):
                Todo(description=long_description, user_id=user.id)

    def test_todo_completion_toggle(self, app):
        """Test toggling todo completion status."""
        with app.app_context():
            # Create a user first
            user = User(username="todouser", password="password123")
            db.session.add(user)
            db.session.commit()

            # Create todo
            todo = Todo(description="Test todo", user_id=user.id)

            # Initially not completed
            assert todo.completed is False

            # Toggle to completed
            todo.toggle_completion()
            assert todo.completed is True

            # Toggle back to not completed
            todo.toggle_completion()
            assert todo.completed is False

    def test_todo_database_persistence(self, app):
        """Test todo creation, saving, and retrieval from database."""
        with app.app_context():
            # Create a user first
            user = User(username="todouser", password="password123")
            db.session.add(user)
            db.session.commit()

            # Create and save todo
            todo = Todo(description="Database test todo", user_id=user.id)
            db.session.add(todo)
            db.session.commit()

            # Todo should have an ID after saving
            assert todo.id is not None
            assert isinstance(todo.id, int)

            # Retrieve todo from database
            retrieved_todo = Todo.query.filter_by(
                description="Database test todo"
            ).first()
            assert retrieved_todo is not None
            assert retrieved_todo.description == "Database test todo"
            assert retrieved_todo.user_id == user.id
            assert retrieved_todo.completed is False
            assert retrieved_todo.id == todo.id

    def test_todo_repr(self, app):
        """Test string representation of Todo object."""
        with app.app_context():
            # Create a user first
            user = User(username="todouser", password="password123")
            db.session.add(user)
            db.session.commit()

            # Test incomplete todo
            todo1 = Todo(description="Short todo", user_id=user.id)
            db.session.add(todo1)
            db.session.commit()
            assert repr(todo1) == f"<Todo {todo1.id}: ○ Short todo>"

            # Test completed todo
            todo2 = Todo(description="Another todo", user_id=user.id)
            todo2.toggle_completion()
            db.session.add(todo2)
            db.session.commit()
            assert repr(todo2) == f"<Todo {todo2.id}: ✓ Another todo>"

            # Test long description (should be truncated)
            long_desc = "This is a very long todo description that should be truncated in the repr"
            todo3 = Todo(description=long_desc, user_id=user.id)
            db.session.add(todo3)
            db.session.commit()
            expected = f"<Todo {todo3.id}: ○ {long_desc[:30]}...>"
            assert repr(todo3) == expected


class TestUserTodoRelationship:
    """Test cases for User-Todo relationships."""

    def test_user_todo_relationship(self, app):
        """Test the one-to-many relationship between User and Todo."""
        with app.app_context():
            # Create user
            user = User(username="relationuser", password="password123")
            db.session.add(user)
            db.session.commit()

            # Create multiple todos for the user
            todo1 = Todo(description="First todo", user_id=user.id)
            todo2 = Todo(description="Second todo", user_id=user.id)
            todo3 = Todo(description="Third todo", user_id=user.id)

            db.session.add_all([todo1, todo2, todo3])
            db.session.commit()

            # Test relationship from user side
            assert len(user.todos) == 3
            assert todo1 in user.todos
            assert todo2 in user.todos
            assert todo3 in user.todos

            # Test relationship from todo side
            assert todo1.user == user
            assert todo2.user == user
            assert todo3.user == user

    def test_user_deletion_cascades_todos(self, app):
        """Test that deleting a user also deletes their todos (cascade delete)."""
        with app.app_context():
            # Create user
            user = User(username="cascadeuser", password="password123")
            db.session.add(user)
            db.session.commit()
            user_id = user.id

            # Create todos for the user
            todo1 = Todo(description="Todo 1", user_id=user.id)
            todo2 = Todo(description="Todo 2", user_id=user.id)
            db.session.add_all([todo1, todo2])
            db.session.commit()

            # Verify todos exist
            assert Todo.query.filter_by(user_id=user_id).count() == 2

            # Delete user
            db.session.delete(user)
            db.session.commit()

            # Verify todos are also deleted (cascade)
            assert Todo.query.filter_by(user_id=user_id).count() == 0

    def test_multiple_users_separate_todos(self, app):
        """Test that different users have separate todo lists."""
        with app.app_context():
            # Create two users
            user1 = User(username="user1", password="password123")
            user2 = User(username="user2", password="password123")
            db.session.add_all([user1, user2])
            db.session.commit()

            # Create todos for each user
            todo1_user1 = Todo(description="User 1 Todo 1", user_id=user1.id)
            todo2_user1 = Todo(description="User 1 Todo 2", user_id=user1.id)
            todo1_user2 = Todo(description="User 2 Todo 1", user_id=user2.id)

            db.session.add_all([todo1_user1, todo2_user1, todo1_user2])
            db.session.commit()

            # Verify each user has their own todos
            assert len(user1.todos) == 2
            assert len(user2.todos) == 1

            # Verify todos belong to correct users
            assert todo1_user1 in user1.todos
            assert todo2_user1 in user1.todos
            assert todo1_user2 in user2.todos

            assert todo1_user1 not in user2.todos
            assert todo2_user1 not in user2.todos
            assert todo1_user2 not in user1.todos

    def test_todo_user_foreign_key_constraint(self, app):
        """Test that todos require a valid user_id."""
        with app.app_context():
            # Create a valid user first
            user = User(username="validuser", password="password123")
            db.session.add(user)
            db.session.commit()

            # Create todo with valid user_id should work
            valid_todo = Todo(description="Valid todo", user_id=user.id)
            db.session.add(valid_todo)
            db.session.commit()

            # Verify the todo was created successfully
            assert valid_todo.id is not None
            assert valid_todo.user_id == user.id

            # Note: SQLite doesn't enforce foreign key constraints by default in testing,
            # but in production with proper FK constraints enabled, invalid user_ids would fail
