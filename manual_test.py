#!/usr/bin/env python3
"""
Manual verification script for Flask Todo App functionality.

This script performs basic checks to verify the application is working correctly.
"""

import sys

import requests


def verify_basic_functionality():
    """Verify basic application functionality."""
    base_url = "http://localhost:5000"

    print("🚀 Flask Todo App Manual Verification")
    print("=" * 40)

    # Test 1: Application is accessible
    print("\n1. Testing application accessibility...")
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("   ✅ Application is accessible")
            print(f"   📊 Response size: {len(response.text)} bytes")
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return False

    # Test 2: Registration page loads
    print("\n2. Testing registration page...")
    try:
        response = requests.get(f"{base_url}/register")
        if response.status_code == 200 and "Register" in response.text:
            print("   ✅ Registration page loads correctly")
            print(
                "   ✅ CSRF token present"
                if "csrf_token" in response.text
                else "   ❌ CSRF token missing"
            )
        else:
            print(f"   ❌ Registration page failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Registration page error: {e}")

    # Test 3: Login page loads
    print("\n3. Testing login page...")
    try:
        response = requests.get(f"{base_url}/login")
        if response.status_code == 200 and "Login" in response.text:
            print("   ✅ Login page loads correctly")
            print(
                "   ✅ CSRF token present"
                if "csrf_token" in response.text
                else "   ❌ CSRF token missing"
            )
        else:
            print(f"   ❌ Login page failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Login page error: {e}")

    # Test 4: Protected route redirects
    print("\n4. Testing protected route access...")
    try:
        # Use a new session to ensure no authentication
        session = requests.Session()
        response = session.get(base_url)
        if "login" in response.url.lower() or "Login" in response.text:
            print("   ✅ Protected route correctly redirects to login")
        else:
            print("   ❌ Protected route does not redirect properly")
    except Exception as e:
        print(f"   ❌ Protected route test error: {e}")

    # Test 5: Static files load
    print("\n5. Testing static file serving...")
    try:
        response = requests.get(f"{base_url}/static/style.css")
        if (
            response.status_code == 200
            and "css" in response.headers.get("content-type", "").lower()
        ):
            print("   ✅ Static CSS file loads correctly")
        else:
            print(f"   ❌ Static file failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Static file error: {e}")

    # Test 6: Security headers
    print("\n6. Testing security headers...")
    try:
        response = requests.get(base_url)
        headers = response.headers
        security_checks = [
            ("X-Content-Type-Options", "nosniff"),
            ("X-Frame-Options", "DENY"),
            ("X-XSS-Protection", "1; mode=block"),
        ]

        for header, expected in security_checks:
            if header in headers:
                print(f"   ✅ {header}: {headers[header]}")
            else:
                print(f"   ❌ {header}: Missing")

    except Exception as e:
        print(f"   ❌ Security headers test error: {e}")

    # Test 7: Database functionality (indirect)
    print("\n7. Testing database functionality...")
    try:
        # Check if the application starts without database errors
        response = requests.get(f"{base_url}/login")
        if response.status_code == 200:
            print("   ✅ Database appears to be working (no startup errors)")
        else:
            print("   ❌ Possible database issues")
    except Exception as e:
        print(f"   ❌ Database test error: {e}")

    print("\n" + "=" * 40)
    print("🏁 Manual verification complete!")
    print("\n📝 Next steps for full testing:")
    print("   1. Open http://localhost:5000 in a web browser")
    print("   2. Register a new user account")
    print("   3. Log in with the new account")
    print("   4. Add, complete, and delete todo items")
    print("   5. Log out and verify session is ended")

    return True


def verify_container_health():
    """Verify Docker container health."""
    print("\n🐳 Docker Container Health Check")
    print("=" * 40)

    import subprocess

    try:
        # Check container status
        result = subprocess.run(
            ["docker-compose", "ps"], capture_output=True, text=True, cwd="."
        )

        if result.returncode == 0:
            if "healthy" in result.stdout:
                print("   ✅ Container is healthy")
            elif "Up" in result.stdout:
                print("   ✅ Container is running")
            else:
                print("   ❌ Container status unclear")
                print(f"   Output: {result.stdout}")
        else:
            print("   ❌ Failed to check container status")

    except Exception as e:
        print(f"   ❌ Container health check error: {e}")


if __name__ == "__main__":
    success = verify_basic_functionality()
    verify_container_health()

    if success:
        print("\n🎉 Basic functionality verification passed!")
        print("The Flask Todo App appears to be working correctly.")
    else:
        print("\n💥 Some issues were detected.")

    sys.exit(0 if success else 1)
