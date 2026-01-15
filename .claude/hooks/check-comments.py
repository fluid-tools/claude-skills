#!/usr/bin/env python3
"""
Comment Checker Hook for Claude Code
Analyzes code changes for excessive comments
"""

import json
import sys
import re
from pathlib import Path

# Configuration
MAX_COMMENT_RATIO = 0.25  # 25% comments triggers warning
CODE_EXTENSIONS = {'.ts', '.tsx', '.js', '.jsx', '.py', '.go', '.rs', '.java', '.cpp', '.c', '.sol'}

# Patterns for valid comments (should not be flagged)
VALID_PATTERNS = [
    r'^\s*#\s*#?\s*(given|when|then|and|but)\b',  # BDD comments (Python)
    r'^\s*//\s*#?\s*(given|when|then|and|but)\b',  # BDD comments (JS/TS)
    r'^\s*"""',  # Python docstrings
    r"^\s*'''",  # Python docstrings
    r'^\s*/\*\*',  # JSDoc/JavaDoc
    r'^\s*\*\s*@',  # JSDoc annotations
    r'^\s*#!',  # Shebang
    r'^\s*//\s*@ts-',  # TypeScript directives
    r'^\s*//\s*eslint-',  # ESLint directives
    r'^\s*#\s*type:',  # Python type comments
    r'^\s*#\s*noqa',  # Python noqa
    r'^\s*#\s*pragma',  # Pragma directives
    r'^\s*//\s*TODO:',  # TODO comments (acceptable)
    r'^\s*//\s*FIXME:',  # FIXME comments (acceptable)
    r'^\s*#\s*TODO:',  # TODO comments
    r'^\s*#\s*FIXME:',  # FIXME comments
    r'^\s*///\s*',  # Rust doc comments
    r'^\s*///',  # Solidity NatSpec
    r'^\s*@dev',  # Solidity dev comments
    r'^\s*@param',  # Parameter docs
    r'^\s*@return',  # Return docs
    r'^\s*@notice',  # Solidity notice
]

def is_valid_comment(line: str) -> bool:
    """Check if a comment line is a valid/acceptable pattern"""
    for pattern in VALID_PATTERNS:
        if re.match(pattern, line, re.IGNORECASE):
            return True
    return False

def is_comment_line(line: str, ext: str) -> bool:
    """Check if a line is a comment"""
    stripped = line.strip()
    if not stripped:
        return False
    
    if ext in {'.py'}:
        return stripped.startswith('#')
    elif ext in {'.ts', '.tsx', '.js', '.jsx', '.java', '.go', '.rs', '.cpp', '.c', '.sol'}:
        return stripped.startswith('//') or stripped.startswith('/*') or stripped.startswith('*')
    
    return False

def analyze_content(content: str, file_path: str) -> dict:
    """Analyze code content for comment ratio"""
    ext = Path(file_path).suffix.lower()
    
    if ext not in CODE_EXTENSIONS:
        return {"skip": True, "reason": "Not a code file"}
    
    lines = content.split('\n')
    total_lines = len([l for l in lines if l.strip()])  # Non-empty lines
    
    if total_lines == 0:
        return {"skip": True, "reason": "Empty file"}
    
    comment_lines = []
    flagged_comments = []
    
    for i, line in enumerate(lines, 1):
        if is_comment_line(line, ext):
            comment_lines.append(i)
            if not is_valid_comment(line):
                flagged_comments.append((i, line.strip()))
    
    comment_ratio = len(comment_lines) / total_lines if total_lines > 0 else 0
    
    return {
        "skip": False,
        "total_lines": total_lines,
        "comment_lines": len(comment_lines),
        "flagged_comments": flagged_comments,
        "comment_ratio": comment_ratio,
        "excessive": comment_ratio > MAX_COMMENT_RATIO and len(flagged_comments) > 0
    }

def main():
    # Debug logging to file
    import os
    debug_log = os.path.expanduser("~/.claude/hooks/debug.log")

    try:
        raw_input = sys.stdin.read()
        with open(debug_log, "a") as f:
            f.write(f"\n=== check-comments.py called ===\n")
            f.write(f"Raw input: {raw_input[:2000]}\n")
        input_data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        with open(debug_log, "a") as f:
            f.write(f"JSON decode error: {e}\n")
        sys.exit(0)
    except Exception as e:
        with open(debug_log, "a") as f:
            f.write(f"Error reading stdin: {e}\n")
        sys.exit(0)

    with open(debug_log, "a") as f:
        f.write(f"Parsed input keys: {list(input_data.keys())}\n")

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_response = input_data.get("tool_response", {})

    file_path = tool_input.get("file_path") or tool_input.get("filePath") or tool_input.get("path", "")

    # Get content based on tool type
    content = ""
    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name in ("Edit", "MultiEdit"):
        # For Edit, read the file after the edit was applied
        if file_path and Path(file_path).exists():
            try:
                content = Path(file_path).read_text()
            except Exception as e:
                with open(debug_log, "a") as f:
                    f.write(f"Error reading file: {e}\n")
                sys.exit(0)

    with open(debug_log, "a") as f:
        f.write(f"Tool: {tool_name}, File: {file_path}, Content length: {len(content)}\n")

    if not file_path or not content:
        sys.exit(0)
    
    result = analyze_content(content, file_path)

    with open(debug_log, "a") as f:
        f.write(f"Analysis result: {result}\n")

    if result.get("skip"):
        sys.exit(0)

    if result.get("excessive"):
        ratio_pct = f"{result['comment_ratio']:.0%}"
        
        # Build warning message
        warning_lines = [
            "",
            "---",
            f"**Comment Check Warning**: {ratio_pct} of lines are comments ({result['comment_lines']}/{result['total_lines']})",
            "",
            "Flagged comments that may be unnecessary:",
        ]
        
        for line_num, comment in result['flagged_comments'][:5]:  # Show max 5
            warning_lines.append(f"  Line {line_num}: `{comment[:60]}{'...' if len(comment) > 60 else ''}`")
        
        if len(result['flagged_comments']) > 5:
            warning_lines.append(f"  ... and {len(result['flagged_comments']) - 5} more")
        
        warning_lines.extend([
            "",
            "**Recommendation**: Code should be self-documenting. Consider:",
            "- Using descriptive variable/function names instead of comments",
            "- Removing obvious comments that repeat what code does",
            "- Keeping only comments that explain *why*, not *what*",
            "---",
        ])
        
        # Output warning to be appended to tool output
        output = {
            "hookSpecificOutput": {
                "additionalContext": "\n".join(warning_lines)
            }
        }
        output_json = json.dumps(output)
        with open(debug_log, "a") as f:
            f.write(f"Outputting: {output_json}\n")
        print(output_json)

    sys.exit(0)

if __name__ == "__main__":
    main()

