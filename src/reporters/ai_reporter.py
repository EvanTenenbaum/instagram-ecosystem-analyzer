import json
import logging
from pathlib import Path
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class AIReporter:
    """Generate AI-consumable outputs with tiered recommendations"""

    def __init__(self, config):
        """Setup directories and configuration"""
        self.config = config
        self.target_account = config["target_account"]
        self.processed_dir = Path("data/processed")
        self.outputs_dir = self.processed_dir / "outputs"
        self.outputs_dir.mkdir(parents=True, exist_ok=True)

    def load_processed_data(self):
        """Load CSVs and JSONs from processed/outputs"""
        # Find most recent account scores JSON
        scores_files = list(self.processed_dir.glob("account_scores_*.json"))
        if not scores_files:
            logger.error("No account scores JSON found")
            return None

        # Sort by filename (timestamp) and get most recent
        latest_scores_file = sorted(scores_files)[-1]
        logger.info(f"Loading scores from: {latest_scores_file}")

        with open(latest_scores_file, 'r') as f:
            scores_data = json.load(f)

        # Load accounts DataFrame (create from scores if CSV doesn't exist)
        accounts_csv = self.outputs_dir / "accounts.csv"
        if accounts_csv.exists():
            accounts_df = pd.read_csv(accounts_csv)
        else:
            # Create DataFrame from scores
            accounts_df = pd.DataFrame(scores_data["scores"])

        # Load metrics if available
        metrics_files = list(self.processed_dir.glob("graph_metrics_*.json"))
        metrics_data = None
        if metrics_files:
            latest_metrics_file = sorted(metrics_files)[-1]
            logger.info(f"Loading metrics from: {latest_metrics_file}")
            with open(latest_metrics_file, 'r') as f:
                metrics_data = json.load(f)

        return {
            "accounts_df": accounts_df,
            "scores_data": scores_data,
            "metrics_data": metrics_data
        }

    def generate_recommended_targets(self, scores_data):
        """Top 50, tiers A/B/C (15/20/15), save CSV"""
        scores = scores_data.get("scores", [])

        # Get top 50
        top_50 = scores[:50]

        # Assign tiers
        recommendations = []
        for idx, account in enumerate(top_50):
            rank = idx + 1
            if rank <= 15:
                tier = "A"
            elif rank <= 35:
                tier = "B"
            else:
                tier = "C"

            recommendations.append({
                "rank": rank,
                "tier": tier,
                "username": account["username"],
                "overall_score": account["overall_score"],
                "proximity_score": account["proximity_score"],
                "engagement_score": account["engagement_score"],
                "bridge_score": account["bridge_score"],
                "category": account["category"],
                "follower_count": account.get("follower_count", 0),
                "following_count": account.get("following_count", 0),
                "bio": account.get("bio", "")
            })

        # Save to CSV
        df = pd.DataFrame(recommendations)
        csv_path = self.outputs_dir / "recommended_targets.csv"
        df.to_csv(csv_path, index=False)
        logger.info(f"Saved recommended targets: {csv_path}")

        return recommendations

    def suggest_engagement_strategy(self, category, account):
        """Return strategy text by category"""
        strategies = {
            "gallery": f"Reach out to inquire about representation or upcoming exhibitions. Reference your work style and how it aligns with their roster.",
            "curator": f"Share your portfolio and ask about potential exhibition opportunities. Mention specific themes or concepts in your work.",
            "wood_artist": f"Connect over shared craft techniques and materials. Consider collaboration or mutual promotion opportunities.",
            "furniture_designer": f"Discuss design philosophy and potential collaboration. Share work-in-progress or behind-the-scenes content.",
            "collector": f"Share high-quality images of available work. Engage with their collection posts and offer insights on your pieces.",
            "institution": f"Inquire about submission processes or artist programs. Research their mission and align your pitch accordingly.",
            "fair": f"Ask about application deadlines and booth requirements. Mention relevant past exhibition experience.",
            "journalist": f"Pitch a story angle about your work or process. Provide high-res images and a compelling narrative.",
            "craft_artist": f"Engage around shared techniques and artistic philosophy. Consider joint workshops or collaborative projects.",
            "unknown": f"Start with general engagement on their posts. Monitor their content to identify specific interests before reaching out directly."
        }

        return strategies.get(category, strategies["unknown"])

    def generate_evidence_summary(self, account):
        """Generate evidence string from scores"""
        evidence_parts = []

        # Proximity
        if account["proximity_score"] > 70:
            evidence_parts.append(f"close connection (proximity: {account['proximity_score']:.0f})")

        # Engagement
        if account["engagement_score"] > 70:
            evidence_parts.append(f"strong engagement (score: {account['engagement_score']:.0f})")

        # Bridge
        if account["bridge_score"] > 50:
            evidence_parts.append(f"network connector (bridge: {account['bridge_score']:.0f})")

        # Category confidence (assuming we have confidence, otherwise infer from category_fit_score)
        if account.get("category") not in ["unknown", ""]:
            evidence_parts.append(f"{account['category']} profile")

        if evidence_parts:
            return "; ".join(evidence_parts)
        else:
            return "general network presence"

    def generate_ai_summary(self, accounts_df, scores_data, metrics_data):
        """Generate markdown report"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Load recommendations
        recommendations_csv = self.outputs_dir / "recommended_targets.csv"
        if recommendations_csv.exists():
            recommendations_df = pd.read_csv(recommendations_csv)
        else:
            logger.error("Recommended targets CSV not found")
            return None

        # Start building markdown
        md_lines = []
        md_lines.append(f"# Instagram Ecosystem Analysis Report")
        md_lines.append(f"")
        md_lines.append(f"**Target Account:** {self.target_account}")
        md_lines.append(f"**Generated:** {timestamp}")
        md_lines.append(f"")

        # Executive Summary
        md_lines.append(f"## Executive Summary")
        md_lines.append(f"")
        total_analyzed = len(accounts_df)
        total_recommended = len(recommendations_df)

        if metrics_data and "graph_metrics" in metrics_data:
            graph_metrics = metrics_data["graph_metrics"]
            md_lines.append(f"- **Total Accounts Analyzed:** {total_analyzed}")
            md_lines.append(f"- **Network Size:** {graph_metrics.get('total_nodes', 'N/A')} nodes, {graph_metrics.get('total_edges', 'N/A')} connections")
            md_lines.append(f"- **Network Density:** {graph_metrics.get('density', 0):.4f}")
        elif scores_data and "graph_metrics" in scores_data:
            graph_metrics = scores_data["graph_metrics"]
            md_lines.append(f"- **Total Accounts Analyzed:** {total_analyzed}")
            md_lines.append(f"- **Network Size:** {graph_metrics.get('total_nodes', 'N/A')} nodes, {graph_metrics.get('total_edges', 'N/A')} connections")
            md_lines.append(f"- **Network Density:** {graph_metrics.get('density', 0):.4f}")
        else:
            md_lines.append(f"- **Total Accounts Analyzed:** {total_analyzed}")

        md_lines.append(f"- **Recommended Targets:** {total_recommended}")
        md_lines.append(f"")

        # Tier breakdown
        tier_counts = recommendations_df['tier'].value_counts()
        md_lines.append(f"### Tier Breakdown")
        md_lines.append(f"")
        md_lines.append(f"- **Tier A (Top Priority):** {tier_counts.get('A', 0)} accounts")
        md_lines.append(f"- **Tier B (High Value):** {tier_counts.get('B', 0)} accounts")
        md_lines.append(f"- **Tier C (Strategic):** {tier_counts.get('C', 0)} accounts")
        md_lines.append(f"")

        # Top 15 (Tier A) Detailed Recommendations
        md_lines.append(f"## Tier A: Top Priority Targets (Rank 1-15)")
        md_lines.append(f"")
        tier_a = recommendations_df[recommendations_df['tier'] == 'A']

        for _, row in tier_a.iterrows():
            md_lines.append(f"### {row['rank']}. @{row['username']} (Score: {row['overall_score']:.1f})")
            md_lines.append(f"")
            md_lines.append(f"**Category:** {row['category'].replace('_', ' ').title()}")
            md_lines.append(f"")
            md_lines.append(f"**Evidence:** {self.generate_evidence_summary(row)}")
            md_lines.append(f"")
            md_lines.append(f"**Engagement Strategy:**")
            md_lines.append(f"{self.suggest_engagement_strategy(row['category'], row)}")
            md_lines.append(f"")
            if row.get('bio'):
                md_lines.append(f"**Bio:** {row['bio']}")
                md_lines.append(f"")
            md_lines.append(f"**Stats:** {row['follower_count']:,} followers, {row['following_count']:,} following")
            md_lines.append(f"")
            md_lines.append(f"---")
            md_lines.append(f"")

        # Tier B Summary Table
        md_lines.append(f"## Tier B: High Value Targets (Rank 16-35)")
        md_lines.append(f"")
        tier_b = recommendations_df[recommendations_df['tier'] == 'B']

        md_lines.append(f"| Rank | Username | Score | Category | Followers |")
        md_lines.append(f"|------|----------|-------|----------|-----------|")
        for _, row in tier_b.iterrows():
            md_lines.append(f"| {row['rank']} | @{row['username']} | {row['overall_score']:.1f} | {row['category'].replace('_', ' ').title()} | {row['follower_count']:,} |")
        md_lines.append(f"")

        # Tier C Summary Table
        md_lines.append(f"## Tier C: Strategic Targets (Rank 36-50)")
        md_lines.append(f"")
        tier_c = recommendations_df[recommendations_df['tier'] == 'C']

        md_lines.append(f"| Rank | Username | Score | Category | Followers |")
        md_lines.append(f"|------|----------|-------|----------|-----------|")
        for _, row in tier_c.iterrows():
            md_lines.append(f"| {row['rank']} | @{row['username']} | {row['overall_score']:.1f} | {row['category'].replace('_', ' ').title()} | {row['follower_count']:,} |")
        md_lines.append(f"")

        # Category Distribution
        md_lines.append(f"## Category Distribution")
        md_lines.append(f"")
        category_counts = recommendations_df['category'].value_counts()

        md_lines.append(f"| Category | Count |")
        md_lines.append(f"|----------|-------|")
        for category, count in category_counts.items():
            md_lines.append(f"| {category.replace('_', ' ').title()} | {count} |")
        md_lines.append(f"")

        # Scoring Methodology
        md_lines.append(f"## Scoring Methodology")
        md_lines.append(f"")
        if scores_data and "metadata" in scores_data:
            weights = scores_data["metadata"].get("scoring_weights", {})
            md_lines.append(f"Accounts are scored using a weighted average of four factors:")
            md_lines.append(f"")
            md_lines.append(f"- **Proximity ({weights.get('proximity', 0):.0%}):** Network distance from target account")
            md_lines.append(f"- **Engagement ({weights.get('engagement', 0):.0%}):** Interaction strength and bidirectional connections")
            md_lines.append(f"- **Bridge ({weights.get('bridge', 0):.0%}):** Network centrality and connector potential")
            md_lines.append(f"- **Category Fit ({weights.get('category_fit', 0):.0%}):** Alignment with target categories (galleries, curators, artists, etc.)")
            md_lines.append(f"")

        # Next Steps
        md_lines.append(f"## Recommended Next Steps")
        md_lines.append(f"")
        md_lines.append(f"1. **Immediate Action (Tier A):** Review and prioritize the top 15 accounts for direct outreach")
        md_lines.append(f"2. **Engagement Preparation:** Customize engagement strategies based on each account's category and evidence")
        md_lines.append(f"3. **Content Alignment:** Ensure your profile and recent posts align with the interests of target categories")
        md_lines.append(f"4. **Monitoring:** Track responses and engagement patterns to refine future outreach")
        md_lines.append(f"5. **Tier B Follow-up:** Plan systematic engagement with high-value targets over the next 2-4 weeks")
        md_lines.append(f"")

        # Save markdown
        md_content = "\n".join(md_lines)
        md_path = self.outputs_dir / "ai_summary.md"
        with open(md_path, 'w') as f:
            f.write(md_content)

        logger.info(f"Saved AI summary: {md_path}")
        return str(md_path)

    def run(self):
        """Load, generate recommendations, generate summary"""
        logger.info("Starting AI report generation")

        # Load processed data
        data = self.load_processed_data()
        if not data:
            logger.error("Failed to load processed data")
            return None

        accounts_df = data["accounts_df"]
        scores_data = data["scores_data"]
        metrics_data = data["metrics_data"]

        # Generate recommendations
        recommendations = self.generate_recommended_targets(scores_data)
        logger.info(f"Generated {len(recommendations)} recommendations")

        # Generate summary
        summary_path = self.generate_ai_summary(accounts_df, scores_data, metrics_data)

        logger.info("AI report generation complete")
        return {
            "recommendations": recommendations,
            "summary_path": summary_path,
            "outputs_dir": str(self.outputs_dir)
        }
