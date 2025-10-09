# Flask Todo App - System Diagrams

This document contains UML diagrams for the Flask Todo application using Mermaid.js.

## Class Diagram

```mermaid
classDiagram
    class User {
        +int id
        +string username
        +string password_hash
        +datetime created_at
        +List~Todo~ todos
        +__init__(username, password)
        +set_password(password)
        +check_password(password) bool
        +validate_username(username) string
        +__repr__() string
    }

    class Todo {
        +int id
        +string description
        +bool completed
        +datetime created_at
        +int user_id
        +User user
        +__init__(description, user_id)
        +validate_description(description) string
        +toggle_completion()
        +__repr__() string
    }

    class Flask {
        +SQLAlchemy db
        +LoginManager login_manager
        +CSRFProtect csrf
        +create_app(config_name) Flask
        +init_database(app)
        +configure_logging(app)
        +register_error_handlers(app)
    }

    class AuthService {
        +load_user(user_id) User
        +authenticate_user(username, password) User
        +create_user(username, password, password_confirm) tuple
        +login_required_with_message(f) function
        +get_current_user() User
        +is_user_authenticated() bool
        +validate_user_ownership(user_id) bool
    }

    class SecurityService {
        +sanitize_input(text, max_length) string
        +validate_username_format(username) bool
        +validate_password_strength(password) tuple
        +sanitize_todo_description(description) string
        +is_safe_redirect_url(url) bool
        +log_security_event(event_type, details, user_id)
        +handle_database_error(operation, error, user_id) string
    }

    class ConfigManager {
        +Config base_config
        +DevelopmentConfig dev_config
        +ProductionConfig prod_config
        +TestingConfig test_config
        +get_config(environment) Config
    }

    class MigrationManager {
        +Flask app
        +init_app(app)
        +get_db_version() int
        +apply_migrations()
        +get_target_version() int
        +apply_migration(version)
        +record_migration(version, description)
        +check_database_constraints()
    }

    User *-- Todo
    Flask o-- User
    Flask o-- Todo
    Flask o-- AuthService
    Flask o-- SecurityService
    Flask o-- ConfigManager
    Flask o-- MigrationManager
    AuthService -- User
    AuthService -- SecurityService
```

## Use Case Diagram

```mermaid
graph TB
    subgraph "Flask Todo Application"
        subgraph "Authentication System"
            UC1[Register Account]
            UC2[Login]
            UC3[Logout]
        end

        subgraph "Todo Management"
            UC4[View Todo List]
            UC5[Add New Todo]
            UC6[Mark Todo Complete/Incomplete]
            UC7[Delete Todo]
        end

        subgraph "System Administration"
            UC8[Database Migration]
            UC9[Security Logging]
            UC10[Error Handling]
        end
    end

    Actor1[Guest User] --> UC1
    Actor1 --> UC2

    Actor2[Authenticated User] --> UC2
    Actor2 --> UC3
    Actor2 --> UC4
    Actor2 --> UC5
    Actor2 --> UC6
    Actor2 --> UC7

    Actor3[System Administrator] --> UC8
    Actor3 --> UC9
    Actor3 --> UC10

    UC1 -.->|after registration| UC2
    UC2 -->|successful login| UC4
    UC5 -->|refresh list| UC4
    UC6 -->|refresh list| UC4
    UC7 -->|refresh list| UC4
```

## Sequence Diagrams

### User Registration Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant R as Routes (auth.register)
    participant A as AuthService
    participant S as SecurityService
    participant M as User Model
    participant DB as Database

    U->>B: Navigate to /register
    B->>R: GET /register
    R->>B: Return registration form
    B->>U: Display form

    U->>B: Submit registration data
    B->>R: POST /register (username, password, confirm)
    R->>A: create_user(username, password, confirm)
    A->>S: sanitize_input(username)
    S-->>A: sanitized username
    A->>M: User.query.filter(username exists?)
    M->>DB: SELECT user WHERE username = ?
    DB-->>M: No existing user
    M-->>A: None (user doesn't exist)
    A->>M: User(username, password)
    M->>S: validate_username(username)
    S-->>M: validated username
    M->>M: set_password(password) - hash password
    M-->>A: new User object
    A->>DB: db.session.add(user) & commit()
    DB-->>A: Success
    A->>S: log_security_event("registration_success")
    S->>S: Log event
    A-->>R: (user, None)
    R->>B: Redirect to login with success message
    B->>U: Show login page with success
```

### User Login Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant R as Routes (auth.login)
    participant A as AuthService
    participant S as SecurityService
    participant M as User Model
    participant DB as Database
    participant FL as Flask-Login

    U->>B: Navigate to /login
    B->>R: GET /login
    R->>B: Return login form
    B->>U: Display form

    U->>B: Submit credentials
    B->>R: POST /login (username, password)
    R->>A: authenticate_user(username, password)
    A->>S: sanitize_input(username)
    S-->>A: sanitized username
    A->>M: User.query.filter(username ilike ?)
    M->>DB: SELECT user WHERE username ILIKE ?
    DB-->>M: User object or None
    M-->>A: User object
    A->>M: user.check_password(password)
    M->>M: check_password_hash(stored_hash, password)
    M-->>A: True (password valid)
    A->>S: log_security_event("login_success")
    S->>S: Log successful login
    A-->>R: User object
    R->>FL: login_user(user)
    FL->>FL: Create session
    R->>B: Redirect to main page with welcome message
    B->>U: Show todo list page
```

### Add Todo Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant R as Routes (main.add_todo)
    participant S as SecurityService
    participant M as Todo Model
    participant DB as Database
    participant FL as Flask-Login

    U->>B: Enter todo description and submit
    B->>R: POST /add (description, csrf_token)
    R->>R: validate_csrf_token()
    R->>FL: current_user (get authenticated user)
    FL-->>R: User object
    R->>S: sanitize_todo_description(description)
    S->>S: sanitize_input(description, max_length=200)
    S-->>R: sanitized description
    R->>M: Todo(description, user_id)
    M->>M: validate_description(description)
    M-->>R: new Todo object
    R->>DB: db.session.add(todo) & commit()
    DB-->>R: Success
    R->>R: Log todo creation
    R->>B: Redirect to main page with success message
    B->>U: Show updated todo list
```

### Toggle Todo Completion Sequence

```mermaid
sequenceDiagram
    participant U as User
    participant B as Browser
    participant R as Routes (main.toggle_todo)
    participant M as Todo Model
    participant DB as Database
    participant FL as Flask-Login
    participant S as SecurityService

    U->>B: Click toggle button for todo
    B->>R: POST /toggle/<todo_id> (csrf_token)
    R->>R: validate_csrf_token()
    R->>FL: current_user (get authenticated user)
    FL-->>R: User object
    R->>M: Todo.query.filter_by(id=todo_id, user_id=current_user.id)
    M->>DB: SELECT todo WHERE id=? AND user_id=?
    DB-->>M: Todo object or None

    alt Todo exists and user owns it
        M-->>R: Todo object
        R->>M: todo.toggle_completion()
        M->>M: self.completed = not self.completed
        R->>DB: db.session.commit()
        DB-->>R: Success
        R->>R: Log toggle action
        R->>B: Redirect with success message
        B->>U: Show updated todo list
    else Todo not found or unauthorized
        M-->>R: None
        R->>S: log_security_event("unauthorized_todo_access")
        S->>S: Log security violation
        R->>B: Redirect with error message
        B->>U: Show error message
    end
```

### Application Startup Sequence

```mermaid
sequenceDiagram
    participant OS as Operating System
    participant APP as app.py
    participant INIT as app/__init__.py
    participant CONFIG as ConfigManager
    participant DB as Database
    participant MIG as MigrationManager
    participant FLASK as Flask Server

    OS->>APP: python app.py
    APP->>APP: get_environment_config()
    APP->>INIT: create_app()
    INIT->>CONFIG: get_config(environment)
    CONFIG-->>INIT: Configuration object
    INIT->>INIT: Initialize extensions (db, login_manager, csrf)
    INIT->>INIT: Configure security headers
    INIT->>INIT: Register error handlers
    INIT->>INIT: init_database(app)
    INIT->>MIG: migration_manager.init_app(app)
    INIT->>DB: db.create_all()
    DB-->>INIT: Tables created
    INIT->>MIG: migration_manager.apply_migrations()
    MIG->>DB: Apply any pending migrations
    DB-->>MIG: Migrations applied
    INIT->>MIG: migration_manager.check_database_constraints()
    MIG->>DB: Verify table structure
    DB-->>MIG: Constraints verified
    INIT->>INIT: Register blueprints (auth, main)
    INIT-->>APP: Flask app instance
    APP->>DB: Test database connection
    DB-->>APP: Connection verified
    APP->>FLASK: app.run(host, port, debug)
    FLASK-->>OS: Server started and listening
```

## Component Architecture Diagram

```mermaid
graph TB
    subgraph "Presentation Layer"
        BROWSER[Web Browser]
        TEMPLATES[Jinja2 Templates]
    end

    subgraph "Application Layer"
        subgraph "Flask Application"
            MAIN[app.py - Entry Point]
            FACTORY[app/__init__.py - App Factory]
            ROUTES[app/routes.py - Route Handlers]
        end

        subgraph "Business Logic"
            AUTH[app/auth.py - Authentication]
            SECURITY[app/security.py - Security Utils]
            MODELS[app/models.py - Data Models]
        end

        subgraph "Configuration & Management"
            CONFIG[app/config.py - Configuration]
            MIGRATIONS[app/migrations.py - DB Migrations]
        end
    end

    subgraph "Data Layer"
        DATABASE[(SQLite/PostgreSQL Database)]
        LOGS[Log Files]
    end

    subgraph "Infrastructure"
        DOCKER[Docker Container]
        NGINX[Reverse Proxy - Optional]
    end

    BROWSER <--> NGINX
    NGINX <--> DOCKER
    DOCKER --> MAIN
    MAIN --> FACTORY
    FACTORY --> ROUTES
    FACTORY --> CONFIG
    FACTORY --> MIGRATIONS
    ROUTES --> AUTH
    ROUTES --> SECURITY
    ROUTES --> MODELS
    ROUTES --> TEMPLATES
    TEMPLATES --> BROWSER
    AUTH --> MODELS
    AUTH --> SECURITY
    MODELS --> DATABASE
    MIGRATIONS --> DATABASE
    FACTORY --> LOGS
    SECURITY --> LOGS

    classDef presentation fill:#e1f5fe
    classDef application fill:#f3e5f5
    classDef data fill:#e8f5e8
    classDef infrastructure fill:#fff3e0

    class BROWSER,TEMPLATES presentation
    class MAIN,FACTORY,ROUTES,AUTH,SECURITY,MODELS,CONFIG,MIGRATIONS application
    class DATABASE,LOGS data
    class DOCKER,NGINX infrastructure
```

## Database Entity Relationship Diagram

```mermaid
erDiagram
    USER {
        int id PK
        string username UK
        string password_hash
        datetime created_at
    }

    TODO {
        int id PK
        string description
        boolean completed
        datetime created_at
        int user_id FK
    }

    MIGRATION_VERSION {
        int id PK
        int version
        datetime applied_at
        string description
    }

    USER ||--o{ TODO : "owns"

    USER {
        string username "3-80 chars, alphanumeric + underscore"
        string password_hash "bcrypt hashed"
        datetime created_at "UTC timezone"
    }

    TODO {
        string description "max 200 chars"
        boolean completed "default false"
        datetime created_at "UTC timezone"
    }
```

## Security Flow Diagram

```mermaid
flowchart TD
    START([HTTP Request]) --> HTTPS{HTTPS?}
    HTTPS -->|No| REDIRECT[Redirect to HTTPS]
    HTTPS -->|Yes| HEADERS[Apply Security Headers]

    HEADERS --> CSP[Content Security Policy]
    HEADERS --> XSS[XSS Protection]
    HEADERS --> FRAME[Frame Options]
    HEADERS --> CONTENT[Content Type Options]

    CSP --> AUTH{Authenticated?}
    XSS --> AUTH
    FRAME --> AUTH
    CONTENT --> AUTH

    AUTH -->|No| LOGIN[Redirect to Login]
    AUTH -->|Yes| CSRF{Valid CSRF Token?}

    CSRF -->|No| ERROR[CSRF Error]
    CSRF -->|Yes| INPUT[Input Sanitization]

    INPUT --> VALIDATE[Input Validation]
    VALIDATE --> AUTHORIZE{User Authorized?}

    AUTHORIZE -->|No| FORBIDDEN[403 Forbidden]
    AUTHORIZE -->|Yes| PROCESS[Process Request]

    PROCESS --> LOG[Security Logging]
    LOG --> RESPONSE[Generate Response]

    LOGIN --> RESPONSE
    ERROR --> RESPONSE
    FORBIDDEN --> RESPONSE
    REDIRECT --> RESPONSE

    RESPONSE --> END([HTTP Response])

    classDef security fill:#ffebee
    classDef success fill:#e8f5e8
    classDef error fill:#ffcdd2

    class HTTPS,HEADERS,CSP,XSS,FRAME,CONTENT,CSRF,INPUT,VALIDATE,AUTHORIZE,LOG security
    class PROCESS,RESPONSE success
    class REDIRECT,LOGIN,ERROR,FORBIDDEN error
```

## MIGRATION_VERSION Table Documentation

### Purpose of the MIGRATION_VERSION Table

The `MIGRATION_VERSION` table serves as a **database schema version control system**. Here's what it does:

#### 🎯 Primary Functions:

1. **Schema Version Tracking**
   - Keeps track of which database schema version is currently applied
   - Stores the version number, when it was applied, and a description

2. **Migration State Management**
   - Prevents running the same migration multiple times
   - Ensures migrations are applied in the correct order
   - Allows the system to know what changes have already been made

3. **Deployment Safety**
   - When deploying to different environments (dev, staging, production), the system can automatically determine what migrations need to be run
   - Prevents schema inconsistencies between environments

#### 📊 Table Structure:

```sql
CREATE TABLE migration_version (
    id INTEGER PRIMARY KEY,
    version INTEGER NOT NULL,        -- Schema version number (1, 2, 3, etc.)
    applied_at DATETIME NOT NULL,    -- When this migration was applied
    description TEXT                 -- Human-readable description of changes
)
```

#### 🔄 How It Works:

1. **Initial Setup**: When the app starts for the first time, it creates the table and records version 1 (initial schema)

2. **Version Checking**:

   ```python
   current_version = self.get_db_version()  # Reads MAX(version) from table
   target_version = self.get_target_version()  # What version the app expects
   ```

3. **Migration Application**: If current < target, it applies missing migrations sequentially

4. **Recording**: Each successful migration is recorded in the table

#### 🚀 Real-World Example:

Let's say you want to add a new feature that requires database changes:

**Version 1** (Current):

- User table: id, username, password_hash, created_at
- Todo table: id, description, completed, created_at, user_id

**Version 2** (New Feature - Todo Categories):

- Add `category` column to Todo table
- Add `Category` table

The migration system would:

1. Check current version (1) vs target version (2)
2. Apply migration v2: Add category column and Category table
3. Record in migration_version: `(2, '2024-01-15 10:30:00', 'Added todo categories')`

#### 💡 Benefits:

- **Automated Deployments**: No manual database changes needed
- **Rollback Safety**: You know exactly what version you're on
- **Team Collaboration**: Everyone gets the same database structure
- **Environment Consistency**: Dev, staging, and production stay in sync
- **Audit Trail**: Complete history of database changes

#### 🔍 In Your App:

Currently, your app only has version 1 (initial schema), but the infrastructure is ready for future changes. When you need to modify the database schema, you would:

1. Increment `get_target_version()` to return 2
2. Add a new condition in `apply_migration()` for version 2
3. Deploy - the system automatically applies the new migration

This is a lightweight alternative to more complex migration systems like Alembic (used with Flask-Migrate), but serves the same fundamental purpose of keeping database schemas synchronized and versioned.

#### Migration Flow Diagram

```mermaid
flowchart TD
    START([App Startup]) --> CHECK{Migration Table Exists?}

    CHECK -->|No| CREATE[Create migration_version table]
    CREATE --> RECORD1[Record Version 1 - Initial Schema]
    RECORD1 --> CURRENT

    CHECK -->|Yes| CURRENT[Get Current Version from DB]

    CURRENT --> TARGET[Get Target Version from Code]
    TARGET --> COMPARE{Current < Target?}

    COMPARE -->|No| DONE[✅ Database Up to Date]
    COMPARE -->|Yes| MIGRATE[Apply Missing Migrations]

    MIGRATE --> APPLY[Apply Migration N+1]
    APPLY --> RECORD[Record Migration in Table]
    RECORD --> NEXT{More Migrations?}

    NEXT -->|Yes| APPLY
    NEXT -->|No| DONE

    DONE --> CONTINUE[Continue App Startup]

    classDef success fill:#e8f5e8
    classDef process fill:#e3f2fd
    classDef decision fill:#fff3e0

    class DONE,CONTINUE success
    class CREATE,RECORD1,CURRENT,TARGET,MIGRATE,APPLY,RECORD process
    class CHECK,COMPARE,NEXT decision
```
