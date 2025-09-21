# src/pr_review_agent/generate_feedback.py

import os
from typing import List, Dict, Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
import dotenv
dotenv.load_dotenv()

def generate_ai_feedback(analysis_results: List[Dict[str, Any]], diff: str) -> Dict[str, Any]:
    """
    Generates AI-driven feedback based on analysis results and a PR diff.

    Args:
        analysis_results: A list of issues found during static analysis.
        diff: The raw diff string of the pull request.

    Returns:
        A formatted, AI-generated feedback string.
    """
    print("Generating AI feedback with LangChain and Gemini...")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {
            "summary": "AI Feedback Skipped. To enable, set the GEMINI_API_KEY environment variable.",
            "comments": [],
            "overall_score": 0,
            "scores": {},
            "markdown_summary": "### AI Feedback Skipped\n\nTo enable AI-powered feedback, please set the `GEMINI_API_KEY` environment variable."
        }

    # Create the comprehensive Chain of Thought prompt template
    prompt_template = """You are an expert senior software engineer and code reviewer with deep knowledge across multiple programming languages, frameworks, and software engineering best practices. Your role is to provide constructive, actionable feedback on code changes in pull requests.

## Chain of Thought Analysis Process

Follow this systematic approach to analyze the code changes:

### Step 1: Initial Understanding
First, analyze the provided information:
- **Context Assessment**: What is this PR trying to achieve?
- **Change Scope**: Are these bug fixes, features, refactoring, or maintenance?
- **Static Analysis Context**: What issues were already detected by automated tools?

**Static Analysis Results:**
{analysis_results}

**Code Diff to Review:**
```diff
{diff}
```

### Step 2: Multi-Dimensional Code Analysis
Now systematically evaluate across these dimensions:

#### 2.1 Code Quality & Structure Analysis
- Readability: Is the code easy to understand?
- Maintainability: Will this be easy to modify later?
- Complexity: Are there overly complex functions?
- DRY Principle: Any code duplications?
- Single Responsibility: Clear, focused purposes?

#### 2.2 Standards & Conventions Check
- Naming: Clear, consistent variable/function names?
- Code Style: Following language conventions?
- Documentation: Adequate comments/docstrings?
- Type Safety: Proper type hints/annotations?

#### 2.3 Security & Reliability Assessment
- Logic Errors: Could this produce wrong results?
- Edge Cases: Are boundary conditions handled?
- Security Risks: Any vulnerabilities (injection, XSS, etc.)?
- Error Handling: Proper exception management?
- Performance: Any potential bottlenecks?

#### 2.4 Testing & Best Practices
- Test Coverage: Are changes tested?
- Backwards Compatibility: Breaking changes?
- Resource Management: Efficient memory/file handling?

### Step 3: Feedback Generation
Based on your analysis, provide feedback with these severity levels:
- **CRITICAL**: Security vulnerabilities, logic errors breaking functionality
- **MAJOR**: Performance issues, maintainability problems, missing error handling
- **MINOR**: Style inconsistencies, minor optimizations, documentation gaps
- **SUGGESTION**: Best practice recommendations, alternative approaches
- **POSITIVE**: Good practices, clever solutions, improvements

### Step 4: Scoring Criteria
Rate each dimension 1-10:
- **Structure & Design**: Code organization, architecture, modularity
- **Standards Compliance**: Following conventions, style guidelines
- **Security & Safety**: Vulnerability management, error handling
- **Performance**: Efficiency, resource usage, scalability
- **Testing & Reliability**: Test coverage, edge case handling

## Required JSON Output Format

Provide your response as a JSON object with these exact keys:

```json
{{
    "thinking_process": "Your step-by-step analysis following the Chain of Thought process above. Be thorough but concise.",
    "summary": "High-level overview of the changes and your overall assessment. Include both strengths and concerns.",
    "comments": [
        {{
            "file_path": "path/to/file.py",
            "line": 42,
            "severity": "MAJOR|MINOR|CRITICAL|SUGGESTION|POSITIVE",
            "category": "Security|Performance|Style|Logic|Best Practice",
            "comment": "Specific, actionable feedback with clear explanation of the issue and suggested improvement",
            "suggestion": "Concrete code example or improvement recommendation (optional)"
        }}
    ],
    "scores": {{
        "structure_design": 8,
        "standards_compliance": 7,
        "security_safety": 9,
        "performance": 6,
        "testing_reliability": 5
    }},
    "overall_score": 7.0,
    "recommendations": [
        "High-level actionable recommendations for improving the PR",
        "Focus on the most impactful changes"
    ],
    "positive_highlights": [
        "Specific things the developer did well",
        "Good practices or clever solutions to acknowledge"
    ]
}}
```

## Guidelines for Quality Feedback

1. **Be Specific**: Instead of "function is complex", say "function has cyclomatic complexity of 12, consider breaking into smaller functions"
2. **Explain Why**: Connect suggestions to maintainability, performance, or security benefits
3. **Provide Solutions**: Don't just identify problems, offer concrete fixes
4. **Stay Professional**: Use collaborative language, focus on code not developer
5. **Balance**: Include both improvements needed AND things done well

## Special Instructions

- If no significant issues found, focus on positive feedback and minor suggestions
- For critical issues, prioritize them and explain the potential impact clearly
- Use line numbers from the diff context (use line 0 for general file-level comments)
- Include code examples in suggestions when helpful
- Consider the broader codebase impact, not just the changed lines

Now, analyze the provided code diff and static analysis results following this Chain of Thought process and provide comprehensive feedback in the required JSON format."""
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    # Initialize the model with better configuration
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", 
        google_api_key=api_key,
        temperature=0.1,  # Lower temperature for more consistent analysis
        max_tokens=4096   # Ensure enough space for comprehensive feedback
    )
    
    # Create the chain
    chain = prompt | llm | JsonOutputParser()
    
    # Format the analysis results for the prompt
    formatted_analysis = []
    for res in analysis_results:
        if res.get('file') != 'N/A':
            formatted_analysis.append(f"- **{res['file']}:{res['line']}** [{res.get('severity', 'UNKNOWN')}]: {res['issue']}")
        else:
            formatted_analysis.append(f"- **General**: {res['issue']}")
    
    formatted_analysis_str = "\n".join(formatted_analysis) if formatted_analysis else "No static analysis issues found."

    try:
        # Invoke the chain
        ai_feedback = chain.invoke({
            "analysis_results": formatted_analysis_str,
            "diff": diff[:8000]  # Limit diff size to prevent token overflow
        })

        # Ensure required keys exist with defaults
        ai_feedback.setdefault('summary', 'No summary provided.')
        ai_feedback.setdefault('comments', [])
        ai_feedback.setdefault('scores', {})
        ai_feedback.setdefault('overall_score', 0)
        ai_feedback.setdefault('recommendations', [])
        ai_feedback.setdefault('positive_highlights', [])

        # Generate comprehensive markdown summary
        markdown_summary = generate_markdown_summary(ai_feedback)
        ai_feedback['markdown_summary'] = markdown_summary
        
        return ai_feedback
        
    except Exception as e:
        print(f"Error generating AI feedback: {e}")
        return {
            "summary": f"AI Feedback Failed: {str(e)}",
            "comments": [],
            "overall_score": 0,
            "scores": {},
            "recommendations": [],
            "positive_highlights": [],
            "markdown_summary": f"### AI Feedback Failed\n\nAn error occurred while generating AI feedback: {str(e)}"
        }


def generate_markdown_summary(ai_feedback: Dict[str, Any]) -> str:
    """Generate a comprehensive markdown summary from AI feedback."""
    
    markdown = f"# 🔍 AI-Powered Code Review\n\n"
    
    # Overall Assessment
    markdown += f"## 📊 Overall Assessment\n\n"
    markdown += f"**Summary**: {ai_feedback.get('summary', 'No summary available.')}\n\n"
    
    # Scores
    if ai_feedback.get('scores'):
        markdown += f"**Quality Score**: {ai_feedback.get('overall_score', 0):.1f}/10\n\n"
        markdown += f"### Detailed Scores\n"
        scores = ai_feedback['scores']
        markdown += f"- 🏗️ **Structure & Design**: {scores.get('structure_design', 0)}/10\n"
        markdown += f"- 📋 **Standards Compliance**: {scores.get('standards_compliance', 0)}/10\n"
        markdown += f"- 🔒 **Security & Safety**: {scores.get('security_safety', 0)}/10\n"
        markdown += f"- ⚡ **Performance**: {scores.get('performance', 0)}/10\n"
        markdown += f"- 🧪 **Testing & Reliability**: {scores.get('testing_reliability', 0)}/10\n\n"
    
    # Positive Highlights
    if ai_feedback.get('positive_highlights'):
        markdown += f"## ✅ What You Did Well\n\n"
        for highlight in ai_feedback['positive_highlights']:
            markdown += f"- {highlight}\n"
        markdown += f"\n"
    
    # Comments by Severity
    comments = ai_feedback.get('comments', [])
    if comments:
        # Group comments by severity
        severity_groups = {
            'CRITICAL': [],
            'MAJOR': [],
            'MINOR': [],
            'SUGGESTION': [],
            'POSITIVE': []
        }
        
        for comment in comments:
            severity = comment.get('severity', 'MINOR')
            severity_groups[severity].append(comment)
        
        # Critical Issues
        if severity_groups['CRITICAL']:
            markdown += f"## 🔴 Critical Issues\n\n"
            for comment in severity_groups['CRITICAL']:
                markdown += format_comment_markdown(comment)
        
        # Major Issues
        if severity_groups['MAJOR']:
            markdown += f"## 🟠 Major Issues\n\n"
            for comment in severity_groups['MAJOR']:
                markdown += format_comment_markdown(comment)
        
        # Minor Issues
        if severity_groups['MINOR']:
            markdown += f"## 🟡 Minor Issues\n\n"
            for comment in severity_groups['MINOR']:
                markdown += format_comment_markdown(comment)
        
        # Suggestions
        if severity_groups['SUGGESTION']:
            markdown += f"## 💡 Suggestions for Improvement\n\n"
            for comment in severity_groups['SUGGESTION']:
                markdown += format_comment_markdown(comment)
    
    # Recommendations
    if ai_feedback.get('recommendations'):
        markdown += f"## 🎯 Key Recommendations\n\n"
        for rec in ai_feedback['recommendations']:
            markdown += f"- {rec}\n"
        markdown += f"\n"
    
    return markdown


def format_comment_markdown(comment: Dict[str, Any]) -> str:
    """Format a single comment as markdown."""
    file_path = comment.get('file_path', 'Unknown')
    line = comment.get('line', 0)
    category = comment.get('category', 'General')
    comment_text = comment.get('comment', 'No comment provided.')
    suggestion = comment.get('suggestion', '')
    
    markdown = f"### 📝 {file_path}:{line} - {category}\n\n"
    markdown += f"{comment_text}\n\n"
    
    if suggestion:
        markdown += f"**💡 Suggestion:**\n```\n{suggestion}\n```\n\n"
    
    return markdown