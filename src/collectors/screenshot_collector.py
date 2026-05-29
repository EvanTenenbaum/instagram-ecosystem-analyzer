import logging
import re
from pathlib import Path
from PIL import Image
import pytesseract
from src.collectors.base_collector import BaseCollector

logger = logging.getLogger(__name__)


class ScreenshotCollector(BaseCollector):
    """OCR-based screenshot collector for manual fallback"""

    def __init__(self, config):
        super().__init__(config)
        self.screenshot_dir = Path("data/manual/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.confidence_threshold = config["ocr"]["confidence_threshold"]
        self.username_pattern = re.compile(config["ocr"]["username_pattern"])

    def collect(self):
        """Collect usernames from screenshots using OCR"""
        logger.info("Starting screenshot OCR collection")

        # Find all image files
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            image_files.extend(self.screenshot_dir.glob(ext))

        if not image_files:
            logger.warning(f"No screenshots found in {self.screenshot_dir}")
            return None

        logger.info(f"Found {len(image_files)} screenshots to process")

        discovered_accounts = set()
        low_confidence_files = []

        # Process each screenshot
        for image_path in image_files:
            logger.info(f"Processing: {image_path.name}")
            usernames, confidence = self.extract_usernames_from_image(image_path)

            if confidence < self.confidence_threshold:
                low_confidence_files.append({
                    "file": image_path.name,
                    "confidence": confidence
                })
                logger.warning(f"Low confidence ({confidence:.2f}) for {image_path.name}")

            discovered_accounts.update(usernames)
            logger.info(f"Extracted {len(usernames)} usernames from {image_path.name}")

        # Build output data
        data = {
            "metadata": self.create_metadata(
                source="screenshot_ocr",
                phase="screenshot_ocr",
                authenticated=False
            ),
            "discovered_accounts": list(discovered_accounts),
            "total_screenshots": len(image_files),
            "total_accounts": len(discovered_accounts),
            "low_confidence_files": low_confidence_files
        }

        # Save progress
        self.save_progress("screenshot_ocr", data)

        logger.info(f"Screenshot OCR complete: {len(discovered_accounts)} unique accounts found")
        return data

    def extract_usernames_from_image(self, image_path):
        """Extract Instagram usernames from image using OCR"""
        try:
            # Open and convert image to grayscale
            image = Image.open(image_path)
            image = image.convert('L')

            # Run OCR with optimized settings
            ocr_data = pytesseract.image_to_data(
                image,
                config='--oem 3 --psm 6',
                output_type=pytesseract.Output.DICT
            )

            # Extract text and confidence scores
            usernames = []
            confidences = []

            for i, text in enumerate(ocr_data['text']):
                if text.strip():
                    # Find username patterns
                    matches = self.username_pattern.findall(text)
                    for match in matches:
                        if self.is_valid_username(match):
                            usernames.append(match)
                            confidences.append(ocr_data['conf'][i])

            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            avg_confidence = avg_confidence / 100.0  # Normalize to 0-1

            return (usernames, avg_confidence)

        except Exception as e:
            logger.error(f"OCR failed for {image_path.name}: {e}")
            return ([], 0.0)

    def is_valid_username(self, username):
        """Validate Instagram username format and filter OCR errors"""
        # Check basic format
        if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
            return False

        # Filter common OCR errors
        # Only digits
        if username.isdigit():
            return False

        # Only punctuation
        if all(c in '._' for c in username):
            return False

        # Contains common OCR noise
        if any(noise in username.lower() for noise in ['http', 'www']):
            return False

        return True
