# backend/core.py

import os
import json
from pr_review_agent.fetch_pr import GitHubClient, GitLabClient
from pr_review_agent.analyze_code import analyze_pr_diff, parse_diff
from pr_review_agent.generate_feedback import generate_ai_feedback
from pr_review_agent.score_pr import calculate_pr_score
from pr_review_agent.database import Database

def run_review(repo: str, pr_id: int, provider: str = 'github', token: str = None):
    # If no token is provided, try to get it from the environment variables
    if not token:
        token = os.getenv('GITHUB_TOKEN')
    """Runs the complete PR review process."""
    print(f"Starting PR Review Agent for {repo} PR #{pr_id} on {provider}")

    db = Database()

    # 1. Fetch PR details
    if provider.lower() == 'github':
        client = GitHubClient(repo, token=token)
    elif provider.lower() == 'gitlab':
        client = GitLabClient(repo, token=token)
    else:
        raise NotImplementedError(f"Git provider '{provider}' is not supported yet.")
    
    details = client.get_pr_details(pr_id)
    diff = client.get_pr_diff(pr_id)

    pr_data = {
        "id": pr_id,
        "repo": repo,
        "title": details.get('title'),
        "author": details.get('author', {}).get('username') if provider == 'gitlab' else details.get('user', {}).get('login'),
        "diff": diff,
        "head_sha": details.get('head', {}).get('sha')
    }
    print(f"Successfully fetched PR: {pr_data.get('title')}")
    print(f"Author: {pr_data.get('author')}")

    try:
        # 2. Analyze the code changes
        analysis_results = analyze_pr_diff(pr_data['diff'], client, pr_data['head_sha'])

        # 3. Fetch content of changed files for scoring
        changed_files_for_scoring = [f for f in parse_diff(pr_data['diff']) if f['file_path'].endswith('.py')]
        file_contents = {}
        for file_info in changed_files_for_scoring:
            try:
                content = client.get_file_content(file_info['file_path'], pr_data['head_sha'])
                file_contents[file_info['file_path']] = content
            except Exception:
                pass # Ignore files that can't be fetched

        # 4. Calculate PR score
        score = calculate_pr_score(analysis_results, file_contents)

        # 5. Generate feedback using AI
        feedback = generate_ai_feedback(analysis_results, pr_data['diff'])
        feedback['score'] = score

        # 6. Store results
        try:
            db.store_pr_data(pr_data, feedback)
        except Exception as db_error:
            print(f"CRITICAL: Failed to store results in database. Error: {db_error}")
            # We can choose to raise this or just log it. For now, we'll log it
            # and allow the feedback to be returned to the user regardless.
    except Exception as e:
        import traceback
        print(f"An error occurred during analysis: {e}")
        # Re-raise the exception with a structured message for the frontend
        error_details = {
            "message": "An error occurred during the code analysis phase.",
            "details": traceback.format_exc()
        }
        raise Exception(json.dumps(error_details)) from e

    # 7. Save and print feedback
    if feedback.get('comments'):
        with open('review_comments.json', 'w') as f:
            json.dump(feedback['comments'], f, indent=2)
        print("\nInline review comments saved to review_comments.json")

    print("\n--- Generated Feedback ---")
    print(f"**Overall PR Score: {score}/100**")
    print(feedback.get('markdown_summary', 'No feedback generated.'))
    print("--------------------------\n")

    return feedback
