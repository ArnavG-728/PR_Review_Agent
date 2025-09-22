# src/pr_review_agent/database.py

import json
from typing import Dict, Any
from .db_manager import db_manager

class Database:
    """A class to handle all database operations with Neo4j."""


    def store_pr_data(self, pr_data: Dict[str, Any], feedback: Dict[str, Any]):
        """Stores PR data, author, and review in the Neo4j database with enhanced schema."""
        driver = db_manager.get_driver()
        if not driver:
            print("Database connection not available. Skipping store operation.")
            return

        print(f"Storing data for PR {pr_data.get('id')} in Neo4j...")

        query = (
            # Find or create the Repository with provider info
            "MERGE (repo:Repository {name: $repo_name}) "
            "ON CREATE SET repo.provider = $provider, repo.created_at = timestamp() "
            "ON MATCH SET repo.provider = $provider "
            
            # Find or create the Author
            "MERGE (author:Author {name: $author_name}) "
            "ON CREATE SET author.created_at = timestamp() "
            
            # Find or create the PullRequest with enhanced properties
            "MERGE (repo)-[:HAS_PR]->(pr:PullRequest {id: $pr_id}) "
            "ON CREATE SET pr.title = $pr_title, pr.head_sha = $pr_head_sha, "
            "pr.provider = $provider, pr.url = $pr_url, pr.created_at = timestamp() "
            "ON MATCH SET pr.title = $pr_title, pr.head_sha = $pr_head_sha, "
            "pr.provider = $provider, pr.url = $pr_url "
            
            # Connect the author to the PR
            "MERGE (author)-[:AUTHORED]->(pr) "
            
            # Create a new Review with detailed scores
            "CREATE (review:Review {"
            "content: $review_content, "
            "overall_score: $overall_score, "
            "structure_score: $structure_score, "
            "standards_score: $standards_score, "
            "security_score: $security_score, "
            "performance_score: $performance_score, "
            "testing_score: $testing_score, "
            "created_at: timestamp()"
            "}) "
            "MERGE (pr)-[:HAS_REVIEW]->(review) "
            
            # Create Issue nodes for each comment
            "WITH review, $comments as comments "
            "UNWIND comments as comment "
            "CREATE (issue:Issue {"
            "file_path: comment.file_path, "
            "line: comment.line, "
            "severity: comment.severity, "
            "category: comment.category, "
            "description: comment.comment, "
            "suggestion: coalesce(comment.suggestion, '') "
            "}) "
            "MERGE (review)-[:IDENTIFIED]->(issue)"
        )

        # Extract scores from feedback
        scores = feedback.get('scores', {})
        comments = feedback.get('comments', [])

        with driver.session() as session:
            try:
                session.run(query,
                            repo_name=pr_data['repo'],
                            provider=pr_data.get('provider', 'unknown'),
                            author_name=pr_data['author'],
                            pr_id=pr_data['id'],
                            pr_title=pr_data['title'],
                            pr_head_sha=pr_data['head_sha'],
                            pr_url=pr_data.get('details', {}).get('url', ''),
                            review_content=json.dumps(feedback),
                            overall_score=feedback.get('overall_score', 0),
                            structure_score=scores.get('structure_design', 0),
                            standards_score=scores.get('standards_compliance', 0),
                            security_score=scores.get('security_safety', 0),
                            performance_score=scores.get('performance', 0),
                            testing_score=scores.get('testing_reliability', 0),
                            comments=comments)
                print("Successfully stored PR data in Neo4j with enhanced schema.")
            except Exception as e:
                print(f"Failed to store PR data in Neo4j: {e}")

# For backward compatibility with the old main.py structure, though it won't be used
def store_pr_data(pr_data: dict):
    print("This function is deprecated. Use the Database class instead.")
    pass
