import json
import logging
from pathlib import Path
import networkx as nx
from datetime import datetime
import csv

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Build NetworkX graph from collected Instagram data"""

    def __init__(self, config):
        """Initialize with config, extract edge_weights, set up directories"""
        self.config = config
        self.target_account = config["target_account"]
        self.edge_weights = config["analysis"]["edge_weights"]
        self.raw_data_dir = Path("data/raw")
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    def load_all_raw_data(self):
        """Load all JSON files from raw data directory"""
        raw_data_list = []

        if not self.raw_data_dir.exists():
            logger.warning(f"Raw data directory does not exist: {self.raw_data_dir}")
            return raw_data_list

        # Load all JSON files from raw data directory
        for json_file in sorted(self.raw_data_dir.glob("*.json")):
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                    raw_data_list.append(data)
                    logger.info(f"Loaded: {json_file}")
            except Exception as e:
                logger.error(f"Failed to load {json_file}: {e}")

        return raw_data_list

    def build_graph(self, raw_data_list):
        """Main graph building logic, process all phases"""
        G = nx.DiGraph()
        accounts = {}  # username -> profile data
        relationships = []  # List of (source, target, relationship_type, metadata)

        # Process data by phase
        for data in raw_data_list:
            metadata = data.get("metadata", {})
            phase = metadata.get("phase", "")

            if phase == "phase0":
                # Target profile
                self.process_target_profile(data, G, accounts)
            elif phase == "phase1":
                # Posts (tags, commenters, collaborators)
                self.process_posts(data, G, accounts, relationships)
            elif phase == "phase2":
                # Following list
                self.process_following(data, G, accounts, relationships)
            elif phase == "phase3":
                # First-degree account full profiles
                self.process_first_degree_accounts(data, G, accounts)

        # Add all relationship edges to graph
        for source, target, rel_type, metadata in relationships:
            if not G.has_edge(source, target):
                weight = self._get_edge_weight(rel_type, metadata)
                G.add_edge(source, target, relationship=rel_type, weight=weight, **metadata)
            else:
                # Edge exists, aggregate weights and relationship types
                existing_weight = G[source][target].get('weight', 0)
                new_weight = self._get_edge_weight(rel_type, metadata)
                # Add weights together
                G[source][target]['weight'] = existing_weight + new_weight
                # Append relationship type to list
                existing_rel = G[source][target]['relationship']
                if isinstance(existing_rel, list):
                    G[source][target]['relationship'].append(rel_type)
                else:
                    G[source][target]['relationship'] = [existing_rel, rel_type]

        # Add account attributes to nodes
        for username, profile in accounts.items():
            if username in G.nodes():
                G.nodes[username].update(profile)

        logger.info(f"Built graph with {len(G.nodes())} nodes and {len(G.edges())} edges")
        return G

    def process_target_profile(self, data, G, accounts):
        """Add target profile to graph"""
        profile = data.get("profile", {})
        if not profile:
            return

        username = profile.get("username", self.target_account)
        G.add_node(username, degree=0, category="target")
        accounts[username] = profile
        logger.info(f"Added target profile: {username}")

    def process_posts(self, data, G, accounts, relationships):
        """Extract relationships from posts"""
        posts = data.get("posts", [])

        for post in posts:
            # Process tagged accounts
            tagged_accounts = post.get("tagged_accounts", [])
            for tagged in tagged_accounts:
                username = tagged.get("username")
                if username:
                    if username not in accounts:
                        accounts[username] = {"username": username}
                    relationships.append((
                        self.target_account,
                        username,
                        "tags",
                        {"post_id": post.get("post_id")}
                    ))

            # Process commenters
            commenters = post.get("commenters", [])
            commenter_counts = {}
            for commenter in commenters:
                username = commenter.get("username")
                if username:
                    if username not in accounts:
                        accounts[username] = {"username": username}
                    commenter_counts[username] = commenter_counts.get(username, 0) + 1

            # Add commenter relationships with frequency-based weights
            for username, count in commenter_counts.items():
                relationships.append((
                    username,
                    self.target_account,
                    "comments",
                    {"post_id": post.get("post_id"), "comment_count": count}
                ))

            # Process collaborators
            collaborators = post.get("collaborators", [])
            for collab in collaborators:
                username = collab.get("username")
                if username:
                    if username not in accounts:
                        accounts[username] = {"username": username}
                    relationships.append((
                        self.target_account,
                        username,
                        "collaborator",
                        {"post_id": post.get("post_id")}
                    ))

    def process_following(self, data, G, accounts, relationships):
        """Process following list"""
        following = data.get("following", [])

        for account in following:
            username = account.get("username")
            if username:
                if username not in accounts:
                    accounts[username] = account
                else:
                    # Update with any additional info
                    accounts[username].update(account)

                # Add following relationship
                relationships.append((
                    self.target_account,
                    username,
                    "follows",
                    {}
                ))

    def process_first_degree_accounts(self, data, G, accounts):
        """Add full profiles for first-degree accounts"""
        profiles = data.get("discovered_accounts", [])

        for profile in profiles:
            username = profile.get("username")
            if username:
                if username not in accounts:
                    accounts[username] = profile
                else:
                    # Update with full profile data
                    accounts[username].update(profile)
                logger.debug(f"Added first-degree profile: {username}")

    def _get_edge_weight(self, rel_type, metadata):
        """Calculate edge weight based on relationship type and metadata"""
        if rel_type == "comments":
            # Commenter weight formula: base + (count - 1) * frequency_bonus
            comment_count = metadata.get("comment_count", 1)
            base = self.edge_weights.get("repeated_commenter_base", 7)
            bonus = self.edge_weights.get("frequency_bonus", 2)
            return base + (comment_count - 1) * bonus
        else:
            # Use configured weight for other relationship types
            return self.edge_weights.get(rel_type, 5)

    def save_graph(self, G):
        """Save graph as JSON and CSVs"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save graph as JSON (node-link format)
        graph_json_path = self.processed_dir / f"graph_{timestamp}.json"
        graph_data = nx.node_link_data(G)
        with open(graph_json_path, 'w') as f:
            json.dump(graph_data, f, indent=2)
        logger.info(f"Saved graph JSON: {graph_json_path}")

        # Save edges CSV
        edges_csv_path = self.processed_dir / f"edges_{timestamp}.csv"
        with open(edges_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['source', 'target', 'relationship', 'weight'])
            for source, target, data in G.edges(data=True):
                writer.writerow([
                    source,
                    target,
                    data.get('relationship', ''),
                    data.get('weight', 0)
                ])
        logger.info(f"Saved edges CSV: {edges_csv_path}")

        # Save accounts CSV
        accounts_csv_path = self.processed_dir / f"accounts_{timestamp}.csv"
        with open(accounts_csv_path, 'w', newline='') as f:
            # Collect all possible fields from nodes
            all_fields = set()
            for node, data in G.nodes(data=True):
                all_fields.update(data.keys())

            fieldnames = ['username'] + sorted(all_fields - {'username'})
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for node, data in G.nodes(data=True):
                row = {'username': node}
                row.update(data)
                writer.writerow(row)
        logger.info(f"Saved accounts CSV: {accounts_csv_path}")

        return {
            'graph_json': str(graph_json_path),
            'edges_csv': str(edges_csv_path),
            'accounts_csv': str(accounts_csv_path)
        }

    def run(self):
        """Main execution orchestrator"""
        logger.info("Starting graph building process")

        # Load all raw data
        raw_data_list = self.load_all_raw_data()
        logger.info(f"Loaded {len(raw_data_list)} raw data files")

        if not raw_data_list:
            logger.warning("No raw data found to process")
            return None

        # Build graph
        G = self.build_graph(raw_data_list)

        # Save graph
        saved_files = self.save_graph(G)

        logger.info("Graph building complete")
        return {
            'graph': G,
            'files': saved_files,
            'stats': {
                'nodes': len(G.nodes()),
                'edges': len(G.edges())
            }
        }
