"""Route handlers for the Flask Todo App."""

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import validate_csrf
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

from app.auth import authenticate_user, create_user


def validate_csrf_token():
    """Validate CSRF token, skip in testing when CSRF is disabled."""
    if current_app.config.get("WTF_CSRF_ENABLED", True):
        try:
            validate_csrf(request.form.get("csrf_token"))
            return True
        except Exception:
            flash("Security token validation failed. Please try again.", "error")
            return False
    return True


# Create blueprint for authentication routes
auth = Blueprint("auth", __name__)


class RegistrationForm(FlaskForm):
    """Form for user registration."""

    username = StringField(
        "Username",
        validators=[
            DataRequired(message="Username is required"),
            Length(
                min=3, max=80, message="Username must be between 3 and 80 characters"
            ),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="Password is required"),
            Length(min=6, message="Password must be at least 6 characters long"),
        ],
    )
    password_confirm = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(message="Password confirmation is required"),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    """Form for user login."""

    username = StringField(
        "Username", validators=[DataRequired(message="Username is required")]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(message="Password is required")]
    )
    submit = SubmitField("Login")


@auth.route("/register", methods=["GET", "POST"])
def register():
    """
    Handle user registration.

    GET: Display registration form
    POST: Process registration form submission
    """
    # Redirect authenticated users to main page
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        password_confirm = form.password_confirm.data

        # Create new user account
        user, error = create_user(username, password, password_confirm)

        if user:
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))
        else:
            flash(error, "error")

    return render_template("register.html", form=form)


@auth.route("/login", methods=["GET", "POST"])
def login():
    """
    Handle user login.

    GET: Display login form
    POST: Process login form submission
    """
    # Redirect authenticated users to main page
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = LoginForm()

    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        # Authenticate user
        user = authenticate_user(username, password)

        if user:
            login_user(user)
            flash(f"Welcome back, {user.username}!", "success")

            # Redirect to next page or main page
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("main.index"))
        else:
            flash("Invalid username or password. Please try again.", "error")

    return render_template("login.html", form=form)


@auth.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    Handle user logout.

    POST: End user session and redirect to login page
    """
    username = current_user.username
    logout_user()
    flash(f"You have been logged out, {username}.", "info")
    return redirect(url_for("auth.login"))


# Create blueprint for main application routes
main = Blueprint("main", __name__)


@main.route("/")
@login_required
def index():
    """
    Display the main todo list page (protected route).

    Query only current user's todos from database and handle empty state.
    Unauthenticated users are redirected to login page by @login_required.
    """
    from app.models import Todo

    # Query only current user's todos, ordered by creation date (newest first)
    user_todos = (
        Todo.query.filter_by(user_id=current_user.id)
        .order_by(Todo.created_at.desc())
        .all()
    )

    return render_template("index.html", todos=user_todos)


@main.route("/add", methods=["POST"])
@login_required
def add_todo():
    """
    Create a new todo item (protected route).

    Associate new todos with current user ID and validate input.
    Redirect to main page after successful creation.
    """
    from app import db
    from app.models import Todo

    # Validate CSRF token
    if not validate_csrf_token():
        return redirect(url_for("main.index"))

    # Get todo description from form
    description = request.form.get("description", "").strip()

    # Validate input
    if not description:
        flash("Todo description is required.", "error")
        return redirect(url_for("main.index"))

    try:
        # Create new todo associated with current user
        new_todo = Todo(description=description, user_id=current_user.id)
        db.session.add(new_todo)
        db.session.commit()

        flash("Todo added successfully!", "success")
    except ValueError as e:
        flash(str(e), "error")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while adding the todo. Please try again.", "error")

    return redirect(url_for("main.index"))


@main.route("/toggle/<int:todo_id>", methods=["POST"])
@login_required
def toggle_todo(todo_id):
    """
    Toggle completion status of a todo item (protected route).

    Verify user owns the todo before allowing toggle.
    Handle unauthorized access attempts.
    """
    from app import db
    from app.models import Todo

    # Validate CSRF token
    if not validate_csrf_token():
        return redirect(url_for("main.index"))

    # Find the todo and verify ownership
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()

    if not todo:
        flash("Todo not found or you don't have permission to modify it.", "error")
        return redirect(url_for("main.index"))

    try:
        # Toggle completion status
        todo.toggle_completion()
        db.session.commit()

        status = "completed" if todo.completed else "incomplete"
        flash(f"Todo marked as {status}!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while updating the todo. Please try again.", "error")

    return redirect(url_for("main.index"))


@main.route("/delete/<int:todo_id>", methods=["POST"])
@login_required
def delete_todo(todo_id):
    """
    Delete a todo item (protected route).

    Verify user owns the todo before allowing deletion.
    Handle unauthorized access attempts.
    """
    from app import db
    from app.models import Todo

    # Validate CSRF token
    if not validate_csrf_token():
        return redirect(url_for("main.index"))

    # Find the todo and verify ownership
    todo = Todo.query.filter_by(id=todo_id, user_id=current_user.id).first()

    if not todo:
        flash("Todo not found or you don't have permission to delete it.", "error")
        return redirect(url_for("main.index"))

    try:
        # Delete the todo
        db.session.delete(todo)
        db.session.commit()

        flash("Todo deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while deleting the todo. Please try again.", "error")

    return redirect(url_for("main.index"))
