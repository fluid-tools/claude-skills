#!/usr/bin/env python3
"""
Keyword Detector Hook for Claude Code
Detects special keywords and injects mode-specific context
"""

import json
import sys
import re

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)
    
    prompt = input_data.get("prompt", "").lower()
    
    additional_context = None
    
    # Ultrawork mode - maximum performance
    if re.search(r'\b(ultrawork|ulw|ultra\s*work)\b', prompt):
        additional_context = """
[ULTRAWORK MODE ACTIVATED]

Execute with maximum capability:

1. **Parallel Execution**: Launch multiple agents/tools simultaneously
2. **Comprehensive Planning**: Create detailed todo list BEFORE starting
3. **Thorough Verification**: Run diagnostics on all changed files
4. **No Premature Stopping**: Continue until ALL tasks complete
5. **Evidence-Based**: Verify each change works correctly

Workflow:
- Use Task tool to delegate to specialized agents (explore, oracle)
- Launch independent searches in parallel
- Create todos for complex multi-step work
- Mark todos complete only after verification
"""

    # Search mode - maximized search effort
    elif re.search(r'\b(search|find|locate|where\s+is)\b', prompt):
        additional_context = """
[SEARCH MODE ACTIVATED]

Maximize search thoroughness:

1. **Parallel Searches**: Launch multiple search operations simultaneously
2. **Multiple Angles**: Search by name, content, pattern, and structure
3. **Cross-Reference**: Verify findings across multiple sources
4. **Exhaustive**: Don't stop at first result - find ALL matches

Tools to use in parallel:
- Grep for text patterns
- Glob for file patterns
- LSP for symbol definitions/references
- Git for history when relevant

Report:
- All matching files with absolute paths
- Relevance explanation for each match
- Confidence level in completeness
"""

    # Analysis mode - deep investigation
    elif re.search(r'\b(analyze|investigate|debug|diagnose)\b', prompt):
        additional_context = """
[ANALYSIS MODE ACTIVATED]

Deep investigation protocol:

1. **Gather Evidence**: Read all relevant files before forming conclusions
2. **Multi-Phase Analysis**:
   - Phase 1: Surface-level scan
   - Phase 2: Deep dive into suspicious areas
   - Phase 3: Cross-reference and validate
3. **Consult Experts**: Use oracle agent for complex reasoning
4. **Document Findings**: Systematic, evidence-based conclusions

For debugging:
- Check recent changes (git log, git blame)
- Trace data flow through the system
- Identify edge cases and error paths
- Propose hypothesis and test it
"""

    # Think mode - extended reasoning (note: Claude Code has native ultrathink)
    elif re.search(r'\b(think\s*(deeply|hard|carefully))\b', prompt):
        additional_context = """
[EXTENDED THINKING MODE]

Take time for thorough reasoning:

1. **Step Back**: Consider the broader context and implications
2. **Multiple Perspectives**: Evaluate different approaches
3. **Trade-off Analysis**: Document pros/cons of each option
4. **Risk Assessment**: Identify potential issues before implementing
5. **Validation Plan**: How will we verify success?

Before acting:
- State your understanding of the problem
- List assumptions being made
- Outline the approach with rationale
- Identify potential failure modes
"""

    if additional_context:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": additional_context.strip()
            }
        }
        print(json.dumps(output))
    
    sys.exit(0)

if __name__ == "__main__":
    main()

