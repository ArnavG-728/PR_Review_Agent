# main.py

import argparse
import os
from pr_review_agent.core import run_review

def main():
    """Main function to run the PR review agent from the command line."""
    parser = argparse.ArgumentParser(description='AI-powered Pull Request Review Agent.')
    parser.add_argument('--repo', required=True, help='Repository name in owner/repo format.')
    parser.add_argument('--pr-id', required=True, type=int, help='Pull Request ID.')
    parser.add_argument('--provider', default='github', help='Git provider (e.g., github, gitlab).')
    parser.add_argument('--token', help='Personal access token for private repositories.')

    args = parser.parse_args()

    token = args.token or os.environ.get("GITHUB_TOKEN")

    try:
        run_review(args.repo, args.pr_id, args.provider, token)
    except Exception as e:
        print(f"CLI Error: {e}")

if __name__ == "__main__":
    main()
