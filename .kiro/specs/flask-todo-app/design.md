# Design Document

## Overview

The Flask Todo App is a lightweight web application that provides basic task management functionality. The application follows a simple MVC (Model-View-Controller) pattern using Flask's built-in capabilities. It will use SQLite as the database for simplicity and persistence, with Flask-SQLAlchemy as the ORM. The application will be containerized using Docker for consistent deployment across environments.

## Architecture

The application follows a layered architecture:

```
┌─────────────────────────────────────┐
│           Web Browser               │
└─────────────────────────────────────┘
                    │
                    │ HTTP Requests (with sessions)
                    ▼
┌─────────────────────────────────────┐
│         Flask Application           │
│  ┌─────────────────────────────────┐│
│  │    Authentication Layer         ││
│  │    (Flask-Login, Sessions)      ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │         Routes/Views            ││
│  │    (Protected & Public)         ││
│  └─────────────────────────────────┘│
│  ┌─────────────────────────────────┐│
│  │      Models (ORM)               ││
│  │    (User, Todo with relations)  ││
│  └─────────────────────────────────┘│
└─────────────────────────────────────┘
                    │
                    │ SQL Queries
                    ▼
┌─────────────────────────────────────┐
│         SQLite Database             │
│      (Users & User-specific Todos)  │
└─────────────────────────────────────┘
```

### Technology Stack

- **Backend Framework**: Flask (Python web framework)
- **Authentication**: Flask-Login (session management)
- **Password Hashing**: Werkzeug security utilities
- **Database**: SQLite (lightweight, file-based database)
- **ORM**: Flask-SQLAlchemy (database abstraction layer)
- **Templating**: Jinja2 (Flask's default template engine)
- **Frontend**: HTML5, CSS3, minimal JavaScript
- **Containerization**: Docker with Docker Compose

## Components and Interfaces

### 1. Flask Application Structure

```
flask-todo-app/
├── app/
│   ├── __init__.py          # Flask app factory
│   ├── models.py            # Database models (User, Todo)
│   ├── auth.py              # Authentication utilities
│   ├── routes.py            # Route handlers
│   └── templates/           # HTML templates
│       ├── base.html        # Base template with auth context
│       ├── login.html       # Login form
│       ├── register.html    # Registration form
│       └── index.html       # Main todo list page (protected)
├── static/
│   └── style.css            # CSS styles
├── app.py                   # Application entry point
├── requirements.txt         # Python dependencies (includes Flask-Login)
├── Dockerfile              # Container definition
└── docker-compose.yml      # Container orchestration
```

### 2. Database Models

**User Model**:

```python
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    todos = db.relationship('Todo', backref='user', lazy=True, cascade='all, delete-orphan')
```

**Todo Model**:

```python
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
```

### 3. API Endpoints

#### Authentication Endpoints

| Method | Endpoint    | Description               | Requirements           |
| ------ | ----------- | ------------------------- | ---------------------- |
| GET    | `/login`    | Display login form        | Req 6.2                |
| POST   | `/login`    | Process login             | Req 6.3, 6.4, 6.5      |
| GET    | `/register` | Display registration form | Req 7.1                |
| POST   | `/register` | Process registration      | Req 7.2, 7.3, 7.4, 7.5 |
| POST   | `/logout`   | Log out user              | Req 8.2, 8.3           |

#### Todo Management Endpoints (Protected)

| Method | Endpoint       | Description            | Requirements                |
| ------ | -------------- | ---------------------- | --------------------------- |
| GET    | `/`            | Display user's todos   | Req 1.1, 1.2, 1.3, 9.2      |
| POST   | `/add`         | Create new todo        | Req 2.1, 2.2, 2.3, 2.4, 9.1 |
| POST   | `/toggle/<id>` | Toggle todo completion | Req 3.1, 3.2, 3.3, 9.4      |
| POST   | `/delete/<id>` | Delete todo item       | Req 4.1, 4.2, 4.3, 9.4      |

### 4. Frontend Components

**Base Template (base.html)**:

- Common HTML structure
- CSS styling links
- Navigation elements with user context
- Flash message display area
- Logout button (when authenticated)

**Login Page (login.html)**:

- Username and password input fields
- Login form submission
- Link to registration page
- Error message display

**Registration Page (register.html)**:

- Username, password, and confirm password fields
- Registration form submission
- Link to login page
- Validation error display

**Main Page (index.html)** (Protected):

- Welcome message with username
- Todo list display (user-specific)
- Add new todo form
- Toggle completion buttons
- Delete buttons
- Empty state message

### 5. Authentication Components

**Flask-Login Integration**:

- `LoginManager` configuration for session management
- `UserMixin` implementation for User model
- `@login_required` decorator for protected routes
- `current_user` context for templates

**Password Security**:

- `werkzeug.security.generate_password_hash()` for password hashing
- `werkzeug.security.check_password_hash()` for password verification
- Salt-based hashing with secure defaults

**Session Management**:

- Flask sessions for user authentication state
- Session timeout configuration
- Secure session cookies (HTTPOnly, Secure flags)
- Remember me functionality (optional)

**Route Protection**:

- Authentication middleware for protected routes
- Automatic redirect to login for unauthenticated users
- User context injection into templates
- Authorization checks for user-specific resources

## Data Models

### User Entity

| Field         | Type        | Constraints                 | Description           |
| ------------- | ----------- | --------------------------- | --------------------- |
| id            | Integer     | Primary Key, Auto-increment | Unique identifier     |
| username      | String(80)  | Not Null, Unique            | User login name       |
| password_hash | String(120) | Not Null                    | Hashed password       |
| created_at    | DateTime    | Default: UTC Now            | Account creation time |

### Todo Entity

| Field       | Type        | Constraints                 | Description        |
| ----------- | ----------- | --------------------------- | ------------------ |
| id          | Integer     | Primary Key, Auto-increment | Unique identifier  |
| description | String(200) | Not Null                    | Task description   |
| completed   | Boolean     | Not Null, Default: False    | Completion status  |
| created_at  | DateTime    | Default: UTC Now            | Creation timestamp |
| user_id     | Integer     | Foreign Key, Not Null       | Owner user ID      |

### Database Schema

```sql
CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(120) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE todo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description VARCHAR(200) NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_id INTEGER NOT NULL,
    FOREIGN KEY (user_id) REFERENCES user (id)
);
```

### Entity Relationships

- **User** has many **Todo** items (One-to-Many)
- **Todo** belongs to one **User** (Many-to-One)
- Cascade delete: When a user is deleted, all their todos are deleted

## Error Handling

### Application-Level Error Handling

1. **Authentication Errors**:
   - Invalid login credentials → Flash error message, stay on login page
   - Username already exists → Flash error message, stay on registration page
   - Password mismatch → Flash error message, stay on registration page
   - Unauthorized access → Redirect to login page with message

2. **Form Validation Errors**:
   - Empty todo description → Flash error message, stay on page
   - Empty username/password → Flash error message, stay on form
   - Invalid input → Sanitize and validate before processing

3. **Database Errors**:
   - Connection issues → Display user-friendly error page
   - Constraint violations → Log error, show generic message
   - User not found → Handle gracefully with appropriate redirect

4. **HTTP Errors**:
   - 401 Unauthorized → Redirect to login page
   - 403 Forbidden → Access denied page
   - 404 Not Found → Custom error page for missing todos/users
   - 500 Internal Server Error → Generic error page with logging

### Input Validation

**Authentication Input Validation**:

- Username: Required, 3-80 characters, alphanumeric and underscore only
- Password: Required, minimum 6 characters, no maximum (hashed)
- Password confirmation: Must match password field
- Username uniqueness: Check against existing users

**Todo Input Validation**:

- Todo description: Required, max 200 characters, strip whitespace
- Todo ID: Must be valid integer for toggle/delete operations
- User ownership: Verify user owns the todo before operations

**Security Validation**:

- CSRF protection using Flask-WTF for all forms
- Input sanitization to prevent XSS attacks
- SQL injection prevention through ORM usage

## Testing Strategy

### Unit Tests

- User model validation and password hashing
- Todo model validation and user relationships
- Authentication utility functions
- Route handler logic and response codes
- Form validation and error handling

### Integration Tests

- User registration and login workflows
- Session management and logout functionality
- Protected route access control
- User-specific todo operations
- End-to-end authentication flows
- Database persistence verification
- Template rendering with user context

### Security Tests

- Password hashing and verification
- Session security and timeout
- Unauthorized access prevention
- CSRF protection validation
- Input sanitization verification

### Manual Testing

- Cross-browser compatibility
- Responsive design verification
- User experience validation
- Authentication flow usability

## Docker Configuration

### Dockerfile Strategy

- Use Python 3.13 slim base image
- Install dependencies via requirements.txt
- Copy application code
- Expose port 5000
- Set Flask environment variables
- Use non-root user for security

### Docker Compose Configuration

- Single service for the Flask app
- Volume mounting for development
- Environment variable configuration
- Port mapping (5000:5000)
- Automatic restart policy

### Container Environment

- Flask app runs on 0.0.0.0:5000 (accessible from host)
- SQLite database file persisted via volume
- Environment variables for Flask configuration
- Health check endpoint for container monitoring

## Security Considerations

### Application Security

1. **Input Sanitization & Validation**:
   - All user inputs sanitized and validated before processing
   - Maximum length limits enforced (200 chars for todo description)
   - HTML encoding for special characters
   - Whitespace trimming and normalization

2. **SQL Injection Prevention**:
   - SQLAlchemy ORM with parameterized queries
   - No raw SQL queries or string concatenation
   - Input validation before database operations

3. **Cross-Site Scripting (XSS) Prevention**:
   - Jinja2 auto-escaping enabled by default
   - Content Security Policy (CSP) headers
   - Sanitization of user-generated content

4. **Cross-Site Request Forgery (CSRF) Protection**:
   - Flask-WTF CSRF tokens for all forms
   - SameSite cookie attributes
   - Referrer validation for state-changing operations

5. **Session Security**:
   - Secure session configuration
   - HTTPOnly and Secure cookie flags
   - Session timeout implementation
   - Strong secret key generation

### Container Security

6. **Docker Security**:
   - Non-root user (app user) for running the application
   - Minimal base image (python:3.13-slim) to reduce attack surface
   - No unnecessary packages or tools in container
   - Read-only filesystem where possible
   - Security scanning of container images

7. **Network Security**:
   - Container runs on internal network by default
   - Only necessary ports exposed (5000)
   - No direct database access from outside container

### Data Security

8. **Database Security**:
   - SQLite file with restricted permissions (600)
   - Database file stored in protected volume
   - No sensitive data stored in plain text
   - Regular backup considerations

9. **Environment Security**:
   - Environment variables for sensitive configuration
   - No hardcoded secrets in code
   - Secure defaults for Flask configuration
   - Debug mode disabled in production

### HTTP Security Headers

10. **Security Headers**:
    - Content-Security-Policy
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Strict-Transport-Security (if HTTPS)

### Logging and Monitoring

11. **Security Monitoring**:
    - Application logging for security events
    - Error logging without exposing sensitive information
    - Request logging for audit trails
    - Container health monitoring

## Performance Considerations

1. **Database**: SQLite suitable for single-user application, minimal overhead
2. **Static Files**: Served directly by Flask in development, nginx in production
3. **Caching**: Browser caching for static assets
4. **Container**: Lightweight Python slim image for faster startup

## Scalability and Concurrent Users

### Current Architecture Limitations

**Concurrent User Capacity**:

- **SQLite Limitation**: SQLite supports multiple readers but only one writer at a time
- **Flask Development Server**: Single-threaded, suitable for 1-5 concurrent users
- **Estimated Capacity**: 1-10 concurrent users with current architecture

### Scaling Considerations

**For Low-Scale Usage (1-10 users)**:

- Current SQLite + Flask setup is sufficient
- Simple deployment with Docker container
- Minimal resource requirements

**For Medium-Scale Usage (10-100 users)**:

- **Database**: Migrate to PostgreSQL or MySQL for better concurrency
- **Application Server**: Use Gunicorn with multiple workers
- **Caching**: Add Redis for session storage and caching
- **Load Balancing**: Nginx reverse proxy for static files

**For High-Scale Usage (100+ users)**:

- **Database**: PostgreSQL with connection pooling
- **Application**: Multiple Flask instances behind load balancer
- **Caching**: Redis cluster for distributed caching
- **Infrastructure**: Container orchestration (Kubernetes)
- **Monitoring**: Application performance monitoring (APM)

### Recommended Scaling Path

1. **Phase 1 (Current)**: SQLite + Flask (1-10 users)
2. **Phase 2**: PostgreSQL + Gunicorn (10-100 users)
3. **Phase 3**: Multi-instance + Load Balancer (100+ users)

### Resource Requirements

**Current Setup**:

- CPU: 0.1-0.5 cores
- Memory: 128-512 MB
- Storage: 100 MB (including OS)
- Network: Minimal bandwidth requirements

**Note**: This design prioritizes simplicity and ease of deployment over high scalability. For applications requiring high concurrent user support, architectural changes would be needed.
