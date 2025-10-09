# Flask Todo App

A secure, production-ready todo application built with Flask, featuring user authentication, CSRF protection, and comprehensive security measures.

## Features

- **User Authentication**: Secure registration and login system with Flask-Login
- **Personal Todo Lists**: Each user has their own private todo list
- **Security First**: CSRF protection, input sanitization, and security headers
- **Database Management**: SQLAlchemy ORM with migration support
- **Container Ready**: Docker and Docker Compose support
- **Production Ready**: Comprehensive logging, error handling, and configuration management
- **Testing Suite**: Comprehensive test coverage with pytest

## Quick Start

### Local Development

1. **Clone and Setup**

   ```bash
   git clone <repository-url>
   cd flask-todo-app
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the Application**

   ```bash
   python app.py
   ```

   Visit http://localhost:5000 to access the application.

### Docker Deployment

1. **Using Docker Compose (Recommended)**

   ```bash
   docker-compose up -d
   ```

2. **Using Docker directly**
   ```bash
   docker build -t flask-todo-app .
   docker run -p 5000:5000 -e SECRET_KEY=your-secret-key flask-todo-app
   ```

## Application Architecture

### Core Components

```
flask-todo-app/
├── app.py                 # Application entry point and configuration
├── app/
│   ├── __init__.py       # Flask app factory and initialization
│   ├── models.py         # Database models (User, Todo)
│   ├── routes.py         # Route handlers and forms
│   ├── auth.py           # Authentication utilities
│   ├── security.py       # Security and validation utilities
│   ├── config.py         # Configuration management
│   ├── migrations.py     # Database migration utilities
│   └── templates/        # Jinja2 templates
├── static/               # CSS and static assets
├── tests/                # Test suite
└── logs/                 # Application logs
```

### Script Relations and Data Flow

#### 1. Application Startup (`app.py`)

- **Purpose**: Main entry point that configures and starts the Flask application
- **Key Functions**:
  - Environment detection (development/production/container)
  - Host and port configuration
  - Database connection verification
  - Production logging setup
- **Dependencies**: Imports from `app/__init__.py`

#### 2. Application Factory (`app/__init__.py`)

- **Purpose**: Creates and configures the Flask application instance
- **Key Functions**:
  - Extension initialization (SQLAlchemy, Flask-Login, CSRF)
  - Security headers configuration
  - Error handler registration
  - Blueprint registration
  - Database initialization
- **Dependencies**: Uses `config.py`, `models.py`, `routes.py`, `migrations.py`

#### 3. Database Models (`app/models.py`)

- **Purpose**: Defines data structures and business logic
- **Models**:
  - `User`: Authentication and user management
  - `Todo`: Task management with user association
- **Features**:
  - Input validation
  - Password hashing
  - Relationship management
- **Dependencies**: Uses SQLAlchemy from `app/__init__.py`

#### 4. Route Handlers (`app/routes.py`)

- **Purpose**: HTTP request handling and response generation
- **Blueprints**:
  - `auth`: Registration, login, logout
  - `main`: Todo CRUD operations
- **Features**:
  - Form validation with WTForms
  - CSRF protection
  - User authorization checks
- **Dependencies**: Uses `auth.py`, `security.py`, `models.py`

#### 5. Authentication (`app/auth.py`)

- **Purpose**: User authentication and authorization utilities
- **Key Functions**:
  - User creation and validation
  - Login/logout handling
  - Password verification
  - Security event logging
- **Dependencies**: Uses `models.py`, `security.py`

#### 6. Security (`app/security.py`)

- **Purpose**: Input validation, sanitization, and security logging
- **Key Functions**:
  - Input sanitization (XSS prevention)
  - Password strength validation
  - Security event logging
  - Rate limiting utilities
- **Dependencies**: Standalone utility module

#### 7. Configuration (`app/config.py`)

- **Purpose**: Environment-specific configuration management
- **Configurations**:
  - `DevelopmentConfig`: Debug mode, relaxed security
  - `ProductionConfig`: Security hardened, performance optimized
  - `TestingConfig`: In-memory database, CSRF disabled
- **Dependencies**: Standalone configuration module

#### 8. Database Migrations (`app/migrations.py`)

- **Purpose**: Database schema versioning and updates
- **Key Functions**:
  - Schema version tracking
  - Migration application
  - Database constraint verification
- **Dependencies**: Uses SQLAlchemy from `app/__init__.py`

### Data Flow Diagram

```
HTTP Request
     ↓
app.py (Entry Point)
     ↓
app/__init__.py (App Factory)
     ↓
routes.py (Route Handler)
     ↓
┌─────────────────┬─────────────────┐
│   auth.py       │   security.py   │
│ (Authentication)│ (Validation)    │
└─────────────────┴─────────────────┘
     ↓
models.py (Database Operations)
     ↓
Database (SQLite/PostgreSQL)
     ↓
Template Rendering
     ↓
HTTP Response
```

## Configuration

### Environment Variables

| Variable       | Description                                  | Default           | Required         |
| -------------- | -------------------------------------------- | ----------------- | ---------------- |
| `FLASK_ENV`    | Environment (development/production/testing) | development       | No               |
| `SECRET_KEY`   | Session encryption key                       | dev-key           | Yes (Production) |
| `DATABASE_URL` | Database connection string                   | sqlite:///todo.db | No               |
| `FLASK_HOST`   | Server bind address                          | 127.0.0.1         | No               |
| `FLASK_PORT`   | Server port                                  | 5000              | No               |
| `CONTAINER`    | Container mode flag                          | false             | No               |

### Production Configuration

For production deployment, ensure:

1. **Set a secure SECRET_KEY**:

   ```bash
   export SECRET_KEY=$(python -c 'import secrets; print(secrets.token_hex(32))')
   ```

2. **Use a production database**:

   ```bash
   export DATABASE_URL=postgresql://user:pass@localhost/todoapp
   ```

3. **Enable HTTPS** (recommended with reverse proxy like nginx)

## Database Schema

### User Table

- `id`: Primary key
- `username`: Unique username (3-80 chars, alphanumeric + underscore)
- `password_hash`: Bcrypt hashed password
- `created_at`: Account creation timestamp

### Todo Table

- `id`: Primary key
- `description`: Todo text (max 200 chars)
- `completed`: Boolean completion status
- `created_at`: Creation timestamp
- `user_id`: Foreign key to User table

## Security Features

- **Authentication**: Flask-Login session management
- **CSRF Protection**: WTF-CSRF tokens on all forms
- **Input Validation**: Comprehensive sanitization and validation
- **Security Headers**: XSS, clickjacking, and content type protection
- **Password Security**: Bcrypt hashing with salt
- **SQL Injection Prevention**: SQLAlchemy ORM parameterized queries
- **Session Security**: Secure cookies, session timeout
- **Audit Logging**: Security events and user actions logged

## Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest

# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_models.py
```

## Development

### Adding New Features

1. **Database Changes**: Update models in `app/models.py`
2. **Routes**: Add new routes in `app/routes.py`
3. **Templates**: Create templates in `app/templates/`
4. **Tests**: Add tests in `tests/`
5. **Migrations**: Update `app/migrations.py` if schema changes

### Code Style

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Add docstrings to functions and classes
- Validate inputs and handle errors gracefully

## Deployment

### Docker Production Deployment

1. **Build and run with Docker Compose**:

   ```bash
   # Update docker-compose.yml with production settings
   docker-compose -f docker-compose.yml up -d
   ```

2. **Environment variables for production**:
   ```yaml
   environment:
     - FLASK_ENV=production
     - SECRET_KEY=your-secure-secret-key
     - DATABASE_URL=postgresql://user:pass@db:5432/todoapp
   ```

### Traditional Server Deployment

1. **Use a WSGI server** (Gunicorn recommended):

   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

2. **Set up reverse proxy** (nginx recommended)
3. **Configure SSL/TLS certificates**
4. **Set up monitoring and logging**

## Troubleshooting

### Common Issues

1. **Database Permission Errors**:
   - Ensure write permissions to database directory
   - Check file ownership in Docker containers

2. **CSRF Token Errors**:
   - Verify SECRET_KEY is set consistently
   - Check that forms include CSRF tokens

3. **Container Networking**:
   - Use `0.0.0.0` as host in container environments
   - Ensure proper port mapping in Docker

### Logs

- **Development**: Console output with debug information
- **Production**: File logging in `logs/todo_app.log`
- **Container**: stdout/stderr for container log aggregation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review application logs
3. Open an issue with detailed error information
