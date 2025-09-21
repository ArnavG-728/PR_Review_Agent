import requests
import os
import dotenv
dotenv.load_dotenv()

def get_pull_requests(owner: str, repo: str) -> list:
    """
    Fetches all pull requests (open and closed) for a given GitHub repository by handling pagination.

    Args:
        owner: The owner of the repository.
        repo: The name of the repository.

    Returns:
        A list of dictionaries, each representing a pull request.

    Raises:
        requests.exceptions.HTTPError: If the repository is not found or another HTTP error occurs.
    """
    all_prs = []
    page = 1
    per_page = 100  # Max allowed by GitHub API

    # Get the token from environment variables
    github_token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json"
    }
    if github_token:
        headers["Authorization"] = f"token {github_token}"
        print("Using GitHub token for authentication.")
    else:
        print("Warning: GITHUB_TOKEN environment variable not set. Making unauthenticated requests, which have a lower rate limit.")

    while True:
        api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls?state=all&per_page={per_page}&page={page}"
        
        print(f"Fetching page {page} of PRs from {owner}/{repo}...")
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        
        # If the page is empty, we've fetched all PRs
        if not data:
            break

        for pr in data:
            all_prs.append({
                "number": pr["number"],
                "title": pr["title"],
                "created_at": pr["created_at"],
                "user": pr["user"]["login"],
                "state": pr["state"]
            })
        
        page += 1

    print(f"Finished fetching. Found {len(all_prs)} total pull requests.")
    return all_prs
