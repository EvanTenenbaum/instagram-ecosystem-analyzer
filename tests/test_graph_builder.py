import pytest
from unittest.mock import Mock, patch, MagicMock
import networkx as nx
from pathlib import Path
from src.analyzers.graph_builder import GraphBuilder


def test_graph_builder_init():
    """Test GraphBuilder initializes correctly"""
    config = {
        "target_account": "test_user",
        "analysis": {
            "edge_weights": {
                "follows": 10,
                "replies_to": 9,
                "tags": 8,
                "collaborator": 10,
                "repeated_commenter_base": 7,
                "frequency_bonus": 2,
                "mentioned": 6
            }
        }
    }

    builder = GraphBuilder(config)

    assert builder.config == config
    assert builder.target_account == "test_user"
    assert builder.edge_weights == config["analysis"]["edge_weights"]
    assert builder.raw_data_dir == Path("data/raw")
    assert builder.processed_dir == Path("data/processed")


def test_build_graph_from_empty_data():
    """Test graph building with empty data"""
    config = {
        "target_account": "test_user",
        "analysis": {
            "edge_weights": {
                "follows": 10,
                "replies_to": 9,
                "tags": 8,
                "collaborator": 10,
                "repeated_commenter_base": 7,
                "frequency_bonus": 2,
                "mentioned": 6
            }
        }
    }

    builder = GraphBuilder(config)

    # Empty data list
    G = builder.build_graph([])

    # Should create empty graph
    assert isinstance(G, nx.DiGraph)
    assert len(G.nodes()) == 0
    assert len(G.edges()) == 0


def test_build_graph_with_following():
    """Test graph building with following relationships"""
    config = {
        "target_account": "sarah_myerscough",
        "analysis": {
            "edge_weights": {
                "follows": 10,
                "replies_to": 9,
                "tags": 8,
                "collaborator": 10,
                "repeated_commenter_base": 7,
                "frequency_bonus": 2,
                "mentioned": 6
            }
        }
    }

    builder = GraphBuilder(config)

    # Mock raw data with following relationships
    raw_data = [
        {
            "metadata": {
                "phase": "phase0",
                "target_account": "sarah_myerscough"
            },
            "data": {
                "profile": {
                    "username": "sarah_myerscough",
                    "follower_count": 5000,
                    "following_count": 300,
                    "bio": "Gallery owner"
                }
            }
        },
        {
            "metadata": {
                "phase": "phase2",
                "target_account": "sarah_myerscough"
            },
            "data": {
                "following": [
                    {
                        "username": "artist1",
                        "full_name": "Artist One"
                    },
                    {
                        "username": "artist2",
                        "full_name": "Artist Two"
                    }
                ]
            }
        }
    ]

    G = builder.build_graph(raw_data)

    # Should have target and following accounts
    assert isinstance(G, nx.DiGraph)
    assert "sarah_myerscough" in G.nodes()
    assert "artist1" in G.nodes()
    assert "artist2" in G.nodes()

    # Should have following edges with correct weight
    assert G.has_edge("sarah_myerscough", "artist1")
    assert G.has_edge("sarah_myerscough", "artist2")
    assert G["sarah_myerscough"]["artist1"]["relationship"] == "follows"
    assert G["sarah_myerscough"]["artist1"]["weight"] == 10
