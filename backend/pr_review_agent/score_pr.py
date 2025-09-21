# src/pr_review_agent/score_pr.py

from typing import List, Dict, Any
from radon.complexity import cc_visit

def calculate_pr_score(analysis_results: List[Dict[str, Any]], file_contents: Dict[str, str]) -> int:
    """Calculates a quality score for a PR based on various metrics."""
    score = 100
    deductions = []

    # Deduction for static analysis issues
    num_issues = len([res for res in analysis_results if res['file'] != 'N/A'])
    if num_issues > 0:
        issue_deduction = min(num_issues * 5, 30)
        deductions.append(f"-{issue_deduction} for {num_issues} static analysis issues.")
        score -= issue_deduction

    # Deduction for high complexity
    total_complexity = 0
    num_functions = 0
    for file_path, content in file_contents.items():
        if file_path.endswith('.py'):
            try:
                blocks = cc_visit(content)
                for block in blocks:
                    total_complexity += block.complexity
                    num_functions += 1
            except Exception:
                pass # Radon might fail on some files
    
    if num_functions > 0:
        avg_complexity = total_complexity / num_functions
        if avg_complexity > 10:
            complexity_deduction = min(int((avg_complexity - 10) * 5), 30)
            deductions.append(f"-{complexity_deduction} for high average complexity ({avg_complexity:.1f}).")
            score -= complexity_deduction

    # A simple heuristic for AI feedback could be added here
    # For now, we'll just base it on the existing metrics

    print("\n--- PR Scoring Breakdown ---")
    if not deductions:
        print("No deductions. Excellent work!")
    else:
        for deduction in deductions:
            print(deduction)
    print("--------------------------")

    return max(0, score)
