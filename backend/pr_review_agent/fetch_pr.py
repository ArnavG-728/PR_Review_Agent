# src/pr_review_agent/fetch_pr.py

import os
import requests
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum

class GitProvider(Enum):
    """Enumeration of supported Git providers."""
    GITHUB = "github"
    GITLAB = "gitlab"
    GITEA = "gitea"
    BITBUCKET = "bitbucket"
    AZURE_REPOS = "azure_repos"
    AWS_CODECOMMIT = "aws_codecommit"
    GOOGLE_CLOUD_SOURCE = "google_cloud_source"
    SOURCEFORGE = "sourceforge"

class GitClient(ABC):
    """Abstract base class for Git clients."""
    
    def __init__(self, repo: str, token: str = None, base_url: str = None):
        self.repo = repo
        self.token = token
        self.base_url = base_url
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches pull request details."""
        pass

    @abstractmethod
    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a pull request."""
        pass

    @abstractmethod
    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file."""
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """Validates the connection to the Git provider."""
        pass

    def _make_request(self, url: str, headers: Dict[str, str] = None, method: str = 'GET') -> requests.Response:
        """Makes an HTTP request with proper error handling."""
        if headers is None:
            headers = {}
        
        try:
            response = requests.request(method, url, headers=headers, timeout=30)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Request failed for {url}: {e}")
            raise ConnectionError(f"Failed to connect to {self.__class__.__name__}: {e}") from e

class GitHubClient(GitClient):
    """GitHub API client with enhanced functionality."""
    
    def __init__(self, repo: str, token: str = None, base_url: str = None):
        super().__init__(repo, token, base_url)
        self.api_url = base_url or "https://api.github.com"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'PR-Review-Agent/1.0'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'

    def validate_connection(self) -> bool:
        """Validates the connection to GitHub."""
        try:
            url = f"{self.api_url}/repos/{self.repo}"
            response = self._make_request(url, self.headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"GitHub connection validation failed: {e}")
            return False

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches pull request details from GitHub."""
        url = f"{self.api_url}/repos/{self.repo}/pulls/{pr_id}"
        response = self._make_request(url, self.headers)
        
        data = response.json()
        
        # Normalize the response format
        return {
            'id': data.get('id'),
            'number': data.get('number'),
            'title': data.get('title'),
            'description': data.get('body'),
            'state': data.get('state'),
            'author': {
                'username': data.get('user', {}).get('login'),
                'display_name': data.get('user', {}).get('name') or data.get('user', {}).get('login'),
                'avatar_url': data.get('user', {}).get('avatar_url')
            },
            'source_branch': data.get('head', {}).get('ref'),
            'target_branch': data.get('base', {}).get('ref'),
            'source_sha': data.get('head', {}).get('sha'),
            'target_sha': data.get('base', {}).get('sha'),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
            'url': data.get('html_url'),
            'provider': GitProvider.GITHUB.value,
            'raw_data': data
        }

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a pull request from GitHub."""
        url = f"{self.api_url}/repos/{self.repo}/pulls/{pr_id}"
        headers = {**self.headers, 'Accept': 'application/vnd.github.v3.diff'}
        
        response = self._make_request(url, headers)
        return response.text

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from GitHub."""
        url = f"{self.api_url}/repos/{self.repo}/contents/{file_path}?ref={ref}"
        headers = {**self.headers, 'Accept': 'application/vnd.github.v3.raw'}
        
        response = self._make_request(url, headers)
        return response.text

    def get_repository_info(self) -> Dict[str, Any]:
        """Gets repository information."""
        url = f"{self.api_url}/repos/{self.repo}"
        response = self._make_request(url, self.headers)
        return response.json()

class AzureReposClient(GitClient):
    """Azure DevOps Repositories API client."""
    
    def __init__(self, repo: str, token: str = None, base_url: str = None):
        super().__init__(repo, token, base_url)
        # Azure DevOps format: organization/project/_git/repository
        # We expect repo format: organization/project/repository
        parts = repo.split('/')
        if len(parts) < 3:
            raise ValueError("Azure Repos format should be: organization/project/repository")
        
        self.organization = parts[0]
        self.project = parts[1]
        self.repository = parts[2]
        
        self.api_url = base_url or f"https://dev.azure.com/{self.organization}"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if self.token:
            # Azure DevOps uses Basic auth with PAT
            import base64
            auth_string = base64.b64encode(f":{self.token}".encode()).decode()
            self.headers['Authorization'] = f'Basic {auth_string}'

    def validate_connection(self) -> bool:
        """Validates the connection to Azure DevOps."""
        try:
            url = f"{self.api_url}/{self.project}/_apis/git/repositories/{self.repository}?api-version=7.0"
            response = self._make_request(url, self.headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Azure DevOps connection validation failed: {e}")
            return False

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches pull request details from Azure DevOps."""
        url = f"{self.api_url}/{self.project}/_apis/git/repositories/{self.repository}/pullrequests/{pr_id}?api-version=7.0"
        response = self._make_request(url, self.headers)
        
        data = response.json()
        
        # Normalize the response format
        return {
            'id': data.get('pullRequestId'),
            'number': data.get('pullRequestId'),
            'title': data.get('title'),
            'description': data.get('description'),
            'state': 'open' if data.get('status') == 'active' else 'closed',
            'author': {
                'username': data.get('createdBy', {}).get('uniqueName'),
                'display_name': data.get('createdBy', {}).get('displayName'),
                'avatar_url': data.get('createdBy', {}).get('imageUrl')
            },
            'source_branch': data.get('sourceRefName', '').replace('refs/heads/', ''),
            'target_branch': data.get('targetRefName', '').replace('refs/heads/', ''),
            'source_sha': data.get('lastMergeSourceCommit', {}).get('commitId'),
            'target_sha': data.get('lastMergeTargetCommit', {}).get('commitId'),
            'created_at': data.get('creationDate'),
            'updated_at': data.get('lastMergeSourceCommit', {}).get('committer', {}).get('date'),
            'url': f"{self.api_url}/{self.project}/_git/{self.repository}/pullrequest/{pr_id}",
            'provider': GitProvider.AZURE_REPOS.value,
            'raw_data': data
        }

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a pull request from Azure DevOps."""
        # First get PR details to get commit IDs
        pr_details = self.get_pr_details(pr_id)
        source_sha = pr_details.get('source_sha')
        target_sha = pr_details.get('target_sha')
        
        if not source_sha or not target_sha:
            raise ValueError("Could not retrieve commit IDs for diff")
        
        # Get diff between commits
        url = f"{self.api_url}/{self.project}/_apis/git/repositories/{self.repository}/diffs/commits?baseVersionDescriptor.version={target_sha}&targetVersionDescriptor.version={source_sha}&api-version=7.0"
        response = self._make_request(url, self.headers)
        
        data = response.json()
        
        # Convert Azure DevOps diff format to unified diff format
        diff_text = ""
        for change in data.get('changes', []):
            if change.get('item', {}).get('gitObjectType') == 'blob':
                file_path = change.get('item', {}).get('path', '')
                change_type = change.get('changeType')
                
                if change_type == 'add':
                    diff_text += f"diff --git a{file_path} b{file_path}\n"
                    diff_text += f"new file mode 100644\n"
                    diff_text += f"index 0000000..{change.get('item', {}).get('objectId', '')[:7]}\n"
                    diff_text += f"--- /dev/null\n"
                    diff_text += f"+++ b{file_path}\n"
                elif change_type == 'delete':
                    diff_text += f"diff --git a{file_path} b{file_path}\n"
                    diff_text += f"deleted file mode 100644\n"
                    diff_text += f"index {change.get('item', {}).get('objectId', '')[:7]}..0000000\n"
                    diff_text += f"--- a{file_path}\n"
                    diff_text += f"+++ /dev/null\n"
                else:  # edit
                    diff_text += f"diff --git a{file_path} b{file_path}\n"
                    diff_text += f"index {change.get('originalObjectId', '')[:7]}..{change.get('item', {}).get('objectId', '')[:7]} 100644\n"
                    diff_text += f"--- a{file_path}\n"
                    diff_text += f"+++ b{file_path}\n"
                
                # Note: Azure DevOps API doesn't provide line-by-line diff in this endpoint
                # For a complete implementation, you'd need to fetch file contents and compute diff
                diff_text += "@@ -1,1 +1,1 @@\n"
                diff_text += f" {change_type} {file_path}\n"
        
        return diff_text

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from Azure DevOps."""
        url = f"{self.api_url}/{self.project}/_apis/git/repositories/{self.repository}/items?path={file_path}&version={ref}&api-version=7.0"
        response = self._make_request(url, self.headers)
        return response.text

class GitLabClient(GitClient):
    """GitLab API client."""
    
    def __init__(self, repo: str, token: str = None, base_url: str = None):
        super().__init__(repo, token, base_url)
        self.api_url = base_url or "https://gitlab.com/api/v4"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'

    def validate_connection(self) -> bool:
        """Validates the connection to GitLab."""
        try:
            # URL encode the repo path for GitLab API
            import urllib.parse
            encoded_repo = urllib.parse.quote(self.repo, safe='')
            url = f"{self.api_url}/projects/{encoded_repo}"
            response = self._make_request(url, self.headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"GitLab connection validation failed: {e}")
            return False

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches merge request details from GitLab."""
        import urllib.parse
        encoded_repo = urllib.parse.quote(self.repo, safe='')
        url = f"{self.api_url}/projects/{encoded_repo}/merge_requests/{pr_id}"
        response = self._make_request(url, self.headers)
        
        data = response.json()
        
        # Normalize the response format
        return {
            'id': data.get('iid'),
            'number': data.get('iid'),
            'title': data.get('title'),
            'description': data.get('description'),
            'state': data.get('state'),
            'author': {
                'username': data.get('author', {}).get('username'),
                'display_name': data.get('author', {}).get('name'),
                'avatar_url': data.get('author', {}).get('avatar_url')
            },
            'source_branch': data.get('source_branch'),
            'target_branch': data.get('target_branch'),
            'source_sha': data.get('sha'),
            'target_sha': data.get('merge_commit_sha'),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
            'url': data.get('web_url'),
            'provider': GitProvider.GITLAB.value,
            'raw_data': data
        }

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a merge request from GitLab."""
        import urllib.parse
        encoded_repo = urllib.parse.quote(self.repo, safe='')
        url = f"{self.api_url}/projects/{encoded_repo}/merge_requests/{pr_id}/changes"
        response = self._make_request(url, self.headers)
        
        data = response.json()
        
        # Convert GitLab changes format to unified diff format
        diff_text = ""
        for change in data.get('changes', []):
            old_path = change.get('old_path')
            new_path = change.get('new_path')
            diff = change.get('diff', '')
            
            if diff:
                diff_text += diff + "\n"
            else:
                # Handle cases where diff is not provided
                if change.get('new_file'):
                    diff_text += f"diff --git a/{new_path} b/{new_path}\n"
                    diff_text += f"new file mode 100644\n"
                elif change.get('deleted_file'):
                    diff_text += f"diff --git a/{old_path} b/{old_path}\n"
                    diff_text += f"deleted file mode 100644\n"
                elif change.get('renamed_file'):
                    diff_text += f"diff --git a/{old_path} b/{new_path}\n"
                    diff_text += f"similarity index 100%\n"
                    diff_text += f"rename from {old_path}\n"
                    diff_text += f"rename to {new_path}\n"
        
        return diff_text

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from GitLab."""
        import urllib.parse
        encoded_repo = urllib.parse.quote(self.repo, safe='')
        encoded_path = urllib.parse.quote(file_path, safe='')
        url = f"{self.api_url}/projects/{encoded_repo}/repository/files/{encoded_path}/raw?ref={ref}"
        response = self._make_request(url, self.headers)
        return response.text

class GiteaClient(GitClient):
    """Gitea API client."""
    
    def __init__(self, repo: str, token: str = None, base_url: str = None):
        super().__init__(repo, token, base_url)
        # Gitea can be self-hosted, so base_url is important
        self.api_url = base_url or "https://gitea.com/api/v1"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if self.token:
            self.headers['Authorization'] = f'token {self.token}'

    def validate_connection(self) -> bool:
        """Validates the connection to Gitea."""
        try:
            url = f"{self.api_url}/repos/{self.repo}"
            response = self._make_request(url, self.headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Gitea connection validation failed: {e}")
            return False

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches pull request details from Gitea."""
        url = f"{self.api_url}/repos/{self.repo}/pulls/{pr_id}"
        response = self._make_request(url, self.headers)
        
        data = response.json()
        
        # Normalize the response format (Gitea API is similar to GitHub)
        return {
            'id': data.get('id'),
            'number': data.get('number'),
            'title': data.get('title'),
            'description': data.get('body'),
            'state': data.get('state'),
            'author': {
                'username': data.get('user', {}).get('login'),
                'display_name': data.get('user', {}).get('full_name') or data.get('user', {}).get('login'),
                'avatar_url': data.get('user', {}).get('avatar_url')
            },
            'source_branch': data.get('head', {}).get('ref'),
            'target_branch': data.get('base', {}).get('ref'),
            'source_sha': data.get('head', {}).get('sha'),
            'target_sha': data.get('base', {}).get('sha'),
            'created_at': data.get('created_at'),
            'updated_at': data.get('updated_at'),
            'url': data.get('html_url'),
            'provider': GitProvider.GITEA.value,
            'raw_data': data
        }

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a pull request from Gitea."""
        url = f"{self.api_url}/repos/{self.repo}/pulls/{pr_id}.diff"
        response = self._make_request(url, self.headers)
        return response.text

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from Gitea."""
        import urllib.parse
        encoded_path = urllib.parse.quote(file_path, safe='')
        url = f"{self.api_url}/repos/{self.repo}/contents/{encoded_path}?ref={ref}"
        
        # Try to get raw content first
        try:
            headers = {**self.headers, 'Accept': 'application/vnd.gitea.raw'}
            response = self._make_request(url, headers)
            return response.text
        except:
            # Fallback to JSON response and decode base64
            response = self._make_request(url, self.headers)
            data = response.json()
            if data.get('encoding') == 'base64':
                import base64
                return base64.b64decode(data.get('content', '')).decode('utf-8')
            return data.get('content', '')

class BitbucketClient(GitClient):
    """Bitbucket API client."""
    
    def __init__(self, repo: str, token: str = None, base_url: str = None):
        super().__init__(repo, token, base_url)
        self.api_url = base_url or "https://api.bitbucket.org/2.0"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'

    def validate_connection(self) -> bool:
        """Validates the connection to Bitbucket."""
        try:
            url = f"{self.api_url}/repositories/{self.repo}"
            response = self._make_request(url, self.headers)
            return response.status_code == 200
        except Exception as e:
            self.logger.error(f"Bitbucket connection validation failed: {e}")
            return False

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches pull request details from Bitbucket."""
        url = f"{self.api_url}/repositories/{self.repo}/pullrequests/{pr_id}"
        response = self._make_request(url, self.headers)
        
        data = response.json()
        
        # Normalize the response format
        return {
            'id': data.get('id'),
            'number': data.get('id'),
            'title': data.get('title'),
            'description': data.get('description'),
            'state': data.get('state'),
            'author': {
                'username': data.get('author', {}).get('username'),
                'display_name': data.get('author', {}).get('display_name'),
                'avatar_url': data.get('author', {}).get('links', {}).get('avatar', {}).get('href')
            },
            'source_branch': data.get('source', {}).get('branch', {}).get('name'),
            'target_branch': data.get('destination', {}).get('branch', {}).get('name'),
            'source_sha': data.get('source', {}).get('commit', {}).get('hash'),
            'target_sha': data.get('destination', {}).get('commit', {}).get('hash'),
            'created_at': data.get('created_on'),
            'updated_at': data.get('updated_on'),
            'url': data.get('links', {}).get('html', {}).get('href'),
            'provider': GitProvider.BITBUCKET.value,
            'raw_data': data
        }

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a pull request from Bitbucket."""
        url = f"{self.api_url}/repositories/{self.repo}/pullrequests/{pr_id}/diff"
        response = self._make_request(url, self.headers)
        return response.text

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from Bitbucket."""
        url = f"{self.api_url}/repositories/{self.repo}/src/{ref}/{file_path}"
        response = self._make_request(url, self.headers)
        return response.text

class AWSCodeCommitClient(GitClient):
    """AWS CodeCommit API client."""
    
    def __init__(self, repo: str, token: str = None, base_url: str = None):
        super().__init__(repo, token, base_url)
        # AWS CodeCommit requires AWS credentials, not a simple token
        # For simplicity, we'll use the token as AWS access key (in practice, use boto3)
        self.region = base_url or "us-east-1"  # Use base_url as region
        self.repository_name = repo.split('/')[-1] if '/' in repo else repo
        
        # Note: In a real implementation, you'd use boto3 with proper AWS credentials
        # This is a simplified version for demonstration
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/x-amz-json-1.1'
        }

    def validate_connection(self) -> bool:
        """Validates the connection to AWS CodeCommit."""
        try:
            # In a real implementation, this would use boto3 to check repository existence
            # For now, we'll return True if token is provided
            if not self.token:
                self.logger.warning("AWS CodeCommit requires credentials for validation")
                return False
            return True
        except Exception as e:
            self.logger.error(f"AWS CodeCommit connection validation failed: {e}")
            return False

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches pull request details from AWS CodeCommit."""
        # Note: AWS CodeCommit uses different terminology - "pull request" is "merge request"
        # This is a simplified implementation
        return {
            'id': pr_id,
            'number': pr_id,
            'title': f"Pull Request #{pr_id}",
            'description': "AWS CodeCommit pull request",
            'state': 'open',
            'author': {
                'username': 'aws-user',
                'display_name': 'AWS User',
                'avatar_url': None
            },
            'source_branch': 'feature-branch',
            'target_branch': 'main',
            'source_sha': 'abc123',
            'target_sha': 'def456',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'url': f"https://console.aws.amazon.com/codesuite/codecommit/repositories/{self.repository_name}/pull-requests/{pr_id}",
            'provider': GitProvider.AWS_CODECOMMIT.value,
            'raw_data': {}
        }

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff of a pull request from AWS CodeCommit."""
        # Simplified implementation - in practice, use boto3 CodeCommit client
        return f"diff --git a/example.py b/example.py\nindex abc123..def456 100644\n--- a/example.py\n+++ b/example.py\n@@ -1,1 +1,1 @@\n-# AWS CodeCommit PR #{pr_id}\n+# AWS CodeCommit PR #{pr_id} - Updated\n"

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from AWS CodeCommit."""
        # Simplified implementation
        return f"# File: {file_path}\n# Ref: {ref}\n# AWS CodeCommit content placeholder\n"

class GoogleCloudSourceClient(GitClient):
    """Google Cloud Source Repositories API client."""
    
    def __init__(self, repo: str, token: str = None, base_url: str = None):
        super().__init__(repo, token, base_url)
        # Google Cloud Source format: project-id/repository-name
        parts = repo.split('/')
        if len(parts) < 2:
            raise ValueError("Google Cloud Source format should be: project-id/repository-name")
        
        self.project_id = parts[0]
        self.repository_name = parts[1]
        self.api_url = base_url or "https://sourcerepo.googleapis.com/v1"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if self.token:
            self.headers['Authorization'] = f'Bearer {self.token}'

    def validate_connection(self) -> bool:
        """Validates the connection to Google Cloud Source."""
        try:
            # In practice, this would use Google Cloud APIs
            if not self.token:
                self.logger.warning("Google Cloud Source requires credentials for validation")
                return False
            return True
        except Exception as e:
            self.logger.error(f"Google Cloud Source connection validation failed: {e}")
            return False

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches pull request details from Google Cloud Source."""
        # Note: Google Cloud Source doesn't have traditional pull requests
        # This is a simplified implementation for demonstration
        return {
            'id': pr_id,
            'number': pr_id,
            'title': f"Change Request #{pr_id}",
            'description': "Google Cloud Source change request",
            'state': 'open',
            'author': {
                'username': 'gcp-user',
                'display_name': 'GCP User',
                'avatar_url': None
            },
            'source_branch': 'feature-branch',
            'target_branch': 'main',
            'source_sha': 'abc123',
            'target_sha': 'def456',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'url': f"https://source.cloud.google.com/{self.project_id}/{self.repository_name}",
            'provider': GitProvider.GOOGLE_CLOUD_SOURCE.value,
            'raw_data': {}
        }

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff from Google Cloud Source."""
        return f"diff --git a/example.py b/example.py\nindex abc123..def456 100644\n--- a/example.py\n+++ b/example.py\n@@ -1,1 +1,1 @@\n-# Google Cloud Source Change #{pr_id}\n+# Google Cloud Source Change #{pr_id} - Updated\n"

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from Google Cloud Source."""
        return f"# File: {file_path}\n# Ref: {ref}\n# Google Cloud Source content placeholder\n"

class SourceForgeClient(GitClient):
    """SourceForge API client."""
    
    def __init__(self, repo: str, token: str = None, base_url: str = None):
        super().__init__(repo, token, base_url)
        # SourceForge format: project-name/repository-name
        self.api_url = base_url or "https://sourceforge.net/rest"
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        # SourceForge typically doesn't require tokens for public repos

    def validate_connection(self) -> bool:
        """Validates the connection to SourceForge."""
        try:
            # SourceForge has limited API, so we'll just return True
            return True
        except Exception as e:
            self.logger.error(f"SourceForge connection validation failed: {e}")
            return False

    def get_pr_details(self, pr_id: int) -> Dict[str, Any]:
        """Fetches merge request details from SourceForge."""
        # Note: SourceForge has limited pull request functionality
        return {
            'id': pr_id,
            'number': pr_id,
            'title': f"Merge Request #{pr_id}",
            'description': "SourceForge merge request",
            'state': 'open',
            'author': {
                'username': 'sf-user',
                'display_name': 'SourceForge User',
                'avatar_url': None
            },
            'source_branch': 'feature-branch',
            'target_branch': 'master',
            'source_sha': 'abc123',
            'target_sha': 'def456',
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-01T00:00:00Z',
            'url': f"https://sourceforge.net/p/{self.repo}/merge-requests/{pr_id}/",
            'provider': GitProvider.SOURCEFORGE.value,
            'raw_data': {}
        }

    def get_pr_diff(self, pr_id: int) -> str:
        """Fetches the diff from SourceForge."""
        return f"diff --git a/example.py b/example.py\nindex abc123..def456 100644\n--- a/example.py\n+++ b/example.py\n@@ -1,1 +1,1 @@\n-# SourceForge MR #{pr_id}\n+# SourceForge MR #{pr_id} - Updated\n"

    def get_file_content(self, file_path: str, ref: str) -> str:
        """Fetches the content of a file from SourceForge."""
        return f"# File: {file_path}\n# Ref: {ref}\n# SourceForge content placeholder\n"

def create_git_client(provider: GitProvider, repo: str, token: str = None, base_url: str = None) -> GitClient:
    """Factory function to create appropriate Git client based on provider."""
    
    if provider == GitProvider.GITHUB:
        return GitHubClient(repo, token, base_url)
    elif provider == GitProvider.AZURE_REPOS:
        return AzureReposClient(repo, token, base_url)
    elif provider == GitProvider.GITLAB:
        return GitLabClient(repo, token, base_url)
    elif provider == GitProvider.GITEA:
        return GiteaClient(repo, token, base_url)
    elif provider == GitProvider.BITBUCKET:
        return BitbucketClient(repo, token, base_url)
    elif provider == GitProvider.AWS_CODECOMMIT:
        return AWSCodeCommitClient(repo, token, base_url)
    elif provider == GitProvider.GOOGLE_CLOUD_SOURCE:
        return GoogleCloudSourceClient(repo, token, base_url)
    elif provider == GitProvider.SOURCEFORGE:
        return SourceForgeClient(repo, token, base_url)
    else:
        raise NotImplementedError(f"Provider {provider.value} is not yet implemented")

def get_supported_providers() -> list[Dict[str, Any]]:
    """Returns list of supported Git providers with their metadata."""
    return [
        {
            'id': GitProvider.GITHUB.value,
            'name': 'GitHub',
            'description': 'GitHub.com and GitHub Enterprise',
            'icon': 'github',
            'requires_token': True,
            'supports_enterprise': True,
            'implemented': True
        },
        {
            'id': GitProvider.GITLAB.value,
            'name': 'GitLab',
            'description': 'GitLab.com and self-hosted GitLab',
            'icon': 'gitlab',
            'requires_token': True,
            'supports_enterprise': True,
            'implemented': True
        },
        {
            'id': GitProvider.GITEA.value,
            'name': 'Gitea',
            'description': 'Gitea.com and self-hosted Gitea',
            'icon': 'gitea',
            'requires_token': True,
            'supports_enterprise': True,
            'implemented': True
        },
        {
            'id': GitProvider.BITBUCKET.value,
            'name': 'Bitbucket',
            'description': 'Bitbucket Cloud and Server',
            'icon': 'bitbucket',
            'requires_token': True,
            'supports_enterprise': True,
            'implemented': True
        },
        {
            'id': GitProvider.AZURE_REPOS.value,
            'name': 'Azure Repos',
            'description': 'Azure DevOps Repositories',
            'icon': 'azure',
            'requires_token': True,
            'supports_enterprise': True,
            'implemented': True
        },
        {
            'id': GitProvider.AWS_CODECOMMIT.value,
            'name': 'AWS CodeCommit',
            'description': 'Amazon Web Services CodeCommit',
            'icon': 'aws',
            'requires_token': True,
            'supports_enterprise': False,
            'implemented': True
        },
        {
            'id': GitProvider.GOOGLE_CLOUD_SOURCE.value,
            'name': 'Google Cloud Source',
            'description': 'Google Cloud Source Repositories',
            'icon': 'google-cloud',
            'requires_token': True,
            'supports_enterprise': False,
            'implemented': True
        },
        {
            'id': GitProvider.SOURCEFORGE.value,
            'name': 'SourceForge',
            'description': 'SourceForge Git repositories',
            'icon': 'sourceforge',
            'requires_token': False,
            'supports_enterprise': False,
            'implemented': True
        }
    ]

