#!/usr/bin/env python3
"""Test target account accessibility"""
import sys
import json
from playwright.sync_api import sync_playwright

def main():
    print("Testing target account...")

    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    target = config['target_account']
    url = f"https://www.instagram.com/{target}/"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=30000)

            title = page.title()

            # Check for "Page Not Found"
            if "Page Not Found" in title or "Sorry" in title:
                print(f"✗ Account @{target} not found or inaccessible")
                browser.close()
                return 1

            # Check for private account
            content = page.content()
            if "This account is private" in content:
                print(f"⚠ Account @{target} is PRIVATE - data collection will be limited")
                browser.close()
                return 0

            browser.close()
            print(f"✓ Account @{target} is accessible and public")
            return 0

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
