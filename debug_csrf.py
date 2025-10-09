#!/usr/bin/env python3
"""Debug script to check CSRF token extraction."""

import requests


def test_csrf_extraction():
    """Test CSRF token extraction from registration page."""
    try:
        response = requests.get("http://localhost:5000/register")
        print(f"Status Code: {response.status_code}")
        print(f"Content Length: {len(response.text)}")
        print("\nFirst 2000 characters of response:")
        print("=" * 50)
        print(response.text[:2000])
        print("=" * 50)

        # Look for CSRF token patterns
        import re

        patterns = [
            r'name="csrf_token"[^>]*value="([^"]+)"',
            r'value="([^"]+)"[^>]*name="csrf_token"',
            r'<meta name="csrf-token" content="([^"]+)"',
            r'csrf_token.*?value="([^"]+)"',
        ]

        print("\nCSRF Token Search Results:")
        for i, pattern in enumerate(patterns):
            match = re.search(pattern, response.text, re.IGNORECASE)
            if match:
                print(f"Pattern {i+1}: FOUND - {match.group(1)}")
            else:
                print(f"Pattern {i+1}: NOT FOUND")

        # Look for any hidden input fields
        hidden_inputs = re.findall(
            r'<input[^>]*type="hidden"[^>]*>', response.text, re.IGNORECASE
        )
        print(f"\nHidden input fields found: {len(hidden_inputs)}")
        for inp in hidden_inputs:
            print(f"  {inp}")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_csrf_extraction()
