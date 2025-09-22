# src/pr_review_agent/generate_feedback.py

import os
from typing import List, Dict, Any, Optional
import json
import logging
from datetime import datetime

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
import dotenv

dotenv.load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_ai_feedback(analysis_results: List[Dict[str, Any]], diff: str, 
                        pr_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generates comprehensive AI-driven feedback using advanced prompting techniques.
    
    Args:
        analysis_results: Static analysis issues found
        diff: The raw diff string of the pull request
        pr_context: Optional PR metadata (title, description, files changed, etc.)
    
    Returns:
        Comprehensive AI-generated feedback with mentorship focus
    """
    logger.info("🚀 Generating ultimate AI feedback with advanced reasoning frameworks...")
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _create_fallback_response("GEMINI_API_KEY environment variable not set")
    
    # Create the ultimate prompt with all advanced techniques
    prompt_template = _create_ultimate_prompt_template()
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    # Initialize model with optimized configuration for complex reasoning
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-exp",  # Use experimental model for better reasoning
        google_api_key=api_key,
        temperature=0.15,  # Slight randomness for creative solutions
        max_tokens=8192,   # Maximum tokens for comprehensive analysis
        top_p=0.8,        # Nucleus sampling for quality
    )
    
    # Create the enhanced chain with better error handling
    chain = prompt | llm | JsonOutputParser()
    
    try:
        # Prepare comprehensive input data
        input_data = _prepare_comprehensive_input(analysis_results, diff, pr_context)
        
        # Execute the advanced reasoning chain
        logger.info("🧠 Executing multi-perspective analysis...")
        ai_feedback = chain.invoke(input_data)
        
        # Validate and enhance the response
        ai_feedback = _validate_and_enhance_response(ai_feedback)
        
        # Generate multiple output formats
        ai_feedback['markdown_summary'] = generate_enhanced_markdown_summary(ai_feedback)
        ai_feedback['executive_summary'] = generate_executive_summary(ai_feedback)
        ai_feedback['action_items'] = extract_action_items(ai_feedback)
        
        logger.info(f"✅ Generated feedback with {len(ai_feedback.get('comments', []))} insights")
        return ai_feedback
        
    except OutputParserException as e:
        logger.error(f"JSON parsing failed: {e}")
        return _create_fallback_response(f"AI response parsing failed: {str(e)}")
    except Exception as e:
        logger.error(f"AI feedback generation failed: {e}")
        return _create_fallback_response(f"AI feedback generation failed: {str(e)}")


def _create_ultimate_prompt_template() -> str:
    """Creates the ultimate prompt template with all advanced techniques."""
    return """You are a world-class Senior Staff Engineer and Tech Lead with 15+ years of experience across multiple domains: backend systems, frontend applications, mobile development, DevOps, and distributed systems. You've led code reviews at top-tier companies and mentored hundreds of engineers. Your reviews are known for being thorough, constructive, and educational.

## 🎯 MISSION
Conduct a comprehensive pull request review that identifies issues, validates improvements, and provides mentorship-quality feedback that helps developers grow while maintaining high code quality standards.

## 🧠 ADVANCED REASONING FRAMEWORK

### PHASE 1: MULTI-PERSPECTIVE ANALYSIS (Tree of Thought)
You will analyze this PR from multiple expert perspectives simultaneously:

**🔒 Security Engineer Perspective:**
- Threat modeling: What attack vectors could this code introduce?
- Input validation, output encoding, authentication/authorization
- Dependency vulnerabilities, secrets management
- Data privacy and compliance considerations

**⚡ Performance Engineer Perspective:**  
- Algorithmic complexity analysis (time/space)
- Database query optimization, N+1 problems
- Memory leaks, resource management
- Caching strategies, network efficiency
- Scalability bottlenecks

**🏗️ Software Architect Perspective:**
- Design patterns and anti-patterns
- SOLID principles adherence
- System boundaries, coupling/cohesion
- Technical debt implications
- Future extensibility considerations

**🧪 Quality Assurance Perspective:**
- Testability and test coverage gaps
- Edge cases and error scenarios  
- Integration points and failure modes
- Observability and debugging support

**👥 Team Lead Perspective:**
- Code maintainability and readability
- Knowledge sharing and documentation
- Onboarding impact for new team members
- Consistency with team conventions

### PHASE 2: REACTIVE REASONING & EVIDENCE GATHERING
Now observe, analyze, and reason about the evidence:

**OBSERVE:** What patterns do I see in this code?
**THINK:** What are the implications of these patterns?  
**ACT:** What specific feedback should I provide?

For each observation:
1. **Evidence**: What specific code construct triggered this observation?
2. **Impact Assessment**: What are the potential consequences?
3. **Context Consideration**: How does this fit within the broader system?
4. **Action Decision**: What type of feedback is most appropriate?

### PHASE 3: FEW-SHOT LEARNING FROM EXEMPLARS
Reference these examples of exceptional code review feedback:

**Example 1 - Security Issue:**
```
❌ CRITICAL: SQL Injection Vulnerability (Line 45)
The user input is concatenated directly into the SQL query without parameterization.

**Risk**: Attackers could execute arbitrary SQL commands, potentially accessing/modifying sensitive data.

**Fix**:
```sql
// Instead of: query = f"SELECT * FROM users WHERE id = {{user_id}}"
query = "SELECT * FROM users WHERE id = %s"
cursor.execute(query, (user_id,))
```

**Why this matters**: Parameterized queries ensure user input is treated as data, not executable code.
```

**Example 2 - Performance Issue:**
```
🟠 MAJOR: O(n²) Performance Issue (Lines 67-72)
The nested loop creates quadratic complexity for processing user lists.

**Impact**: With 1000+ users, this could cause 5+ second delays and potential timeouts.

**Solution**: Use a HashMap for O(1) lookups:
```python
user_lookup = {{user.id: user for user in users}}  # O(n)
for item in items:  # O(n) 
    user = user_lookup.get(item.user_id)  # O(1)
```

**Performance improvement**: Reduces complexity from O(n²) to O(n).
```

**Example 3 - Positive Feedback:**
```
✅ EXCELLENT: Clean Error Handling Pattern (Lines 23-31)
Love the structured error handling with specific exception types and contextual logging.

**What makes this great**:
- Clear exception hierarchy for different failure modes
- Structured logging with correlation IDs for debugging
- Graceful degradation that maintains user experience

This pattern should be adopted across other service calls.
```

### PHASE 4: CRITIQUE AND REVISION PROCESS
Before finalizing feedback, apply this self-critique:

**Accuracy Check**: 
- Is my technical analysis correct?
- Have I made any assumptions that need validation?
- Are my severity assessments appropriate?

**Completeness Check**:
- Did I miss any critical issues?
- Are there positive aspects I should acknowledge?
- Is my feedback actionable and specific?

**Tone and Impact Check**:
- Is my language constructive and growth-oriented?
- Will this feedback help the developer improve?
- Am I balancing criticism with recognition?

**Priority Verification**:
- Are the most critical issues clearly highlighted?
- Is my feedback ordered by impact and urgency?

## 📊 INPUT ANALYSIS

**PR Context:**
{pr_context}

**Static Analysis Results:**
{analysis_results}

**Pull Request Diff:**
```diff
{diff}
```

## 🔄 SYSTEMATIC EVALUATION PROCESS

### Step 1: Context Understanding & Goal Alignment
- **Change Intent**: What problem is this PR solving?
- **Risk Assessment**: What's the blast radius of these changes?
- **Strategic Fit**: How does this align with architectural goals?

### Step 2: Multi-Dimensional Quality Gates

**🔒 Security Evaluation**
- [ ] Input validation and sanitization
- [ ] Authentication and authorization checks  
- [ ] Secrets and sensitive data handling
- [ ] Dependency security scan
- [ ] Output encoding and injection prevention

**⚡ Performance Analysis**
- [ ] Algorithmic complexity assessment
- [ ] Database query efficiency
- [ ] Memory usage patterns
- [ ] Network call optimization
- [ ] Caching strategies

**🏗️ Architecture & Design**
- [ ] SOLID principles adherence
- [ ] Design pattern appropriateness
- [ ] Separation of concerns
- [ ] Dependency management
- [ ] Future extensibility

**📈 Maintainability & Readability**
- [ ] Code clarity and self-documentation
- [ ] Naming conventions and consistency
- [ ] Function/class size and complexity
- [ ] Technical debt implications
- [ ] Documentation quality

**🧪 Testing & Reliability**  
- [ ] Test coverage and quality
- [ ] Edge case handling
- [ ] Error scenarios and recovery
- [ ] Integration test considerations
- [ ] Observability and monitoring

### Step 3: Evidence-Based Scoring
Rate each dimension 1-10 with detailed justification:

- **1-3**: Critical issues requiring immediate attention
- **4-6**: Significant problems impacting quality/maintainability  
- **7-8**: Good quality with minor improvement opportunities
- **9-10**: Exceptional quality, exemplary practices

## 📋 COMPREHENSIVE OUTPUT FORMAT

Provide your analysis as a JSON object with the following structure:

```json
{{
    "meta_analysis": {{
        "change_intent": "What is this PR trying to achieve?",
        "risk_level": "LOW|MEDIUM|HIGH|CRITICAL",
        "complexity_assessment": "Simple|Moderate|Complex|Highly Complex",
        "architectural_impact": "Description of broader system implications"
    }},
    "thinking_process": {{
        "security_analysis": "Detailed security assessment from security engineer perspective",
        "performance_analysis": "Performance implications and bottlenecks identified",
        "architecture_analysis": "Design and architectural considerations",
        "maintainability_analysis": "Code quality and maintainability assessment",
        "testing_analysis": "Test coverage and reliability evaluation"
    }},
    "summary": "Executive summary of the review findings and overall assessment",
    "comments": [
        {{
            "file_path": "path/to/file.py",
            "line": 42,
            "severity": "CRITICAL|MAJOR|MINOR|SUGGESTION|POSITIVE", 
            "category": "Security|Performance|Architecture|Style|Logic|Testing|Documentation",
            "title": "Concise title of the issue",
            "comment": "Detailed explanation of the issue, its impact, and why it matters",
            "evidence": "Specific code snippet or pattern that triggered this feedback",
            "suggestion": "Concrete, actionable solution with code examples when helpful",
            "learning_opportunity": "Educational context to help developer grow",
            "priority": 1
        }}
    ],
    "scores": {{
        "security_safety": 8,
        "performance_efficiency": 7,
        "architecture_design": 9,
        "maintainability_readability": 6,
        "testing_reliability": 5,
        "documentation_clarity": 7
    }},
    "overall_score": 7.2,
    "risk_assessment": {{
        "deployment_readiness": "READY|NEEDS_MINOR_CHANGES|NEEDS_MAJOR_CHANGES|NOT_READY",
        "security_risk": "Description of security implications",
        "performance_risk": "Description of performance implications", 
        "operational_risk": "Description of operational/maintenance implications"
    }},
    "recommendations": {{
        "immediate_actions": ["Critical items that must be addressed before merge"],
        "short_term_improvements": ["Important improvements for next iteration"],
        "long_term_considerations": ["Architectural or strategic improvements to consider"],
        "learning_resources": ["Relevant documentation, articles, or training materials"]
    }},
    "positive_highlights": [
        {{
            "aspect": "What was done well",
            "impact": "Why this is valuable",
            "encouragement": "Specific recognition for the developer"
        }}
    ],
    "mentorship_notes": {{
        "growth_opportunities": "Areas where the developer can continue to improve",
        "strength_recognition": "Specific strengths demonstrated in this PR", 
        "suggested_focus": "What to focus on in future development"
    }}
}}
```

## 🎯 QUALITY STANDARDS FOR EXCEPTIONAL FEEDBACK

### Specificity Requirements
- **Line-specific**: Reference exact line numbers and code constructs
- **Evidence-based**: Quote specific code snippets that demonstrate issues
- **Impact-quantified**: Explain the measurable consequences of issues
- **Solution-oriented**: Provide concrete, implementable fixes

### Educational Value
- **Context-rich**: Explain the "why" behind recommendations  
- **Best-practice grounded**: Reference industry standards and proven patterns
- **Growth-focused**: Frame feedback as learning opportunities
- **Resource-supported**: Suggest relevant documentation or learning materials

### Prioritization Excellence  
- **Risk-weighted**: Critical security/performance issues first
- **Impact-assessed**: Focus on changes that provide maximum value
- **Effort-considered**: Balance improvement impact with implementation effort
- **Strategic-aligned**: Consider long-term architectural goals

### Tone and Delivery
- **Constructive collaboration**: Frame as partnership in code quality
- **Specific recognition**: Acknowledge good practices and improvements  
- **Professional respect**: Maintain collegial, non-judgmental language
- **Actionable guidance**: Ensure all feedback can be acted upon

## 🚀 EXECUTION INSTRUCTIONS

1. **Read and understand** the static analysis results and diff completely
2. **Apply the multi-perspective analysis** framework systematically  
3. **Use reactive reasoning** to gather evidence and assess impact
4. **Reference the few-shot examples** to calibrate feedback quality
5. **Apply critique and revision** to ensure accuracy and completeness
6. **Generate comprehensive JSON output** following the specified format
7. **Ensure all feedback** meets the quality standards outlined above

Your goal is to provide a review that not only identifies issues but actively contributes to the developer's growth and the codebase's long-term health. Make every comment count.

---

**Remember**: Great code reviews balance thorough analysis with constructive mentorship. Your feedback should make the code better AND the developer stronger."""


def _prepare_comprehensive_input(analysis_results: List[Dict[str, Any]], 
                               diff: str, 
                               pr_context: Optional[Dict[str, Any]]) -> Dict[str, str]:
    """Prepare comprehensive input data for the AI model."""
    
    # Enhanced static analysis formatting
    formatted_analysis = _format_static_analysis_results(analysis_results)
    
    # Smart diff truncation with context preservation
    truncated_diff = smart_truncate_diff_enhanced(diff, max_chars=12000)
    
    # PR context formatting
    pr_context_str = _format_pr_context(pr_context)
    
    return {
        "analysis_results": formatted_analysis,
        "diff": truncated_diff,
        "pr_context": pr_context_str
    }


def _format_static_analysis_results(analysis_results: List[Dict[str, Any]]) -> str:
    """Format static analysis results with enhanced categorization."""
    if not analysis_results:
        return "✅ No static analysis issues detected."
    
    # Group by severity for better organization
    severity_groups = {}
    for result in analysis_results:
        severity = result.get('severity', 'UNKNOWN').upper()
        if severity not in severity_groups:
            severity_groups[severity] = []
        severity_groups[severity].append(result)
    
    formatted_sections = []
    severity_order = ['CRITICAL', 'HIGH', 'MAJOR', 'MEDIUM', 'MINOR', 'LOW', 'INFO', 'UNKNOWN']
    
    for severity in severity_order:
        if severity in severity_groups:
            issues = severity_groups[severity]
            formatted_sections.append(f"\n**{severity} Issues ({len(issues)}):**")
            
            for issue in issues:
                file_path = issue.get('file', 'Unknown')
                line = issue.get('line', 'N/A')
                description = issue.get('issue', 'No description')
                rule = issue.get('rule', '')
                
                formatted_sections.append(
                    f"- **{file_path}:{line}** [{rule}]: {description}"
                )
    
    return "\n".join(formatted_sections)


def _format_pr_context(pr_context: Optional[Dict[str, Any]]) -> str:
    """Format PR context information."""
    if not pr_context:
        return "No additional PR context provided."
    
    context_parts = []
    
    if pr_context.get('title'):
        context_parts.append(f"**Title**: {pr_context['title']}")
    
    if pr_context.get('description'):
        context_parts.append(f"**Description**: {pr_context['description']}")
    
    if pr_context.get('files_changed'):
        files = pr_context['files_changed']
        context_parts.append(f"**Files Changed**: {len(files)} files")
        context_parts.append(f"**File List**: {', '.join(files[:10])}")
        if len(files) > 10:
            context_parts.append(f"... and {len(files) - 10} more files")
    
    if pr_context.get('author'):
        context_parts.append(f"**Author**: {pr_context['author']}")
    
    if pr_context.get('branch'):
        context_parts.append(f"**Branch**: {pr_context['branch']}")
    
    return "\n".join(context_parts) if context_parts else "No additional PR context provided."


def smart_truncate_diff_enhanced(diff_text: str, max_chars: int = 12000) -> str:
    """Enhanced diff truncation with better context preservation."""
    if len(diff_text) <= max_chars:
        return diff_text

    lines = diff_text.split('\n')
    truncated_diff = []
    current_chars = 0
    
    # Preserve file headers and important context
    important_line_patterns = [
        lambda line: line.startswith('+++') or line.startswith('---'),  # File headers
        lambda line: line.startswith('@@'),  # Hunk headers
        lambda line: line.startswith('+') or line.startswith('-'),  # Changes
        lambda line: 'TODO' in line or 'FIXME' in line or 'HACK' in line,  # Important comments
    ]
    
    # First pass: collect all important lines
    important_lines = []
    regular_lines = []
    
    for line in lines:
        is_important = any(pattern(line) for pattern in important_line_patterns)
        if is_important:
            important_lines.append(line)
        else:
            regular_lines.append(line)
    
    # Add important lines first
    for line in important_lines:
        if current_chars + len(line) + 1 <= max_chars:
            truncated_diff.append(line)
            current_chars += len(line) + 1
        else:
            break
    
    # Add regular lines if space permits
    for line in regular_lines:
        if current_chars + len(line) + 1 <= max_chars:
            truncated_diff.append(line)
            current_chars += len(line) + 1
        else:
            break
    
    if len(truncated_diff) < len(lines):
        truncated_diff.append(f"\n... [Diff truncated: showing {len(truncated_diff)}/{len(lines)} lines] ...")
    
    return '\n'.join(truncated_diff)


def _validate_and_enhance_response(ai_feedback: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and enhance the AI response with defaults and improvements."""
    
    # Ensure all required top-level keys exist
    default_structure = {
        'meta_analysis': {
            'change_intent': 'Analysis not provided',
            'risk_level': 'MEDIUM',
            'complexity_assessment': 'Moderate',
            'architectural_impact': 'Impact assessment not provided'
        },
        'thinking_process': {
            'security_analysis': 'Security analysis not provided',
            'performance_analysis': 'Performance analysis not provided',
            'architecture_analysis': 'Architecture analysis not provided',
            'maintainability_analysis': 'Maintainability analysis not provided',
            'testing_analysis': 'Testing analysis not provided'
        },
        'summary': 'Summary not provided',
        'comments': [],
        'scores': {
            'security_safety': 5,
            'performance_efficiency': 5,
            'architecture_design': 5,
            'maintainability_readability': 5,
            'testing_reliability': 5,
            'documentation_clarity': 5
        },
        'overall_score': 5.0,
        'risk_assessment': {
            'deployment_readiness': 'NEEDS_MINOR_CHANGES',
            'security_risk': 'No specific security risks identified',
            'performance_risk': 'No specific performance risks identified',
            'operational_risk': 'No specific operational risks identified'
        },
        'recommendations': {
            'immediate_actions': [],
            'short_term_improvements': [],
            'long_term_considerations': [],
            'learning_resources': []
        },
        'positive_highlights': [],
        'mentorship_notes': {
            'growth_opportunities': 'Continue focusing on code quality and best practices',
            'strength_recognition': 'Code demonstrates good understanding of requirements',
            'suggested_focus': 'Consider focusing on testing and documentation'
        }
    }
    
    # Deep merge with defaults
    ai_feedback = _deep_merge_with_defaults(ai_feedback, default_structure)
    
    # Enhance comments with additional metadata
    for comment in ai_feedback.get('comments', []):
        if 'priority' not in comment:
            severity = comment.get('severity', 'MINOR')
            comment['priority'] = _severity_to_priority(severity)
        
        if 'learning_opportunity' not in comment:
            comment['learning_opportunity'] = 'Consider researching best practices for this area'
    
    # Calculate overall score if not provided
    if ai_feedback['overall_score'] == 5.0:  # Default value
        scores = ai_feedback['scores']
        ai_feedback['overall_score'] = round(sum(scores.values()) / len(scores), 1)
    
    # Add timestamp
    ai_feedback['generated_at'] = datetime.utcnow().isoformat()
    ai_feedback['version'] = '2.0'
    
    return ai_feedback


def _deep_merge_with_defaults(target: Dict[str, Any], defaults: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge target dict with defaults."""
    for key, value in defaults.items():
        if key not in target:
            target[key] = value
        elif isinstance(value, dict) and isinstance(target[key], dict):
            target[key] = _deep_merge_with_defaults(target[key], value)
    return target


def _severity_to_priority(severity: str) -> int:
    """Convert severity to priority number."""
    severity_map = {
        'CRITICAL': 1,
        'MAJOR': 2,
        'MINOR': 3,
        'SUGGESTION': 4,
        'POSITIVE': 5
    }
    return severity_map.get(severity.upper(), 3)


def _create_fallback_response(error_message: str) -> Dict[str, Any]:
    """Create a fallback response when AI generation fails."""
    return {
        "meta_analysis": {
            "change_intent": "Unable to analyze due to error",
            "risk_level": "UNKNOWN",
            "complexity_assessment": "Unable to assess",
            "architectural_impact": error_message
        },
        "summary": f"AI feedback generation failed: {error_message}",
        "comments": [],
        "overall_score": 0,
        "scores": {},
        "risk_assessment": {
            "deployment_readiness": "UNKNOWN",
            "security_risk": "Unable to assess",
            "performance_risk": "Unable to assess",
            "operational_risk": "Unable to assess"
        },
        "recommendations": {
            "immediate_actions": ["Fix AI feedback generation"],
            "short_term_improvements": [],
            "long_term_considerations": [],
            "learning_resources": []
        },
        "positive_highlights": [],
        "mentorship_notes": {
            "growth_opportunities": "Unable to provide due to error",
            "strength_recognition": "Unable to assess",
            "suggested_focus": "Fix the feedback generation system"
        },
        "markdown_summary": f"### AI Feedback Failed\n\n{error_message}",
        "executive_summary": f"Failed to generate feedback: {error_message}",
        "action_items": [],
        "generated_at": datetime.utcnow().isoformat(),
        "version": "2.0"
    }


def generate_enhanced_markdown_summary(ai_feedback: Dict[str, Any]) -> str:
    """Generate an enhanced markdown summary with the new structure."""
    
    markdown_parts = []
    
    # Header with meta information
    markdown_parts.append("# 🔍 AI-Powered Code Review Analysis\n")
    
    # Executive dashboard
    meta = ai_feedback.get('meta_analysis', {})
    risk_level = meta.get('risk_level', 'UNKNOWN')
    risk_emoji = {'LOW': '🟢', 'MEDIUM': '🟡', 'HIGH': '🟠', 'CRITICAL': '🔴'}.get(risk_level, '⚪')
    
    markdown_parts.append("## 📊 Executive Dashboard\n")
    markdown_parts.append(f"- **Change Intent**: {meta.get('change_intent', 'Not specified')}")
    markdown_parts.append(f"- **Risk Level**: {risk_emoji} {risk_level}")
    markdown_parts.append(f"- **Complexity**: {meta.get('complexity_assessment', 'Unknown')}")
    markdown_parts.append(f"- **Overall Score**: {ai_feedback.get('overall_score', 0):.1f}/10")
    markdown_parts.append("")
    
    # Risk Assessment
    risk_assessment = ai_feedback.get('risk_assessment', {})
    deployment_readiness = risk_assessment.get('deployment_readiness', 'UNKNOWN')
    deployment_emoji = {
        'READY': '✅',
        'NEEDS_MINOR_CHANGES': '⚠️',
        'NEEDS_MAJOR_CHANGES': '🟠',
        'NOT_READY': '🔴'
    }.get(deployment_readiness, '⚪')
    
    markdown_parts.append("## 🚀 Deployment Readiness")
    markdown_parts.append(f"**Status**: {deployment_emoji} {deployment_readiness}\n")
    
    if risk_assessment.get('security_risk') != 'No specific security risks identified':
        markdown_parts.append(f"**Security Risk**: {risk_assessment.get('security_risk', 'Unknown')}")
    if risk_assessment.get('performance_risk') != 'No specific performance risks identified':
        markdown_parts.append(f"**Performance Risk**: {risk_assessment.get('performance_risk', 'Unknown')}")
    if risk_assessment.get('operational_risk') != 'No specific operational risks identified':
        markdown_parts.append(f"**Operational Risk**: {risk_assessment.get('operational_risk', 'Unknown')}")
    
    markdown_parts.append("")
    
    # Summary
    markdown_parts.append("## 📋 Summary")
    markdown_parts.append(ai_feedback.get('summary', 'No summary provided'))
    markdown_parts.append("")
    
    # Scores breakdown
    scores = ai_feedback.get('scores', {})
    if scores:
        markdown_parts.append("## 📈 Quality Scores")
        for category, score in scores.items():
            score_emoji = "🔴" if score <= 3 else "🟠" if score <= 5 else "🟡" if score <= 7 else "🟢"
            category_display = category.replace('_', ' ').title()
            markdown_parts.append(f"- {score_emoji} **{category_display}**: {score}/10")
        markdown_parts.append("")
    
    # Positive highlights first
    positive_highlights = ai_feedback.get('positive_highlights', [])
    if positive_highlights:
        markdown_parts.append("## ✅ What You Did Excellently")
        for highlight in positive_highlights:
            if isinstance(highlight, dict):
                aspect = highlight.get('aspect', 'Good work')
                impact = highlight.get('impact', '')
                encouragement = highlight.get('encouragement', '')
                markdown_parts.append(f"### {aspect}")
                if impact:
                    markdown_parts.append(f"**Impact**: {impact}")
                if encouragement:
                    markdown_parts.append(f"**Recognition**: {encouragement}")
            else:
                markdown_parts.append(f"- {highlight}")
            markdown_parts.append("")
    
    # Comments by severity
    comments = ai_feedback.get('comments', [])
    if comments:
        # Group by severity
        severity_groups = {}
        for comment in comments:
            severity = comment.get('severity', 'MINOR')
            if severity not in severity_groups:
                severity_groups[severity] = []
            severity_groups[severity].append(comment)
        
        severity_order = ['CRITICAL', 'MAJOR', 'MINOR', 'SUGGESTION', 'POSITIVE']
        severity_config = {
            'CRITICAL': ('🔴 Critical Issues', 'These issues must be addressed before deployment'),
            'MAJOR': ('🟠 Major Issues', 'Important issues that should be resolved'),
            'MINOR': ('🟡 Minor Issues', 'Small improvements that would enhance code quality'),
            'SUGGESTION': ('💡 Suggestions', 'Ideas for potential improvements'),
            'POSITIVE': ('⭐ Positive Feedback', 'Great practices worth recognizing')
        }
        
        for severity in severity_order:
            if severity in severity_groups:
                title, description = severity_config[severity]
                markdown_parts.append(f"## {title}")
                markdown_parts.append(f"*{description}*\n")
                
                for comment in severity_groups[severity]:
                    markdown_parts.append(_format_enhanced_comment_markdown(comment))
    
    # Recommendations
    recommendations = ai_feedback.get('recommendations', {})
    if any(recommendations.values()):
        markdown_parts.append("## 🎯 Recommendations")
        
        if recommendations.get('immediate_actions'):
            markdown_parts.append("### 🚨 Immediate Actions")
            for action in recommendations['immediate_actions']:
                markdown_parts.append(f"- {action}")
            markdown_parts.append("")
        
        if recommendations.get('short_term_improvements'):
            markdown_parts.append("### ⏭️ Short-term Improvements")
            for improvement in recommendations['short_term_improvements']:
                markdown_parts.append(f"- {improvement}")
            markdown_parts.append("")
        
        if recommendations.get('long_term_considerations'):
            markdown_parts.append("### 🔮 Long-term Considerations")
            for consideration in recommendations['long_term_considerations']:
                markdown_parts.append(f"- {consideration}")
            markdown_parts.append("")
        
        if recommendations.get('learning_resources'):
            markdown_parts.append("### 📚 Learning Resources")
            for resource in recommendations['learning_resources']:
                markdown_parts.append(f"- {resource}")
            markdown_parts.append("")
    
    # Mentorship section
    mentorship = ai_feedback.get('mentorship_notes', {})
    if mentorship:
        markdown_parts.append("## 👨‍🏫 Mentorship Insights")
        
        if mentorship.get('strength_recognition'):
            markdown_parts.append(f"**Strengths Demonstrated**: {mentorship['strength_recognition']}")
            markdown_parts.append("")
        
        if mentorship.get('growth_opportunities'):
            markdown_parts.append(f"**Growth Opportunities**: {mentorship['growth_opportunities']}")
            markdown_parts.append("")
        
        if mentorship.get('suggested_focus'):
            markdown_parts.append(f"**Suggested Focus Areas**: {mentorship['suggested_focus']}")
            markdown_parts.append("")
    
    # Thinking process (collapsible)
    thinking_process = ai_feedback.get('thinking_process', {})
    if thinking_process and any(thinking_process.values()):
        markdown_parts.append("## 🧠 Detailed Analysis Process")
        markdown_parts.append("<details>")
        markdown_parts.append("<summary>Click to expand detailed analysis</summary>")
        markdown_parts.append("")
        
        for category, analysis in thinking_process.items():
            if analysis and analysis != f"{category.replace('_', ' ').title()} analysis not provided":
                category_display = category.replace('_', ' ').title()
                markdown_parts.append(f"### {category_display}")
                markdown_parts.append(analysis)
                markdown_parts.append("")
        
        markdown_parts.append("</details>")
        markdown_parts.append("")
    
    # Footer
    generation_time = ai_feedback.get('generated_at', 'Unknown')
    version = ai_feedback.get('version', '1.0')
    markdown_parts.append("---")
    markdown_parts.append(f"*Generated by AI Code Review Agent v{version} at {generation_time}*")
    
    return "\n".join(markdown_parts)


def _format_enhanced_comment_markdown(comment: Dict[str, Any]) -> str:
    """Format a single comment with enhanced markdown structure."""
    file_path = comment.get('file_path', 'Unknown')
    line = comment.get('line', 0)
    title = comment.get('title', 'Code Review Comment')
    category = comment.get('category', 'General')
    comment_text = comment.get('comment', 'No comment provided')
    evidence = comment.get('evidence', '')
    suggestion = comment.get('suggestion', '')
    learning_opportunity = comment.get('learning_opportunity', '')
    priority = comment.get('priority', 3)
    
    markdown = f"### 📝 {title}\n"
    markdown += f"**Location**: `{file_path}:{line}` | **Category**: {category} | **Priority**: {priority}\n\n"
    markdown += f"{comment_text}\n\n"
    
    if evidence:
        markdown += f"**Evidence**:\n```\n{evidence}\n```\n\n"
    
    if suggestion:
        markdown += f"**💡 Suggested Solution**:\n```\n{suggestion}\n```\n\n"
    
    if learning_opportunity and learning_opportunity != 'Consider researching best practices for this area':
        markdown += f"**📚 Learning Opportunity**: {learning_opportunity}\n\n"
    
    markdown += "---\n\n"
    return markdown


def generate_executive_summary(ai_feedback: Dict[str, Any]) -> str:
    """Generate a concise executive summary for stakeholders."""
    
    meta = ai_feedback.get('meta_analysis', {})
    scores = ai_feedback.get('scores', {})
    risk_assessment = ai_feedback.get('risk_assessment', {})
    comments = ai_feedback.get('comments', [])
    
    # Count issues by severity
    severity_counts = {}
    for comment in comments:
        severity = comment.get('severity', 'MINOR')
        severity_counts[severity] = severity_counts.get(severity, 0) + 1
    
    overall_score = ai_feedback.get('overall_score', 0)
    risk_level = meta.get('risk_level', 'UNKNOWN')
    deployment_readiness = risk_assessment.get('deployment_readiness', 'UNKNOWN')
    
    # Create executive summary
    summary_parts = []
    
    # Header
    summary_parts.append(f"Change Intent: {meta.get('change_intent', 'Not specified')}")
    summary_parts.append(f"Overall Quality Score: {overall_score:.1f}/10")
    summary_parts.append(f"Risk Level: {risk_level}")
    summary_parts.append(f"Deployment Status: {deployment_readiness}")
    
    # Issue summary
    if severity_counts:
        issue_summary = []
        for severity in ['CRITICAL', 'MAJOR', 'MINOR']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                issue_summary.append(f"{count} {severity.lower()}")
        
        if issue_summary:
            summary_parts.append(f"Issues Found: {', '.join(issue_summary)}")
    
    # Key recommendations
    recommendations = ai_feedback.get('recommendations', {})
    if recommendations.get('immediate_actions'):
        summary_parts.append(f"Immediate Actions Required: {len(recommendations['immediate_actions'])}")
    
    return " | ".join(summary_parts)


def extract_action_items(ai_feedback: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract actionable items from the feedback for task tracking."""
    
    action_items = []
    
    # From immediate actions
    recommendations = ai_feedback.get('recommendations', {})
    for action in recommendations.get('immediate_actions', []):
        action_items.append({
            'type': 'immediate',
            'priority': 'high',
            'description': action,
            'category': 'requirement'
        })
    
    # From critical and major comments
    comments = ai_feedback.get('comments', [])
    for comment in comments:
        severity = comment.get('severity', 'MINOR')
        if severity in ['CRITICAL', 'MAJOR']:
            action_items.append({
                'type': 'fix',
                'priority': 'high' if severity == 'CRITICAL' else 'medium',
                'description': comment.get('title', 'Fix issue'),
                'location': f"{comment.get('file_path', 'unknown')}:{comment.get('line', 0)}",
                'category': comment.get('category', 'general').lower(),
                'suggestion': comment.get('suggestion', '')
            })
    
    # From short-term improvements
    for improvement in recommendations.get('short_term_improvements', []):
        action_items.append({
            'type': 'improvement',
            'priority': 'medium',
            'description': improvement,
            'category': 'enhancement'
        })
    
    return action_items


# Legacy function for backward compatibility
def smart_truncate_diff(diff_text: str, max_chars: int = 8000) -> str:
    """Legacy function - use smart_truncate_diff_enhanced instead."""
    return smart_truncate_diff_enhanced(diff_text, max_chars)


def generate_markdown_summary(ai_feedback: Dict[str, Any]) -> str:
    """Legacy function - use generate_enhanced_markdown_summary instead."""
    return generate_enhanced_markdown_summary(ai_feedback)


# Additional utility functions for integration

def validate_ai_response_structure(response: Dict[str, Any]) -> bool:
    """Validate that the AI response has the expected structure."""
    required_keys = [
        'meta_analysis', 'thinking_process', 'summary', 'comments',
        'scores', 'overall_score', 'risk_assessment', 'recommendations',
        'positive_highlights', 'mentorship_notes'
    ]
    
    for key in required_keys:
        if key not in response:
            logger.warning(f"Missing required key in AI response: {key}")
            return False
    
    # Validate nested structures
    meta_keys = ['change_intent', 'risk_level', 'complexity_assessment', 'architectural_impact']
    if not all(key in response['meta_analysis'] for key in meta_keys):
        logger.warning("Invalid meta_analysis structure")
        return False
    
    return True


def calculate_review_metrics(ai_feedback: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate metrics for review quality and coverage."""
    comments = ai_feedback.get('comments', [])
    
    metrics = {
        'total_comments': len(comments),
        'severity_distribution': {},
        'category_distribution': {},
        'files_reviewed': len(set(c.get('file_path', '') for c in comments)),
        'avg_priority': 0,
        'coverage_score': ai_feedback.get('overall_score', 0),
        'actionable_items': len([c for c in comments if c.get('suggestion')])
    }
    
    # Calculate distributions
    for comment in comments:
        severity = comment.get('severity', 'MINOR')
        category = comment.get('category', 'General')
        
        metrics['severity_distribution'][severity] = metrics['severity_distribution'].get(severity, 0) + 1
        metrics['category_distribution'][category] = metrics['category_distribution'].get(category, 0) + 1
    
    # Calculate average priority
    priorities = [c.get('priority', 3) for c in comments]
    if priorities:
        metrics['avg_priority'] = sum(priorities) / len(priorities)
    
    return metrics


def export_review_data(ai_feedback: Dict[str, Any], format_type: str = 'json') -> str:
    """Export review data in different formats for integration."""
    if format_type.lower() == 'json':
        return json.dumps(ai_feedback, indent=2, ensure_ascii=False)
    
    elif format_type.lower() == 'csv':
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['File', 'Line', 'Severity', 'Category', 'Title', 'Comment', 'Priority'])
        
        # Write comments
        for comment in ai_feedback.get('comments', []):
            writer.writerow([
                comment.get('file_path', ''),
                comment.get('line', ''),
                comment.get('severity', ''),
                comment.get('category', ''),
                comment.get('title', ''),
                comment.get('comment', ''),
                comment.get('priority', '')
            ])
        
        return output.getvalue()
    
    elif format_type.lower() == 'markdown':
        return generate_enhanced_markdown_summary(ai_feedback)
    
    else:
        raise ValueError(f"Unsupported export format: {format_type}")


# Main execution example
if __name__ == "__main__":
    # Example usage
    sample_analysis = [
        {
            'file': 'example.py',
            'line': 10,
            'severity': 'MAJOR',
            'issue': 'Potential SQL injection vulnerability',
            'rule': 'security-sql-injection'
        }
    ]
    
    sample_diff = """
--- a/example.py
+++ b/example.py
@@ -8,6 +8,10 @@
 
 def get_user(user_id):
-    query = f"SELECT * FROM users WHERE id = {user_id}"
+    query = "SELECT * FROM users WHERE id = %s"
+    cursor.execute(query, (user_id,))
     return cursor.fetchone()
"""
    
    sample_pr_context = {
        'title': 'Fix SQL injection vulnerability',
        'description': 'Replaces string formatting with parameterized queries',
        'author': 'developer@example.com',
        'files_changed': ['example.py']
    }
    
    # Generate feedback
    feedback = generate_ai_feedback(sample_analysis, sample_diff, sample_pr_context)
    
    # Print results
    print("=== AI Feedback Generated ===")
    print(f"Overall Score: {feedback['overall_score']}")
    print(f"Comments: {len(feedback['comments'])}")
    print(f"Deployment Readiness: {feedback['risk_assessment']['deployment_readiness']}")
    
    # Export examples
    print("\n=== Export Examples ===")
    print("Executive Summary:", feedback['executive_summary'])
    print(f"Action Items: {len(feedback['action_items'])}")
    
    # Metrics
    metrics = calculate_review_metrics(feedback)
    print("Review Metrics:", json.dumps(metrics, indent=2))