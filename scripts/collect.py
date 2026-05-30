#!/usr/bin/env python3
"""
Instagram data collection script
"""
import sys
import json
import logging
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.playwright_collector import PlaywrightCollector
from src.collectors.screenshot_collector import ScreenshotCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Collect Instagram data')
    parser.add_argument('--limit', type=int, help='Limit posts collected (for testing)')
    parser.add_argument('--ocr-only', action='store_true', help='Only run OCR on screenshots')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')

    args = parser.parse_args()

    # Load config
    config_file = Path('config.json')
    if not config_file.exists():
        logger.error("config.json not found")
        return 1

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Apply limit if specified
    if args.limit:
        config['collection']['max_posts'] = args.limit

    try:
        if args.ocr_only:
            # Run OCR collector only
            logger.info("Running OCR collector on screenshots")
            collector = ScreenshotCollector(config)
            collector.collect()
        else:
            # Run Playwright collector
            logger.info("Running Playwright collector")
            collector = PlaywrightCollector(config)
            collector.collect()

        logger.info("Collection complete!")
        return 0

    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
