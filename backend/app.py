# backend/app.py

import atexit
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from urllib.parse import urlparse
from pr_review_agent.core import run_review
from pr_review_agent.github_api import get_pull_requests
from pr_review_agent.db_manager import db_manager
import os

app = Flask(__name__)
# Whitelist of allowed origins for CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
CORS(app, origins=[frontend_url], supports_credentials=True)

@app.route('/api/validate_repo', methods=['POST'])
def validate_repo_endpoint():
    data = request.get_json()
    if not data or 'repo_url' not in data:
        return jsonify({'error': 'repo_url is required'}), 400

    repo_url = data['repo_url']
    try:
        path = urlparse(repo_url).path.strip('/')
        parts = path.split('/')
        if len(parts) < 2:
            raise ValueError("Invalid repository URL format. Expected format: https://github.com/owner/repo")
        
        owner, repo = parts[0], parts[1]
        
        pull_requests = get_pull_requests(owner, repo)
        return jsonify(pull_requests)

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return jsonify({'error': 'Repository not found or is private.'}), 404
        else:
            return jsonify({'error': f'GitHub API error: {e.response.text}'}), e.response.status_code
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"API Error on /api/validate_repo: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@app.route('/api/check_workflow', methods=['POST'])
def check_workflow_endpoint():
    data = request.get_json()
    repo_url = data.get('repo_url')
    if not repo_url:
        return jsonify({'error': 'repo_url is required'}), 400

    try:
        path = urlparse(repo_url).path.strip('/')
        parts = path.split('/')
        owner, repo = parts[0], parts[1]
        workflow_path = '.github/workflows/ai-review.yml'

        github_token = os.getenv('GITHUB_TOKEN')
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if github_token:
            headers['Authorization'] = f'token {github_token}'

        # Try to get the content of the workflow file
        api_url = f'https://api.github.com/repos/{owner}/{repo}/contents/{workflow_path}'
        response = requests.get(api_url, headers=headers)

        if response.status_code == 200:
            return jsonify({'exists': True})
        elif response.status_code == 404:
            return jsonify({'exists': False})
        else:
            response.raise_for_status()

    except Exception as e:
        print(f"API Error on /api/check_workflow: {e}")
        return jsonify({'error': 'An internal error occurred while checking for workflow.'}), 500


@app.route('/api/get_reviews', methods=['POST'])
def get_reviews_endpoint():
    data = request.get_json()
    repo_url = data.get('repo_url')
    if not repo_url:
        return jsonify({'error': 'repo_url is required'}), 400

    try:
        path = urlparse(repo_url).path.strip('/')
        parts = path.split('/')
        repo_name = f"{parts[0]}/{parts[1]}"

        driver = db_manager.get_driver()
        if not driver:
            return jsonify({'error': 'Database connection not available.'}), 500

        with driver.session() as session:
            result = session.run("""
                MATCH (pr:PullRequest)-[:HAS_REVIEW]->(r:Review)
                WHERE pr.repo = $repo_name
                RETURN pr.id AS number, pr.title AS title, r.score AS score
                ORDER BY number DESC
            """, repo_name=repo_name)
            
            reviews = [record.data() for record in result]
        
        return jsonify(reviews)

    except Exception as e:
        print(f"API Error on /api/get_reviews: {e}")
        return jsonify({'error': 'An internal error occurred while fetching reviews.'}), 500


@app.route('/api/review', methods=['POST'])
def review_pr_endpoint():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    repo = data.get('repo')
    pr_id = data.get('pr_id')
    provider = data.get('provider', 'github')
    token = data.get('token')

    if not repo or not pr_id:
        return jsonify({'error': 'repo and pr_id are required'}), 400

    try:
        # The run_review function now returns the feedback dictionary
        result = run_review(repo, pr_id, provider, token)
        return jsonify(result)
    except Exception as e:
        # Log the full error for debugging
        print(f"API Error in review_pr_endpoint: {e}")
        try:
            # Check if the error message is a JSON string with our custom structure
            error_data = json.loads(str(e))
            return jsonify({'error': error_data.get('message'), 'details': error_data.get('details')}), 500
        except (json.JSONDecodeError, TypeError):
            # If not, return a generic error
            return jsonify({'error': 'An internal error occurred during analysis.'}), 500

# Initialize the database connection when the app starts
db_manager.connect()

# Register a function to close the database connection when the app exits
atexit.register(db_manager.close)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)
