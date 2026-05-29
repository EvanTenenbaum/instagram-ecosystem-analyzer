import pytest
from src.utils.data_validator import DataValidator


def test_validate_account_data_valid():
    """Test validation of valid account data"""
    data = {
        "username": "test_user",
        "display_name": "Test User",
        "bio": "Test bio",
        "follower_count": 1000,
        "following_count": 500
    }

    validator = DataValidator()
    is_valid, errors = validator.validate_account(data)

    assert is_valid is True
    assert len(errors) == 0


def test_validate_account_data_missing_username():
    """Test validation fails on missing username"""
    data = {
        "display_name": "Test User",
        "bio": "Test bio"
    }

    validator = DataValidator()
    is_valid, errors = validator.validate_account(data)

    assert is_valid is False
    assert "username" in errors[0].lower()


def test_validate_account_data_invalid_username():
    """Test validation fails on invalid username format"""
    data = {
        "username": "invalid@username!",
        "display_name": "Test User"
    }

    validator = DataValidator()
    is_valid, errors = validator.validate_account(data)

    assert is_valid is False
    assert "username" in errors[0].lower()


def test_validate_relationship_valid():
    """Test validation of valid relationship"""
    data = {
        "source": "user1",
        "target": "user2",
        "type": "follows",
        "weight": 10
    }

    validator = DataValidator()
    is_valid, errors = validator.validate_relationship(data)

    assert is_valid is True
    assert len(errors) == 0


def test_validate_relationship_missing_fields():
    """Test validation fails on missing fields"""
    data = {
        "source": "user1"
    }

    validator = DataValidator()
    is_valid, errors = validator.validate_relationship(data)

    assert is_valid is False
    assert len(errors) > 0
