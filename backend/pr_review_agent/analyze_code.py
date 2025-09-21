# src/pr_review_agent/analyze_code.py

import re
import subprocess
import tempfile
from typing import List, Dict, Any, Tuple
from .fetch_pr import GitClient

def parse_diff(diff: str) -> List[Dict[str, Any]]:
    """
    Parses a git diff and extracts changed files and added lines.

    Args:
        diff: The raw diff string.

    Returns:
        A list of dictionaries, each representing a changed file.
    """
    changed_files = []
    # Regex to find file paths in the diff
    file_path_pattern = re.compile(r'^\+\+\+ b/(.*)$', re.MULTILINE)
    
    # Split diff by file
    file_diffs = re.split(r'^diff --git', diff, flags=re.MULTILINE)[1:]

    for file_diff in file_diffs:
        file_path_match = file_path_pattern.search(file_diff)
        if not file_path_match:
            continue
        
        file_path = file_path_match.group(1)
        
        added_lines: List[Tuple[int, str]] = []
        
        # Regex to find hunk headers (e.g., @@ -15,7 +15,8 @@)
        hunk_pattern = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@', re.MULTILINE)
        
        hunks = hunk_pattern.split(file_diff)[1:]
        
        for i in range(0, len(hunks), 2):
            try:
                start_line = int(hunks[i])
                hunk_content = hunks[i+1]
                current_line_number = start_line
                
                for line in hunk_content.splitlines():
                    if line.startswith('+'):
                        added_lines.append((current_line_number, line[1:]))
                        current_line_number += 1
                    elif not line.startswith('-'):
                        current_line_number += 1
            except (ValueError, IndexError):
                continue

        if added_lines:
            changed_files.append({
                "file_path": file_path,
                "added_lines": added_lines
            })
            
    return changed_files

def analyze_file_with_flake8(file_content: str) -> List[Dict[str, Any]]:
    """Runs flake8 on a given file content and returns the issues."""
    issues = []
    # Ensure utf-8 encoding is used for the temp file to handle all characters
    with tempfile.NamedTemporaryFile(mode='w+', suffix='.py', delete=False, encoding='utf-8') as temp_file:
        temp_file.write(file_content)
        temp_file_path = temp_file.name
    
    try:
        # The --select option can be used to specify which checks to run
        result = subprocess.run(
            ['flake8', '--select=F821,F822,F841,E111,E112,E113', temp_file_path],
            capture_output=True,
            text=True,
            encoding='utf-8', # Explicitly set encoding to utf-8
            check=False # Do not raise exception on non-zero exit code
        )
        
        # Regex to parse flake8 output, which can be complex on Windows
        # Format: path:line:col: code message
        flake8_pattern = re.compile(r'^.+?:(\d+):(\d+): (.+)$')

        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            match = flake8_pattern.match(line)
            if match:
                line_num, col_num, message_body = match.groups()
                error_code = message_body.split(' ')[0]
                message = ' '.join(message_body.split(' ')[1:])
                
                issues.append({
                    "line": int(line_num),
                    "column": int(col_num),
                    "code": error_code,
                    "message": message
                })
    finally:
        import os
        os.remove(temp_file_path)

    return issues

def analyze_pr_diff(diff: str, client: GitClient, head_sha: str) -> List[Dict[str, Any]]:
    """
    Analyzes the diff of a pull request.

    Args:
        diff: The PR diff string.

    Returns:
        A list of analysis results.
    """
    print("Analyzing PR diff with flake8...")
    changed_py_files = [f for f in parse_diff(diff) if f['file_path'].endswith('.py')]
    analysis_results = []

    for file_info in changed_py_files:
        file_path = file_info['file_path']
        try:
            # Fetch the full file content at the PR's head commit
            file_content = client.get_file_content(file_path, head_sha)
            flake8_issues = analyze_file_with_flake8(file_content)
            
            # Filter issues to only those on added lines
            added_lines_nums = {line_num for line_num, _ in file_info['added_lines']}
            for issue in flake8_issues:
                if issue['line'] in added_lines_nums:
                    analysis_results.append({
                        "file": file_path,
                        "line": issue['line'],
                        "issue": f"{issue['code']}: {issue['message']}"
                    })
        except Exception as e:
            print(f"Could not analyze file {file_path}: {e}")

    # If no issues are found, provide a positive message
    if not analysis_results:
        analysis_results.append({
            "file": "N/A",
            "line": 0,
            "issue": "No flake8 issues found in the changed Python files. Great work!"
        })

    return analysis_results
