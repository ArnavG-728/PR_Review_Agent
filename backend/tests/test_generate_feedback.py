import unittest
from unittest.mock import patch, MagicMock
from pr_review_agent.generate_feedback import smart_truncate_diff, generate_ai_feedback

class TestSmartTruncateDiff(unittest.TestCase):

    def test_short_diff_unchanged(self):
        short_diff = "diff --git a/file.py b/file.py\n+print('hello')"
        result = smart_truncate_diff(short_diff, max_chars=1000)
        self.assertEqual(result, short_diff)

    def test_long_diff_truncated(self):
        long_diff = "diff --git a/file.py b/file.py\n" + "+" + "x" * 9000
        result = smart_truncate_diff(long_diff, max_chars=100)
        self.assertTrue(len(result) <= 100)

    def test_hunk_preservation(self):
        diff_with_hunk = """diff --git a/file.py b/file.py
@@ -1,3 +1,3 @@
 line1
-old line
+new line
 line3"""
        result = smart_truncate_diff(diff_with_hunk, max_chars=50)
        self.assertIn("@@", result)

class TestGenerateAIFeedback(unittest.TestCase):

    def test_no_api_key(self):
        with patch.dict('os.environ', {}, clear=True):
            result = generate_ai_feedback([], "test diff")
            self.assertIn("AI Feedback Skipped", result['summary'])

    @patch('os.getenv')
    def test_with_api_key_but_mock_failure(self, mock_getenv):
        mock_getenv.return_value = "test-key"
        
        with patch('pr_review_agent.generate_feedback.ChatGoogleGenerativeAI') as mock_llm:
            mock_llm.side_effect = Exception("API Error")
            
            result = generate_ai_feedback([], "test diff")
            self.assertIn("AI Feedback Failed", result['summary'])

if __name__ == '__main__':
    unittest.main()
