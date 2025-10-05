# Test Suite for Flask Todo App

This directory contains comprehensive unit tests for the Flask Todo App models.

## Test Structure

- `conftest.py` - Test configuration and fixtures for Flask app and database setup
- `test_models.py` - Unit tests for User and Todo models

## Test Coverage

### User Model Tests

- User creation with valid data
- Password hashing and verification
- Password validation (minimum length, empty passwords)
- Username validation (length, characters, uniqueness)
- Database persistence and retrieval
- Username uniqueness constraints
- String representation

### Todo Model Tests

- Todo creation with valid data
- Description validation (length, empty descriptions)
- Completion status toggling
- Database persistence and retrieval
- String representation with completion indicators

### User-Todo Relationship Tests

- One-to-many relationship between users and todos
- Cascade deletion (deleting user deletes their todos)
- Data isolation between different users
- Foreign key relationships

## Running Tests

```bash
# Run all model tests
uv run pytest tests/test_models.py -v

# Run specific test class
uv run pytest tests/test_models.py::TestUserModel -v

# Run with coverage (if coverage is installed)
uv run pytest tests/test_models.py --cov=app.models
```

## Test Requirements Covered

- **Requirement 6.3**: User authentication and password verification
- **Requirement 7.2**: User registration validation
- **Requirement 9.1**: User-specific todo data isolation

All tests use temporary SQLite databases that are created and destroyed for each test to ensure test isolation.
