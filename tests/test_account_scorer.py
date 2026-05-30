import pytest
from unittest.mock import Mock, patch, MagicMock
import networkx as nx
from pathlib import Path
import json
from src.analyzers.account_scorer import AccountScorer


def test_account_scorer_init():
    """Test AccountScorer initializes correctly"""
    config = {
        "target_account": "test_user",
        "analysis": {
            "scoring_weights": {
                "proximity": 0.4,
                "engagement": 0.3,
                "bridge": 0.2,
                "category_fit": 0.1
            },
            "category_keywords": {
                "gallery": ["gallery", "art space"],
                "curator": ["curator", "curating"],
                "wood_artist": ["wood", "woodwork"]
            }
        }
    }

    scorer = AccountScorer(config)

    assert scorer.config == config
    assert scorer.target_account == "test_user"
    assert scorer.scoring_weights == config["analysis"]["scoring_weights"]
    assert scorer.scoring_weights["proximity"] == 0.4
    assert scorer.category_keywords == config["analysis"]["category_keywords"]
    assert scorer.processed_dir == Path("data/processed")


def test_calculate_proximity_score():
    """Test proximity scoring based on path length"""
    config = {
        "target_account": "sarah_myerscough",
        "analysis": {
            "scoring_weights": {
                "proximity": 0.4,
                "engagement": 0.3,
                "bridge": 0.2,
                "category_fit": 0.1
            },
            "category_keywords": {}
        }
    }

    scorer = AccountScorer(config)

    # Create a simple graph with paths of different lengths
    G = nx.DiGraph()
    G.add_node("sarah_myerscough")
    G.add_node("artist1")  # 1 hop away
    G.add_node("artist2")  # 2 hops away
    G.add_node("artist3")  # unreachable

    # 1 hop path
    G.add_edge("sarah_myerscough", "artist1")

    # 2 hop path
    G.add_edge("sarah_myerscough", "intermediate")
    G.add_edge("intermediate", "artist2")

    # Test 1 hop = 100 points
    score1 = scorer.calculate_proximity_score(G, "artist1")
    assert score1 == 100

    # Test 2 hops = 50 points (1/2 * 100)
    score2 = scorer.calculate_proximity_score(G, "artist2")
    assert score2 == 50

    # Test unreachable = 0 points
    score3 = scorer.calculate_proximity_score(G, "artist3")
    assert score3 == 0

    # Test target account itself = 0 points
    score_target = scorer.calculate_proximity_score(G, "sarah_myerscough")
    assert score_target == 0


def test_calculate_engagement_score():
    """Test engagement scoring based on edge weights"""
    config = {
        "target_account": "sarah_myerscough",
        "analysis": {
            "scoring_weights": {
                "proximity": 0.4,
                "engagement": 0.3,
                "bridge": 0.2,
                "category_fit": 0.1
            },
            "category_keywords": {}
        }
    }

    scorer = AccountScorer(config)

    # Create a graph with weighted edges
    G = nx.DiGraph()
    G.add_node("sarah_myerscough")
    G.add_node("artist1")
    G.add_node("artist2")

    # Bidirectional edges with weights
    # artist1: target follows (10) + artist1 comments back (7) = 17
    # Normalized: (17 / 30.0) * 100 = 56.67
    G.add_edge("sarah_myerscough", "artist1", weight=10)
    G.add_edge("artist1", "sarah_myerscough", weight=7)

    # artist2: only unidirectional (target follows) = 10
    # Normalized: (10 / 30.0) * 100 = 33.33
    G.add_edge("sarah_myerscough", "artist2", weight=10)

    # Test bidirectional engagement
    score1 = scorer.calculate_engagement_score(G, "artist1")
    assert round(score1, 2) == 56.67

    # Test unidirectional engagement
    score2 = scorer.calculate_engagement_score(G, "artist2")
    assert round(score2, 2) == 33.33

    # Test account with no edges
    G.add_node("artist3")
    score3 = scorer.calculate_engagement_score(G, "artist3")
    assert score3 == 0
