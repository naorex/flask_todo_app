#!/usr/bin/env python3
"""
Container Testing Script

A simple script to test Docker container functionality manually.
This script builds the container, runs it, and performs basic functionality tests.
"""

import os
import subprocess
import sys
import time

import requests


def run_command(cmd, description):
    """Run a command and return the result"""
    print(f"\n{description}...")
    print(f"Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ {description} - SUCCESS")
        if result.stdout:
            print(f"Output: {result.stdout.strip()}")
    else:
        print(f"❌ {description} - FAILED")
        print(f"Error: {result.stderr.strip()}")
        return False

    return True


def run_container_functionality_test():
    """Test container build and basic functionality"""
    print("🐳 Flask Todo App Container Testing")
    print("=" * 50)

    # Clean up any existing test containers
    print("\n🧹 Cleaning up existing test containers...")
    subprocess.run(["docker", "stop", "flask-todo-test"], capture_output=True)
    subprocess.run(["docker", "rm", "flask-todo-test"], capture_output=True)
    subprocess.run(["docker", "rmi", "flask-todo-app-test"], capture_output=True)

    # Build the container
    if not run_command(
        ["docker", "build", "-t", "flask-todo-app-test", "."],
        "Building Docker container",
    ):
        return False

    # Create instance directory for database persistence
    instance_dir = "./test_instance"
    os.makedirs(instance_dir, exist_ok=True)

    # Run the container
    if not run_command(
        [
            "docker",
            "run",
            "-d",
            "--name",
            "flask-todo-test",
            "-p",
            "5002:5000",
            "-v",
            f"{os.path.abspath(instance_dir)}:/app/instance",
            "-e",
            "SECRET_KEY=test-secret-key-for-container-testing",
            "flask-todo-app-test",
        ],
        "Starting Docker container",
    ):
        return False

    # Wait for container to be ready
    print("\n⏳ Waiting for container to be ready...")
    max_retries = 30
    container_ready = False

    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:5002/login", timeout=5)
            if response.status_code == 200:
                container_ready = True
                print(f"✅ Container ready after {i+1} seconds")
                break
        except requests.exceptions.RequestException:
            pass

        print(f"Waiting... ({i+1}/{max_retries})")
        time.sleep(1)

    if not container_ready:
        print("❌ Container failed to start within timeout")
        return False

    # Test basic functionality
    print("\n🧪 Testing container functionality...")

    try:
        # Test login page
        response = requests.get("http://localhost:5002/login")
        if response.status_code == 200 and "login" in response.text.lower():
            print("✅ Login page accessible")
        else:
            print("❌ Login page test failed")
            return False

        # Test registration page
        response = requests.get("http://localhost:5002/register")
        if response.status_code == 200 and "register" in response.text.lower():
            print("✅ Registration page accessible")
        else:
            print("❌ Registration page test failed")
            return False

        # Test protected route redirect
        response = requests.get("http://localhost:5002/", allow_redirects=False)
        if response.status_code in [302, 401]:
            print("✅ Protected route properly redirects")
        else:
            print("❌ Protected route test failed")
            return False

        # Test database persistence
        if os.path.exists(instance_dir) and os.access(instance_dir, os.W_OK):
            print("✅ Database persistence directory accessible")
        else:
            print("❌ Database persistence test failed")
            return False

    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

    print("\n🎉 All container tests passed!")
    return True


def cleanup():
    """Clean up test containers and images"""
    print("\n🧹 Cleaning up...")
    subprocess.run(["docker", "stop", "flask-todo-test"], capture_output=True)
    subprocess.run(["docker", "rm", "flask-todo-test"], capture_output=True)
    subprocess.run(["docker", "rmi", "flask-todo-app-test"], capture_output=True)

    # Clean up test instance directory
    import shutil

    if os.path.exists("./test_instance"):
        shutil.rmtree("./test_instance", ignore_errors=True)

    print("✅ Cleanup completed")


if __name__ == "__main__":
    try:
        # Check if Docker is available
        result = subprocess.run(["docker", "--version"], capture_output=True)
        if result.returncode != 0:
            print(
                "❌ Docker is not available. Please install Docker to run container tests."
            )
            sys.exit(1)

        success = run_container_functionality_test()

        if success:
            print("\n🎉 Container testing completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Container testing failed!")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    finally:
        cleanup()
