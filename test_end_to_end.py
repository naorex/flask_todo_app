#!/usr/bin/env python3
"""
End-to-end integration test for Flask Todo App.

This script tests the complete authentication flow and todo CRUD operations
to verify that all components are working together correctly.
"""

import sys
import time
from urllib.parse import urljoin

import requests


class TodoAppTester:
    """End-to-end tester for the Flask Todo App."""

    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_username = f"testuser_{int(time.time())}"
        self.test_password = "testpass123"

    def test_application_health(self):
        """Test that the application is running and accessible."""
        print("🔍 Testing application health...")
        try:
            response = self.session.get(self.base_url, timeout=10)
            if response.status_code == 200:
                print("✅ Application is accessible")
                return True
            else:
                print(f"❌ Application returned status code: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to connect to application: {e}")
            return False

    def test_registration_flow(self):
        """Test user registration functionality."""
        print(f"🔍 Testing user registration for '{self.test_username}'...")

        # Get registration page
        reg_url = urljoin(self.base_url, "/register")
        response = self.session.get(reg_url)
        if response.status_code != 200:
            print(f"❌ Failed to access registration page: {response.status_code}")
            return False

        # Extract CSRF token
        csrf_token = self._extract_csrf_token(response.text)
        if not csrf_token:
            print("❌ Failed to extract CSRF token from registration page")
            return False

        # Submit registration form
        reg_data = {
            "username": self.test_username,
            "password": self.test_password,
            "password_confirm": self.test_password,
            "csrf_token": csrf_token,
            "submit": "Register",
        }

        response = self.session.post(reg_url, data=reg_data)
        if response.status_code == 200 and "Registration successful" in response.text:
            print("✅ User registration successful")
            return True
        elif "Username already exists" in response.text:
            print("⚠️  Username already exists, continuing with login test")
            return True
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"Response content: {response.text[:500]}...")
            return False

    def test_login_flow(self):
        """Test user login functionality."""
        print(f"🔍 Testing user login for '{self.test_username}'...")

        # Get login page
        login_url = urljoin(self.base_url, "/login")
        response = self.session.get(login_url)
        if response.status_code != 200:
            print(f"❌ Failed to access login page: {response.status_code}")
            return False

        # Extract CSRF token
        csrf_token = self._extract_csrf_token(response.text)
        if not csrf_token:
            print("❌ Failed to extract CSRF token from login page")
            return False

        # Submit login form
        login_data = {
            "username": self.test_username,
            "password": self.test_password,
            "csrf_token": csrf_token,
            "submit": "Login",
        }

        response = self.session.post(login_url, data=login_data)
        if (
            response.status_code == 200
            and f"Welcome back, {self.test_username}" in response.text
        ):
            print("✅ User login successful")
            return True
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response content: {response.text[:500]}...")
            return False

    def test_todo_crud_operations(self):
        """Test todo CRUD (Create, Read, Update, Delete) operations."""
        print("🔍 Testing todo CRUD operations...")

        # Test adding a todo
        if not self._test_add_todo():
            return False

        # Test viewing todos
        if not self._test_view_todos():
            return False

        # Test toggling todo completion
        if not self._test_toggle_todo():
            return False

        # Test deleting todo
        if not self._test_delete_todo():
            return False

        print("✅ All todo CRUD operations successful")
        return True

    def _test_add_todo(self):
        """Test adding a new todo."""
        print("  🔍 Testing add todo...")

        # Get main page to extract CSRF token
        response = self.session.get(self.base_url)
        if response.status_code != 200:
            print(f"  ❌ Failed to access main page: {response.status_code}")
            return False

        csrf_token = self._extract_csrf_token(response.text)
        if not csrf_token:
            print("  ❌ Failed to extract CSRF token from main page")
            return False

        # Add a todo
        add_url = urljoin(self.base_url, "/add")
        todo_data = {
            "description": "Test todo item for end-to-end testing",
            "csrf_token": csrf_token,
        }

        response = self.session.post(add_url, data=todo_data)
        if response.status_code == 200 and "Todo added successfully" in response.text:
            print("  ✅ Add todo successful")
            return True
        else:
            print(f"  ❌ Add todo failed: {response.status_code}")
            return False

    def _test_view_todos(self):
        """Test viewing todos on the main page."""
        print("  🔍 Testing view todos...")

        response = self.session.get(self.base_url)
        if response.status_code != 200:
            print(f"  ❌ Failed to access main page: {response.status_code}")
            return False

        if "Test todo item for end-to-end testing" in response.text:
            print("  ✅ View todos successful")
            return True
        else:
            print("  ❌ Todo not found on main page")
            return False

    def _test_toggle_todo(self):
        """Test toggling todo completion status."""
        print("  🔍 Testing toggle todo...")

        # Get main page to find todo ID
        response = self.session.get(self.base_url)
        if response.status_code != 200:
            print(f"  ❌ Failed to access main page: {response.status_code}")
            return False

        # Extract todo ID and CSRF token
        todo_id = self._extract_todo_id(response.text)
        csrf_token = self._extract_csrf_token(response.text)

        if not todo_id or not csrf_token:
            print("  ❌ Failed to extract todo ID or CSRF token")
            return False

        # Toggle todo completion
        toggle_url = urljoin(self.base_url, f"/toggle/{todo_id}")
        toggle_data = {"csrf_token": csrf_token}

        response = self.session.post(toggle_url, data=toggle_data)
        if response.status_code == 200 and (
            "marked as completed" in response.text
            or "marked as incomplete" in response.text
        ):
            print("  ✅ Toggle todo successful")
            return True
        else:
            print(f"  ❌ Toggle todo failed: {response.status_code}")
            return False

    def _test_delete_todo(self):
        """Test deleting a todo."""
        print("  🔍 Testing delete todo...")

        # Get main page to find todo ID
        response = self.session.get(self.base_url)
        if response.status_code != 200:
            print(f"  ❌ Failed to access main page: {response.status_code}")
            return False

        # Extract todo ID and CSRF token
        todo_id = self._extract_todo_id(response.text)
        csrf_token = self._extract_csrf_token(response.text)

        if not todo_id or not csrf_token:
            print("  ❌ Failed to extract todo ID or CSRF token")
            return False

        # Delete todo
        delete_url = urljoin(self.base_url, f"/delete/{todo_id}")
        delete_data = {"csrf_token": csrf_token}

        response = self.session.post(delete_url, data=delete_data)
        if response.status_code == 200 and "Todo deleted successfully" in response.text:
            print("  ✅ Delete todo successful")
            return True
        else:
            print(f"  ❌ Delete todo failed: {response.status_code}")
            return False

    def test_logout_flow(self):
        """Test user logout functionality."""
        print("🔍 Testing user logout...")

        # Get main page to extract CSRF token
        response = self.session.get(self.base_url)
        if response.status_code != 200:
            print(f"❌ Failed to access main page: {response.status_code}")
            return False

        csrf_token = self._extract_csrf_token(response.text)
        if not csrf_token:
            print("❌ Failed to extract CSRF token from main page")
            return False

        # Submit logout form
        logout_url = urljoin(self.base_url, "/logout")
        logout_data = {"csrf_token": csrf_token}

        response = self.session.post(logout_url, data=logout_data)
        if (
            response.status_code == 200
            and f"You have been logged out, {self.test_username}" in response.text
        ):
            print("✅ User logout successful")
            return True
        else:
            print(f"❌ Logout failed: {response.status_code}")
            return False

    def test_authorization_protection(self):
        """Test that protected routes require authentication."""
        print("🔍 Testing authorization protection...")

        # Create a new session (not authenticated)
        unauth_session = requests.Session()

        # Test accessing protected main page
        response = unauth_session.get(self.base_url)
        if (
            response.status_code == 200
            and "Login" in response.text
            and "Please log in" in response.text
        ):
            print("✅ Protected route correctly redirects to login")
            return True
        else:
            print(f"❌ Protected route authorization failed: {response.status_code}")
            return False

    def _extract_csrf_token(self, html_content):
        """Extract CSRF token from HTML content."""
        import re

        # Try multiple patterns to find CSRF token
        patterns = [
            r'name="csrf_token"[^>]*value="([^"]+)"',
            r'value="([^"]+)"[^>]*name="csrf_token"',
            r'<meta name="csrf-token" content="([^"]+)"',
            r'csrf_token.*?value="([^"]+)"',
        ]

        for pattern in patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                return match.group(1)

        # If no token found, print debug info
        print(f"  🔍 Debug: Looking for CSRF token in HTML content (first 1000 chars):")
        print(f"  {html_content[:1000]}...")
        return None

    def _extract_todo_id(self, html_content):
        """Extract todo ID from HTML content."""
        import re

        match = re.search(r"/toggle/(\d+)", html_content)
        return match.group(1) if match else None

    def run_all_tests(self):
        """Run all end-to-end tests."""
        print("🚀 Starting Flask Todo App End-to-End Tests")
        print("=" * 50)

        tests = [
            ("Application Health", self.test_application_health),
            ("User Registration", self.test_registration_flow),
            ("User Login", self.test_login_flow),
            ("Todo CRUD Operations", self.test_todo_crud_operations),
            ("User Logout", self.test_logout_flow),
            ("Authorization Protection", self.test_authorization_protection),
        ]

        passed = 0
        failed = 0

        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ Test '{test_name}' failed with exception: {e}")
                failed += 1

        print("\n" + "=" * 50)
        print(f"🏁 Test Results: {passed} passed, {failed} failed")

        if failed == 0:
            print("🎉 All tests passed! The Flask Todo App is working correctly.")
            return True
        else:
            print("💥 Some tests failed. Please check the application.")
            return False


def main():
    """Main function to run the end-to-end tests."""
    import argparse

    parser = argparse.ArgumentParser(description="End-to-end tests for Flask Todo App")
    parser.add_argument(
        "--url",
        default="http://localhost:5000",
        help="Base URL of the Flask Todo App (default: http://localhost:5000)",
    )
    parser.add_argument(
        "--wait",
        type=int,
        default=5,
        help="Seconds to wait for application startup (default: 5)",
    )

    args = parser.parse_args()

    # Wait for application to be ready
    if args.wait > 0:
        print(f"⏳ Waiting {args.wait} seconds for application to be ready...")
        time.sleep(args.wait)

    # Run tests
    tester = TodoAppTester(args.url)
    success = tester.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
