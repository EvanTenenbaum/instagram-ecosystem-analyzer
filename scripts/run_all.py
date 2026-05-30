#!/usr/bin/env python3
"""
Run complete Instagram ecosystem mapping pipeline
"""
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """Run command and handle errors"""
    logger.info(f"Running: {description}")
    result = subprocess.run(cmd, shell=True)

    if result.returncode != 0:
        logger.error(f"Failed: {description}")
        return False

    logger.info(f"Complete: {description}")
    return True


def main():
    logger.info("="*60)
    logger.info("Instagram Ecosystem Mapping - Full Pipeline")
    logger.info("="*60)

    # Step 1: Collection
    if not run_command("python scripts/collect.py", "Data Collection"):
        logger.error("Collection failed - stopping pipeline")
        return 1

    # Step 2: Analysis
    if not run_command("python scripts/analyze.py", "Data Analysis"):
        logger.error("Analysis failed - stopping pipeline")
        return 1

    # Step 3: Reporting
    if not run_command("python scripts/report.py", "Report Generation"):
        logger.error("Reporting failed - stopping pipeline")
        return 1

    logger.info("="*60)
    logger.info("Pipeline complete!")
    logger.info("Check outputs/ directory for results")
    logger.info("="*60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
