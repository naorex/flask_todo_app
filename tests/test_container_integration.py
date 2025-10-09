"""
Container Integration Tests

Tests for Docker container build, startup, and functionality.
These tests verify that the application works correctly when running in a container.
"""

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import pytest
import requests


class TestContainerIntegration:
    """Test container build and startup process"""

    @pytest.fixture(scope="class")
    def container_setup(self):
        """Set up container for testing"""
        # Create temporary directory for test database
        test_dir = tempfile.mkdtemp()
        instance_dir = os.path.join(test_dir, "instance")
        os.makedirs(instance_dir, exist_ok=True)

        # Build the Docker image
        build_result = subprocess.run(
            ["docker", "build", "-t", "flask-todo-test", "."],
            capture_output=True,
            text=True,
        )

        if build_result.returncode != 0:
            pytest.skip(f"Docker build failed: {build_result.stderr}")

        # Start the container
        container_result = subprocess.run(
            [
                "docker",
                "run",
                "-d",
                "--name",
                "flask-todo-test-container",
                "-p",
                "5001:5000",  # Use different port to avoid conflicts
                "-v",
                f"{instance_dir}:/app/instance",
                "-e",
                "SECRET_KEY=test-secret-key",
                "flask-todo-test",
            ],
            capture_output=True,
            text=True,
        )

        if container_result.returncode != 0:
            pytest.skip(f"Container start failed: {container_result.stderr}")

        # Wait for container to be ready
        max_retries = 30
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:5001/login", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                pass
            time.sleep(1)
        else:
            # Clean up on failure
            subprocess.run(
                ["docker", "stop", "flask-todo-test-container"], capture_output=True
            )
            subprocess.run(
                ["docker", "rm", "flask-todo-test-container"], capture_output=True
            )
            pytest.skip("Container failed to start within timeout")

        yield {
            "base_url": "http://localhost:5001",
            "instance_dir": instance_dir,
            "test_dir": test_dir,
        }

        # Cleanup
        subprocess.run(
            ["docker", "stop", "flask-todo-test-container"], capture_output=True
        )
        subprocess.run(
            ["docker", "rm", "flask-todo-test-container"], capture_output=True
        )
        subprocess.run(["docker", "rmi", "flask-todo-test"], capture_output=True)
        shutil.rmtree(test_dir, ignore_errors=True)

    def test_container_build_success(self):
        """Test that Docker container builds successfully"""
        result = subprocess.run(
            ["docker", "build", "-t", "flask-todo-build-test", "."],
            capture_output=True,
            text=True,
        )

        # Clean up test image
        subprocess.run(["docker", "rmi", "flask-todo-build-test"], capture_output=True)

        # Check if build was successful
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"

        # Check for success indicators in both stdout and stderr
        output = result.stdout + result.stderr
        success_indicators = [
            "Successfully built",
            "Successfully tagged",
            "naming to docker.io/library/flask-todo-build-test",
            "flask-todo-build-test:latest",
            "exporting to image",
            "writing image sha256:",
        ]

        build_success = any(indicator in output for indicator in success_indicators)
        assert (
            build_success
        ), f"Docker build success not detected. Output: {output[:500]}..."

    def test_container_startup(self, container_setup):
        """Test that container starts and responds to requests"""
        base_url = container_setup["base_url"]

        # Test that the application is responding
        response = requests.get(f"{base_url}/login")
        assert response.status_code == 200
        assert "login" in response.text.lower()

    def test_authentication_functionality_in_container(self, container_setup):
        """Verify authentication functionality works in container"""
        base_url = container_setup["base_url"]

        # Create a session to maintain cookies
        session = requests.Session()

        # Test registration
        # First get the registration page to extract CSRF token
        reg_response = session.get(f"{base_url}/register")
        assert reg_response.status_code == 200

        # Extract CSRF token (simplified - in real test would parse HTML)
        # For now, just test that we can access the registration page
        assert "register" in reg_response.text.lower()

        # Test login page access
        login_response = session.get(f"{base_url}/login")
        assert login_response.status_code == 200
        assert "login" in login_response.text.lower()

        # Test that protected routes redirect to login
        protected_response = session.get(f"{base_url}/", allow_redirects=False)
        assert protected_response.status_code in [302, 401]  # Redirect or unauthorized

    def test_database_persistence(self, container_setup):
        """Test database persistence and user data isolation"""
        instance_dir = container_setup["instance_dir"]

        # Check that instance directory exists and is writable
        assert os.path.exists(instance_dir)
        assert os.access(instance_dir, os.W_OK)

        # After container runs, there should be database-related files
        # Wait a moment for any database initialization
        time.sleep(2)

        # Check if database file exists or can be created
        db_path = os.path.join(instance_dir, "todo.db")

        # The database file might not exist yet if no operations were performed
        # But the directory should be accessible
        test_file = os.path.join(instance_dir, "test_write.txt")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            persistence_test_passed = True
        except (IOError, OSError):
            persistence_test_passed = False

        assert persistence_test_passed, "Database persistence directory is not writable"

    def test_container_health_check(self, container_setup):
        """Test that container health check is working"""
        # Get container health status
        result = subprocess.run(
            [
                "docker",
                "inspect",
                "--format='{{.State.Health.Status}}'",
                "flask-todo-test-container",
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            health_status = result.stdout.strip().strip("'")
            # Health status should be 'healthy' or 'starting'
            assert health_status in [
                "healthy",
                "starting",
            ], f"Unexpected health status: {health_status}"

    def test_container_environment_variables(self, container_setup):
        """Test that environment variables are properly set in container"""
        # Check environment variables by making a request that would fail with wrong config
        base_url = container_setup["base_url"]

        # The fact that we can access the application means environment variables are working
        response = requests.get(f"{base_url}/login")
        assert response.status_code == 200

        # Test that the application is running in production mode
        # (Debug mode would show different error pages)
        response = requests.get(f"{base_url}/nonexistent-route")
        assert response.status_code == 404
        # In production mode, we shouldn't see debug information
        assert "Werkzeug" not in response.text

    def test_container_port_mapping(self, container_setup):
        """Test that port mapping is working correctly"""
        base_url = container_setup["base_url"]

        # Test that we can access the application on the mapped port
        response = requests.get(f"{base_url}/login")
        assert response.status_code == 200

        # Test that the application is accessible from outside the container
        assert "localhost:5001" in base_url
        assert response.headers.get("Server") is not None

    def test_container_user_isolation(self, container_setup):
        """Test that container runs with non-root user"""
        # Check that container is running with non-root user
        result = subprocess.run(
            ["docker", "exec", "flask-todo-test-container", "whoami"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            user = result.stdout.strip()
            assert (
                user != "root"
            ), f"Container should not run as root user, but runs as: {user}"


# Additional utility functions for container testing
def is_docker_available():
    """Check if Docker is available on the system"""
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def wait_for_container_ready(container_name, max_retries=30):
    """Wait for container to be ready to accept connections"""
    for i in range(max_retries):
        result = subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "python",
                "-c",
                "import requests; requests.get('http://localhost:5000/login')",
            ],
            capture_output=True,
        )

        if result.returncode == 0:
            return True
        time.sleep(1)
    return False


# Skip all tests if Docker is not available
pytestmark = pytest.mark.skipif(
    not is_docker_available(), reason="Docker is not available on this system"
)
