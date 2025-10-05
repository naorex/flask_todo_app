"""Route handlers for the Flask Todo App."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_wtf import FlaskForm
from flask_wtf.csrf import validate_csrf
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length

from app.auth import authenticate_user, create_user

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

    This is a placeholder that will be implemented in task 4.1
    """
    return render_template("index.html", todos=[])
