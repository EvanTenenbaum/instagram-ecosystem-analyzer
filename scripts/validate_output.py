#!/usr/bin/env python3
"""Validate output file formats"""
import sys
import json
from pathlib import Path
import pandas as pd

def validate_file_exists(filepath, name):
    """Check if file exists"""
    if not filepath.exists():
        print(f"✗ Missing: {name} ({filepath})")
        return False
    print(f"✓ Found: {name}")
    return True


def validate_csv_schema(filepath, required_columns, name):
    """Validate CSV has required columns"""
    try:
        df = pd.read_csv(filepath)
        missing = set(required_columns) - set(df.columns)

        if missing:
            print(f"✗ {name} missing columns: {missing}")
            return False

        print(f"✓ {name} schema valid ({len(df)} rows)")
        return True

    except Exception as e:
        print(f"✗ {name} validation failed: {e}")
        return False


def validate_json_structure(filepath, required_keys, name):
    """Validate JSON has required keys"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)

        missing = set(required_keys) - set(data.keys())

        if missing:
            print(f"✗ {name} missing keys: {missing}")
            return False

        print(f"✓ {name} structure valid")
        return True

    except Exception as e:
        print(f"✗ {name} validation failed: {e}")
        return False


def main():
    print("Validating outputs...")
    print("="*60)

    outputs_dir = Path("outputs")
    processed_dir = Path("data/processed")

    all_valid = True

    # Check processed files
    print("\nProcessed Data:")
    all_valid &= validate_file_exists(processed_dir / "accounts.csv", "accounts.csv")
    all_valid &= validate_csv_schema(
        processed_dir / "accounts.csv",
        ["username", "display_name", "bio", "degree"],
        "accounts.csv"
    )

    all_valid &= validate_file_exists(processed_dir / "relationships.csv", "relationships.csv")
    all_valid &= validate_csv_schema(
        processed_dir / "relationships.csv",
        ["source", "target", "weight", "types"],
        "relationships.csv"
    )

    # Check output files
    print("\nOutput Files:")
    all_valid &= validate_file_exists(outputs_dir / "scores.json", "scores.json")
    all_valid &= validate_json_structure(
        outputs_dir / "scores.json",
        ["scoring_metadata", "ranked_accounts"],
        "scores.json"
    )

    all_valid &= validate_file_exists(outputs_dir / "recommended_targets.csv", "recommended_targets.csv")
    all_valid &= validate_csv_schema(
        outputs_dir / "recommended_targets.csv",
        ["username", "category", "overall_score", "recommendation_tier"],
        "recommended_targets.csv"
    )

    all_valid &= validate_file_exists(outputs_dir / "ai_summary.md", "ai_summary.md")

    print("="*60)
    if all_valid:
        print("✓ All validations passed")
        return 0
    else:
        print("✗ Some validations failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
