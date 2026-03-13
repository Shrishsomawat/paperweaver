PLANNER_PROMPT = """You are a senior ML engineer tasked with implementing a research paper for a lightweight MVP.

PAPER TITLE: {title}
ABSTRACT: {abstract}

METHODOLOGY SECTION:
{methodology_text}

ARCHITECTURE ANALYSIS FROM FIGURES:
{architecture_analysis}

Create an ordered implementation plan as a JSON list of the smallest useful set of modules.
Prefer 3-4 modules total unless the paper absolutely requires more.
Each item must have:
- module_name: snake_case filename ending in .py
- description: what the module does in 1-2 sentences
- key_classes: list of class/function names
- depends_on: list of module filenames this depends on
- paper_reference: section, figure, or equation reference

Return only valid JSON.
"""

CODER_PROMPT = """Implement one Python module from a research paper.

PAPER EXCERPT:
{paper_excerpt}

MODULE TO IMPLEMENT:
Name: {module_name}
Description: {description}
Key classes/functions: {key_classes}
Paper reference: {paper_reference}

AVAILABLE MODULES:
{existing_modules_summary}

CRITIC FEEDBACK TO FIX:
{critic_feedback}

Write concise runnable Python code with:
- docstrings
- type hints
- no placeholders
- minimal comments only when they add real clarity
- prefer simple, dependency-light implementations

Return only Python code.
"""

CRITIC_PROMPT = """You are reviewing generated Python code against a research paper.

PAPER EXCERPT:
{paper_excerpt}

MODULE SPEC:
{module_spec}

CODE:
{code}

Respond in exactly this format:
VERDICT: PASS or FAIL
ISSUES:
- issue 1
- issue 2
SUGGESTIONS:
- suggestion 1
- suggestion 2
"""

TEST_PROMPT = """Write a minimal pytest suite for this paper implementation.

PAPER TITLE: {title}
MODULES:
{module_names}

CODE SAMPLE:
{code_sample}

Requirements:
- keep the test file short
- verify basic interfaces or shapes where possible
- include one smoke test

Return only pytest code.
"""
