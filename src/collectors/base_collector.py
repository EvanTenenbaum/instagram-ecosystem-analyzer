from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for data collectors"""

    def __init__(self, config):
        self.config = config
        self.target_account = config["target_account"]
        self.raw_data_dir = Path("data/raw")
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    def collect(self):
        """Collect data from source"""
        pass

    def save_progress(self, phase, data):
        """Save collection progress to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{phase}_{timestamp}.json"
        filepath = self.raw_data_dir / filename

        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Progress saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
            return None

    def load_checkpoint(self, phase):
        """Load most recent checkpoint for phase"""
        pattern = f"{phase}_*.json"
        files = sorted(self.raw_data_dir.glob(pattern))

        if not files:
            logger.info(f"No checkpoint found for phase: {phase}")
            return None

        latest = files[-1]
        try:
            with open(latest, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded checkpoint: {latest}")
            return data
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None

    def create_metadata(self, source, phase, authenticated=False):
        """Create collection metadata"""
        return {
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "target_account": self.target_account,
            "phase": phase,
            "authenticated": authenticated
        }
