#!/usr/bin/env python3
"""Test Playwright setup"""
import sys
from playwright.sync_api import sync_playwright

def main():
    print("Testing Playwright...")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("https://www.instagram.com")

            title = page.title()

            browser.close()

            if title:
                print(f"✓ Playwright working (page title: {title})")
                return 0
            else:
                print("✗ Playwright launched but couldn't get page title")
                return 1

    except Exception as e:
        print(f"✗ Playwright test failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
