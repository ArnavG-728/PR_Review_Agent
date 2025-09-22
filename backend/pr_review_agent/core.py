# backend/core.py

import os
import json
import logging
from pr_review_agent.fetch_pr import create_git_client, GitProvider
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

    # 1. Create Git client and fetch PR details
    try:
        git_provider = GitProvider(provider.lower())
        client = create_git_client(git_provider, repo, token)
        
        # Validate connection
        if not client.validate_connection():
            raise ConnectionError(f"Failed to connect to {provider} repository: {repo}")
        
        details = client.get_pr_details(pr_id)
        diff = client.get_pr_diff(pr_id)

        pr_data = {
            "id": pr_id,
            "repo": repo,
            "title": details.get('title'),
            "author": details.get('author', {}).get('display_name'),
            "diff": diff,
            "head_sha": details.get('source_sha'),
            "provider": provider,
            "details": details
        }
    except ValueError as e:
        if "is not a valid GitProvider" in str(e):
            raise NotImplementedError(f"Git provider '{provider}' is not supported yet.")
        raise
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
            except Exception as e:
                logging.warning(f"Could not fetch content for file {file_info['file_path']}: {e}")

        # 4. Calculate PR score
        score = calculate_pr_score(analysis_results, file_contents)

        # 5. Generate feedback using AI with enhanced context
        pr_context = {
            'title': pr_data['title'],
            'description': pr_data['details'].get('description', ''),
            'author': pr_data['author'],
            'provider': pr_data['provider'],
            'url': pr_data['details'].get('url', ''),
            'files_changed': [f['file_path'] for f in parse_diff(pr_data['diff'])],
            'branch': pr_data['details'].get('source_branch', 'unknown')
        }
        
        feedback = generate_ai_feedback(analysis_results, pr_data['diff'], pr_context)
        
        # Maintain backward compatibility with score field
        feedback['score'] = feedback.get('overall_score', score)
        
        # 6. Add PR details to feedback
        feedback['pr_details'] = {
            'number': pr_data['id'],
            'title': pr_data['title'],
            'author': pr_data['author'],
            'provider': pr_data['provider'].title(),
            'url': pr_data['details'].get('url', '')
        }

        # 7. Store results
        try:
            db.store_pr_data(pr_data, feedback)
        except Exception as db_error:
            logging.error(f"CRITICAL: Failed to store results in database. Error: {db_error}")
            # Optionally, add a warning to the feedback to be returned
            feedback['warnings'] = feedback.get('warnings', []) + ["Failed to save review results to the database."]
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

    # 8. Save and print feedback
    if feedback.get('comments'):
        with open('review_comments.json', 'w') as f:
            json.dump(feedback['comments'], f, indent=2)
        print("\nInline review comments saved to review_comments.json")

    print("\n--- Generated Feedback ---")
    print(f"**Overall PR Score: {score}/100**")
    print(feedback.get('markdown_summary', 'No feedback generated.'))
    print("--------------------------\n")

    return feedback
