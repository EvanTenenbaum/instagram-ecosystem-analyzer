#!/usr/bin/env python3
"""Test Instagram connectivity"""
import sys
import requests

def main():
    print("Testing Instagram connectivity...")

    try:
        response = requests.get("https://www.instagram.com", timeout=10)

        if response.status_code == 200:
            print("✓ Instagram is accessible")
            return 0
        else:
            print(f"✗ Instagram returned status {response.status_code}")
            return 1

    except requests.RequestException as e:
        print(f"✗ Connection failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
