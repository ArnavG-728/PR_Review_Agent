# src/pr_review_agent/database.py

import json
from typing import Dict, Any
from .db_manager import db_manager

class Database:
    """A class to handle all database operations with Neo4j."""


    def store_pr_data(self, pr_data: Dict[str, Any], feedback: Dict[str, Any]):
        """Stores PR data, author, and review in the Neo4j database."""
        driver = db_manager.get_driver()
        if not driver:
            print("Database connection not available. Skipping store operation.")
            return

        print(f"Storing data for PR {pr_data.get('id')} in Neo4j...")

        query = (
            # Find or create the Repository and Author
            "MERGE (repo:Repository {name: $repo_name}) "
            "MERGE (author:Author {name: $author_name}) "
            
            # Find or create the PullRequest based on its ID within the repository
            "MERGE (repo)-[:HAS_PR]->(pr:PullRequest {id: $pr_id}) "
            "ON CREATE SET pr.title = $pr_title, pr.head_sha = $pr_head_sha, pr.created_at = timestamp() "
            "ON MATCH SET pr.title = $pr_title, pr.head_sha = $pr_head_sha "
            
            # Connect the author to the PR
            "MERGE (author)-[:AUTHORED]->(pr) "
            
            # Always create a new Review for this analysis run
            "CREATE (review:Review {content: $review_content, created_at: timestamp()}) "
            "MERGE (pr)-[:HAS_REVIEW]->(review)"
        )

        with driver.session() as session:
            try:
                session.run(query,
                            repo_name=pr_data['repo'],
                            author_name=pr_data['author'],
                            pr_id=pr_data['id'],
                            pr_title=pr_data['title'],
                            pr_head_sha=pr_data['head_sha'],
                            review_content=json.dumps(feedback))
                print("Successfully stored PR data in Neo4j.")
            except Exception as e:
                print(f"Failed to store PR data in Neo4j: {e}")

# For backward compatibility with the old main.py structure, though it won't be used
def store_pr_data(pr_data: dict):
    print("This function is deprecated. Use the Database class instead.")
    pass
