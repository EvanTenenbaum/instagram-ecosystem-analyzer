import json
import logging
from pathlib import Path
import networkx as nx
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


class AccountScorer:
    """Calculate multi-factor scores for Instagram accounts"""

    def __init__(self, config):
        """Initialize with config, scoring_weights, category_keywords"""
        self.config = config
        self.target_account = config["target_account"]
        self.scoring_weights = config["analysis"]["scoring_weights"]
        self.category_keywords = config["analysis"]["category_keywords"]
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def calculate_proximity_score(self, G, account):
        """Score based on shortest path (1 hop = 100, 2 hops = 50, etc.)"""
        if account == self.target_account:
            return 0

        try:
            # Calculate shortest path length
            path_length = nx.shortest_path_length(G, self.target_account, account)
            # Inverse scoring: 1/hops * 100
            score = (1.0 / path_length) * 100

            # Check if path is reverse (account -> target)
            try:
                reverse_path_length = nx.shortest_path_length(G, account, self.target_account)
                # If reverse path exists and is shorter/equal, apply 80% penalty
                if reverse_path_length <= path_length:
                    score = score * 0.8
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                # No reverse path, no penalty
                pass

            return score
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            # No path exists or node not in graph
            return 0

    def calculate_engagement_score(self, G, account):
        """Score based on edge weights (bidirectional)"""
        total_weight = 0

        # Check edge from target to account
        if G.has_edge(self.target_account, account):
            total_weight += G[self.target_account][account].get('weight', 0)

        # Check edge from account to target (bidirectional)
        if G.has_edge(account, self.target_account):
            total_weight += G[account][self.target_account].get('weight', 0)

        # Normalize to 0-100 scale
        score = (total_weight / 30.0) * 100
        # Cap at 100
        score = min(score, 100.0)

        return score

    def calculate_bridge_score(self, G, account):
        """Score based on betweenness centrality"""
        if account == self.target_account:
            return 0

        if account not in G.nodes():
            return 0

        # Calculate betweenness centrality for all nodes
        try:
            centrality = nx.betweenness_centrality(G)
            # Get centrality for this account (0.0 to 1.0)
            account_centrality = centrality.get(account, 0)
            # Normalize to 0-100 scale
            score = account_centrality * 100
            return score
        except Exception as e:
            logger.error(f"Error calculating betweenness centrality for {account}: {e}")
            return 0

    def classify_category(self, account_data):
        """Classify account by bio keywords"""
        bio = account_data.get("bio", "").lower()
        if not bio:
            return ("unknown", 0.0)

        # Define desirable categories in priority order
        desirable_categories = ["gallery", "curator", "wood_artist", "furniture_designer"]

        # Check for keyword matches
        matched_categories = []
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword.lower() in bio:
                    matched_categories.append(category)
                    break  # Move to next category once we find a match

        # Calculate confidence based on number of matches
        if matched_categories:
            confidence = min(len(matched_categories) / len(self.category_keywords), 1.0)
            return (matched_categories[0], confidence)

        return ("unknown", 0.0)

    def score_accounts(self, G):
        """Score all accounts with weighted average"""
        scored_accounts = []

        for node in G.nodes():
            # Skip target account
            if node == self.target_account:
                continue

            # Get node data
            node_data = G.nodes[node]

            # Calculate component scores
            proximity = self.calculate_proximity_score(G, node)
            engagement = self.calculate_engagement_score(G, node)
            bridge = self.calculate_bridge_score(G, node)

            # Classify category
            category, confidence = self.classify_category(node_data)

            # Calculate category fit score (100 if desirable, 0 otherwise)
            desirable_categories = ["gallery", "curator", "wood_artist", "furniture_designer"]
            category_fit = 100 if category in desirable_categories else 0

            # Calculate weighted overall score
            overall_score = (
                proximity * self.scoring_weights["proximity"] +
                engagement * self.scoring_weights["engagement"] +
                bridge * self.scoring_weights["bridge"] +
                category_fit * self.scoring_weights["category_fit"]
            )

            scored_accounts.append({
                "username": node,
                "overall_score": round(overall_score, 2),
                "proximity_score": round(proximity, 2),
                "engagement_score": round(engagement, 2),
                "bridge_score": round(bridge, 2),
                "category_fit_score": category_fit,
                "category": category,
                "bio": node_data.get("bio", ""),
                "follower_count": node_data.get("follower_count", 0),
                "following_count": node_data.get("following_count", 0)
            })

        # Sort by overall score (highest first)
        scored_accounts.sort(key=lambda x: x["overall_score"], reverse=True)

        logger.info(f"Scored {len(scored_accounts)} accounts")
        return scored_accounts

    def save_scores(self, scored_accounts, graph_metrics=None):
        """Save to JSON"""
        timestamp = pd.Timestamp.now().isoformat()
        scores_path = self.processed_dir / f"account_scores_{timestamp}.json"

        output_data = {
            "metadata": {
                "timestamp": timestamp,
                "target_account": self.target_account,
                "total_accounts_scored": len(scored_accounts),
                "scoring_weights": self.scoring_weights
            },
            "scores": scored_accounts
        }

        # Add graph metrics if provided
        if graph_metrics:
            output_data["graph_metrics"] = graph_metrics

        with open(scores_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Saved account scores: {scores_path}")
        return str(scores_path)

    def run(self, graph):
        """Main execution"""
        logger.info("Starting account scoring process")

        if not isinstance(graph, nx.Graph):
            logger.error("Invalid graph object provided")
            return None

        # Score all accounts
        scored_accounts = self.score_accounts(graph)

        # Prepare graph metrics
        graph_metrics = {
            "total_nodes": len(graph.nodes()),
            "total_edges": len(graph.edges()),
            "density": nx.density(graph)
        }

        # Save scores
        scores_file = self.save_scores(scored_accounts, graph_metrics)

        logger.info("Account scoring complete")
        return {
            "scored_accounts": scored_accounts,
            "scores_file": scores_file,
            "graph_metrics": graph_metrics
        }
