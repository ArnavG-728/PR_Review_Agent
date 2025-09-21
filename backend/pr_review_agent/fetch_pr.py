# src/pr_review_agent/fetch_pr.py

import os
import requests
import gitlab
from abc import ABC, abstractmethod
from typing import Dict, Any

class GitClient(ABC):
    """Abstract base class for Git clients."""
    def __init__(self, repo: str, token: str = None):
        self.repo = repo
        self.token = token

    @abstractmethod
    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches pull request details."""
        pass

    @abstractmethod
    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a pull request."""
        pass

class GitHubClient(GitClient):
    """GitHub API client."""
    API_URL = "https://api.github.com"

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches pull request details from GitHub."""
        url = f"{self.API_URL}/repos/{self.repo}/pulls/{pr_id}"
        headers = {'Accept': 'application/vnd.github.v3+json'}
        if self.token:
            headers['Authorization'] = f'token {self.token}'
        
        response = requests.get(url, headers=headers)
        response.raise_for_status() # Raise an exception for bad status codes
        return response.json()

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a pull request from GitHub."""
        url = f"{self.API_URL}/repos/{self.repo}/pulls/{pr_id}"
        headers = {'Accept': 'application/vnd.github.v3.diff'}
        if self.token:
            headers['Authorization'] = f'token {self.token}'

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from GitHub."""
        url = f"{self.API_URL}/repos/{self.repo}/contents/{file_path}?ref={ref}"
        headers = {'Accept': 'application/vnd.github.v3.raw'}
        if self.token:
            headers['Authorization'] = f'token {self.token}'

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text


class GitLabClient(GitClient):
    """GitLab API client."""

    def __init__(self, repo: str, token: str = None):
        super().__init__(repo, token)
        self.gl = gitlab.Gitlab('https://gitlab.com', private_token=token)
        try:
            self.project = self.gl.projects.get(self.repo)
        except gitlab.exceptions.GitlabError as e:
            raise ValueError(f"Could not find GitLab project '{self.repo}'. Please check the name and your token.") from e

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches merge request details from GitLab."""
        mr = self.project.mergerequests.get(pr_id)
        return mr.attributes

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a merge request from GitLab."""
        mr = self.project.mergerequests.get(pr_id)
        # The GitLab API returns diffs per-file, so we need to concatenate them
        diff_text = ""
        for change in mr.changes()['changes']:
            diff_text += change['diff']
        return diff_text

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from GitLab."""
        file_content = self.project.files.get(file_path=file_path, ref=ref)
        return file_content.decode('utf-8')
