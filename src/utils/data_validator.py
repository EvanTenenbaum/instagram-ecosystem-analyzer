import re
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates collected data formats"""

    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9._]{1,30}$')

    def validate_account(self, data):
        """Validate account data structure"""
        errors = []

        # Required fields
        if "username" not in data:
            errors.append("Missing required field: username")
        elif not self.USERNAME_PATTERN.match(data["username"]):
            errors.append(f"Invalid username format: {data['username']}")

        # Optional but validated if present
        if "follower_count" in data and not isinstance(data["follower_count"], (int, type(None))):
            errors.append("follower_count must be integer or None")

        if "following_count" in data and not isinstance(data["following_count"], (int, type(None))):
            errors.append("following_count must be integer or None")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Account validation failed: {errors}")

        return is_valid, errors

    def validate_relationship(self, data):
        """Validate relationship data structure"""
        errors = []

        required_fields = ["source", "target", "type", "weight"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")

        if "weight" in data and not isinstance(data["weight"], (int, float)):
            errors.append("weight must be numeric")

        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Relationship validation failed: {errors}")

        return is_valid, errors

    def validate_json_file(self, filepath):
        """Validate JSON file exists and is parseable"""
        import json
        import os

        if not os.path.exists(filepath):
            return False, [f"File not found: {filepath}"]

        try:
            with open(filepath, 'r') as f:
                json.load(f)
            return True, []
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {str(e)}"]
