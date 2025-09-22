import unittest
from unittest.mock import patch, MagicMock
from pr_review_agent.fetch_pr import (
    GitHubClient, GitLabClient, BitbucketClient, GiteaClient, 
    AzureReposClient, create_git_client, GitProvider
)

class TestGitHubClient(unittest.TestCase):

    @patch('requests.get')
    def test_get_pr_details(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'title': 'Test PR'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = GitHubClient('test/repo', token='test_token')
        details = client.get_pr_details(1)

        self.assertEqual(details['title'], 'Test PR')

    @patch('requests.get')
    def test_get_pr_diff(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = 'diff --git a/file.py b/file.py'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = GitHubClient('test/repo', token='test_token')
        diff = client.get_pr_diff(1)

        self.assertEqual(diff, 'diff --git a/file.py b/file.py')

    @patch('requests.get')
    def test_get_file_content(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = 'print("hello world")'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = GitHubClient('test/repo', token='test_token')
        content = client.get_file_content('file.py', 'main')

        self.assertEqual(content, 'print("hello world")')

class TestGitLabClient(unittest.TestCase):

    @patch('gitlab.Gitlab')
    def test_get_pr_details(self, mock_gitlab):
        mock_project = MagicMock()
        mock_mr = MagicMock()
        mock_mr.attributes = {'title': 'Test MR'}
        mock_project.mergerequests.get.return_value = mock_mr
        mock_gitlab.return_value.projects.get.return_value = mock_project

        client = GitLabClient('test/repo', token='test_token')
        details = client.get_pr_details(1)

        self.assertEqual(details['title'], 'Test MR')

    @patch('gitlab.Gitlab')
    def test_get_pr_diff(self, mock_gitlab):
        mock_project = MagicMock()
        mock_mr = MagicMock()
        mock_mr.changes.return_value = {'changes': [{'diff': 'diff --git a/file.py b/file.py'}]}
        mock_project.mergerequests.get.return_value = mock_mr
        mock_gitlab.return_value.projects.get.return_value = mock_project

        client = GitLabClient('test/repo', token='test_token')
        diff = client.get_pr_diff(1)

        self.assertEqual(diff, 'diff --git a/file.py b/file.py')

    @patch('gitlab.Gitlab')
    def test_get_file_content(self, mock_gitlab):
        mock_project = MagicMock()
        mock_file = MagicMock()
        mock_file.content = 'cHJpbnQoImhlbGxvIHdvcmxkIik='
        mock_project.files.get.return_value = mock_file
        mock_gitlab.return_value.projects.get.return_value = mock_project

        client = GitLabClient('test/repo', token='test_token')
        content = client.get_file_content('file.py', 'main')

        self.assertEqual(content, 'print("hello world")')

class TestBitbucketClient(unittest.TestCase):

    @patch('requests.get')
    def test_get_pr_details(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {'title': 'Test PR'}
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = BitbucketClient('test/repo', token='test_token')
        details = client.get_pr_details(1)

        self.assertEqual(details['title'], 'Test PR')

    @patch('requests.get')
    def test_get_pr_diff(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = 'diff --git a/file.py b/file.py'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = BitbucketClient('test/repo', token='test_token')
        diff = client.get_pr_diff(1)

        self.assertEqual(diff, 'diff --git a/file.py b/file.py')

    @patch('requests.get')
    def test_get_file_content(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = 'print("hello world")'
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = BitbucketClient('test/repo', token='test_token')
        content = client.get_file_content('file.py', 'main')

        self.assertEqual(content, 'print("hello world")')

class TestFactoryFunction(unittest.TestCase):

    def test_create_github_client(self):
        client = create_git_client(GitProvider.GITHUB, 'test/repo', 'token')
        self.assertIsInstance(client, GitHubClient)

    def test_create_gitlab_client(self):
        client = create_git_client(GitProvider.GITLAB, 'test/repo', 'token')
        self.assertIsInstance(client, GitLabClient)

    def test_create_gitea_client(self):
        client = create_git_client(GitProvider.GITEA, 'test/repo', 'token')
        self.assertIsInstance(client, GiteaClient)

    def test_create_bitbucket_client(self):
        client = create_git_client(GitProvider.BITBUCKET, 'test/repo', 'token')
        self.assertIsInstance(client, BitbucketClient)

    def test_create_azure_client(self):
        client = create_git_client(GitProvider.AZURE_REPOS, 'org/proj/repo', 'token')
        self.assertIsInstance(client, AzureReposClient)

class TestErrorHandling(unittest.TestCase):

    @patch('requests.request')
    def test_connection_error_handling(self, mock_request):
        mock_request.side_effect = Exception("Network error")
        
        client = GitHubClient('test/repo', 'token')
        
        with self.assertRaises(ConnectionError):
            client._make_request('http://test.com')

    def test_azure_repo_format_validation(self):
        with self.assertRaises(ValueError):
            AzureReposClient('invalid-format', 'token')

if __name__ == '__main__':
    unittest.main()
