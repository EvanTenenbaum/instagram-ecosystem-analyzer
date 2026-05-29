import pytest
from unittest.mock import Mock, patch, MagicMock
from src.collectors.playwright_collector import PlaywrightCollector


def test_build_profile_url():
    """Test that profile URLs are built correctly"""
    config = {
        "target_account": "test_user",
        "rate_limiting": {
            "min_delay_seconds": 1,
            "max_delay_seconds": 2
        },
        "authentication": {
            "session_cookie_file": "test_session.json"
        }
    }
    collector = PlaywrightCollector(config)

    assert collector.build_profile_url("test_user") == "https://www.instagram.com/test_user/"
    assert collector.build_profile_url("another_user") == "https://www.instagram.com/another_user/"


def test_extract_profile_data():
    """Test profile data extraction from mock page"""
    config = {
        "target_account": "test_user",
        "rate_limiting": {
            "min_delay_seconds": 1,
            "max_delay_seconds": 2
        },
        "authentication": {
            "session_cookie_file": "test_session.json"
        }
    }
    collector = PlaywrightCollector(config)

    # Mock page object with locator methods
    mock_page = Mock()

    # Mock profile header element
    mock_header = Mock()
    mock_header_first = Mock()
    mock_header_first.text_content.return_value = "test_user\n1,234 posts\n5,678 followers\n910 following"
    mock_header.first = mock_header_first

    mock_page.locator.return_value = mock_header

    # Mock bio
    mock_bio = Mock()
    mock_bio.text_content.return_value = "Test bio\ntest.com"
    mock_page.query_selector.return_value = mock_bio

    # Mock profile pic
    mock_img = Mock()
    mock_img.get_attribute.return_value = "https://example.com/profile.jpg"
    mock_page.query_selector_all.return_value = [mock_img]

    data = collector.extract_profile_data(mock_page, "test_user")

    assert data["username"] == "test_user"
    assert "follower_count" in data
    assert "following_count" in data
    assert "post_count" in data
    assert "bio" in data
    assert "profile_pic_url" in data
