import json
import logging
from pathlib import Path
import networkx as nx
from datetime import datetime
from networkx.algorithms import community

logger = logging.getLogger(__name__)


class CommunityDetector:
    """Identify community clusters using Louvain algorithm"""

    def __init__(self, config):
        """Store config, target_account, outputs_dir"""
        self.config = config
        self.target_account = config["target_account"]
        self.outputs_dir = Path("outputs")
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def detect_communities(self, G):
        """Use greedy_modularity_communities, return list of cluster dicts"""
        # Convert to undirected graph for community detection
        G_undirected = G.to_undirected()

        logger.info("Running community detection using greedy modularity algorithm")

        # Use greedy_modularity_communities algorithm
        communities_generator = community.greedy_modularity_communities(G_undirected)

        # Convert to list of sets
        communities_sets = list(communities_generator)

        logger.info(f"Detected {len(communities_sets)} communities")

        # Convert to JSON-serializable format (list of dicts)
        communities = []
        for idx, community_set in enumerate(communities_sets):
            community_dict = {
                "community_id": idx,
                "size": len(community_set),
                "members": sorted(list(community_set))
            }
            communities.append(community_dict)

        # Sort by size (largest first)
        communities.sort(key=lambda x: x["size"], reverse=True)

        # Re-assign community IDs based on size ranking
        for idx, community_dict in enumerate(communities):
            community_dict["community_id"] = idx

        return communities

    def find_bridge_accounts(self, G, communities):
        """Find accounts connecting multiple clusters"""
        # Create a mapping of account -> community_id
        account_to_community = {}
        for community_dict in communities:
            community_id = community_dict["community_id"]
            for member in community_dict["members"]:
                account_to_community[member] = community_id

        bridge_accounts = []

        # Check each account in the graph
        for node in G.nodes():
            if node not in account_to_community:
                continue

            node_community = account_to_community[node]
            connected_communities = set([node_community])

            # Check all neighbors (both in and out edges)
            neighbors = set(G.predecessors(node)) | set(G.successors(node))

            for neighbor in neighbors:
                if neighbor in account_to_community:
                    neighbor_community = account_to_community[neighbor]
                    connected_communities.add(neighbor_community)

            # If connected to multiple communities, it's a bridge account
            if len(connected_communities) > 1:
                bridge_accounts.append({
                    "username": node,
                    "home_community": node_community,
                    "connected_communities": sorted(list(connected_communities)),
                    "bridge_count": len(connected_communities)
                })

        # Sort by bridge_count (highest first)
        bridge_accounts.sort(key=lambda x: x["bridge_count"], reverse=True)

        logger.info(f"Found {len(bridge_accounts)} bridge accounts")

        return bridge_accounts

    def save_communities(self, communities, bridge_accounts):
        """Save to JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        communities_path = self.outputs_dir / f"communities_{timestamp}.json"

        output_data = {
            "metadata": {
                "timestamp": timestamp,
                "target_account": self.target_account,
                "total_communities": len(communities),
                "total_bridge_accounts": len(bridge_accounts)
            },
            "communities": communities,
            "bridge_accounts": bridge_accounts
        }

        with open(communities_path, 'w') as f:
            json.dump(output_data, f, indent=2)

        logger.info(f"Saved community data: {communities_path}")
        return str(communities_path)

    def run(self, graph):
        """Detect, find bridges, save"""
        logger.info("Starting community detection process")

        if not isinstance(graph, nx.Graph):
            logger.error("Invalid graph object provided")
            return None

        # Detect communities
        communities = self.detect_communities(graph)

        # Find bridge accounts
        bridge_accounts = self.find_bridge_accounts(graph, communities)

        # Save results
        communities_file = self.save_communities(communities, bridge_accounts)

        logger.info("Community detection complete")
        return {
            "communities": communities,
            "bridge_accounts": bridge_accounts,
            "communities_file": communities_file,
            "stats": {
                "total_communities": len(communities),
                "total_bridge_accounts": len(bridge_accounts),
                "largest_community_size": communities[0]["size"] if communities else 0
            }
        }
