#!/usr/bin/env python3
"""
Instagram report generation script
"""
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reporters.ai_reporter import AIReporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/reporting.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    try:
        logger.info("Generating reports")
        reporter = AIReporter(config)
        recommendations, summary = reporter.run()

        logger.info("Reports generated!")
        logger.info(f"Recommendations: {len(recommendations)}")
        logger.info("Check outputs/ directory for results")

        return 0

    except Exception as e:
        logger.error(f"Reporting failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
