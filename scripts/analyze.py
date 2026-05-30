#!/usr/bin/env python3
"""
Instagram data analysis script
"""
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.graph_builder import GraphBuilder
from src.analyzers.account_scorer import AccountScorer
from src.analyzers.community_detector import CommunityDetector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)

    try:
        # Build graph
        logger.info("Building graph from raw data")
        graph_builder = GraphBuilder(config)
        result = graph_builder.run()
        graph = result['graph']

        # Score accounts
        logger.info("Scoring accounts")
        scorer = AccountScorer(config)
        scored_accounts = scorer.run(graph)

        # Detect communities
        logger.info("Detecting communities")
        detector = CommunityDetector(config)
        communities, bridges = detector.run(graph)

        logger.info("Analysis complete!")
        logger.info(f"Total accounts: {len(graph.nodes)}")
        logger.info(f"Total relationships: {len(graph.edges)}")
        logger.info(f"Communities found: {len(communities)}")

        return 0

    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
