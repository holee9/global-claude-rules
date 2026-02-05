#!/usr/bin/env python3
"""
PreToolUse Hook: Enforce ERR Rules Before Tool Execution

Claude Code Event: PreToolUse
Purpose: Display relevant ERR-XXX rules before executing tools
Execution: Triggered before Write, Edit, Bash, and Task tools

Features:
- Detects relevant ERR rules based on tool type and parameters
- Shows file-related rules for Write/Edit operations
- Shows command-related rules for Bash operations
- Shows agent-related rules for Task operations
- Keyword-based matching to surface contextually relevant rules
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any


# =============================================================================
# Constants
# =============================================================================
# Global memory path
DEFAULT_GLOBAL_MEMORY_PATH = Path.home() / ".claude" / "memory.md"
PROJECT_MEMORY_PATH = Path.cwd() / ".claude" / "memory.md"

# Tool to ERR rule keyword mapping
TOOL_KEYWORDS = {
    "Write": [
        "file", "write", "create", "save", "path", "directory",
        "encoding", "utf-8", "utf-16", "charset"
    ],
    "Edit": [
        "file", "edit", "modify", "replace", "path", "not found",
        "encoding", "utf-8", "utf-16", "string", "escape"
    ],
    "Bash": [
        "command", "git", "terminal", "shell", "path", "execute",
        "permissions", "directory"
    ],
    "Task": [
        "agent", "subagent", "task", "create", "parameter",
        "context", "delegate"
    ],
    "Read": [
        "file", "read", "path", "not found", "encoding", "permission"
    ],
    "Grep": [
        "pattern", "search", "match", "regex", "grep", "find"
    ],
    "Glob": [
        "file", "pattern", "path", "find", "wildcard"
    ],
}

# Common error patterns and their associated ERR rules
ERROR_PATTERNS = {
    r"todo|task": ["ERR-001", "ERR-008"],
    r"hook.*not.*found|file.*not.*found": ["ERR-002", "ERR-003", "ERR-004", "ERR-024"],
    r"edit.*fail|replace.*fail": ["ERR-003", "ERR-013", "ERR-023"],
    r"file.*not.*found|path.*wrong": ["ERR-004", "ERR-022"],
    r"port.*direction|input|output": ["ERR-005"],
    r"reset|polarity|rst_n": ["ERR-006", "ERR-012"],
    r"undriven|driver": ["ERR-007"],
    r"parameter.*missing|required": ["ERR-008"],
    r"grep.*match|pattern.*not": ["ERR-009"],
    r"comment|//|#": ["ERR-014", "ERR-016"],
    r"escape|backslash": ["ERR-015"],
    r"instruction|command.*not.*follow": ["ERR-022"],
    r"utf-?16|encoding|rc.*file|res.*file": ["ERR-023"],
    r"hook.*directory|moai.*hook": ["ERR-024"],
    r"OnInitDialog|MFC|control": ["ERR-600"],
    r"dll.*architecture|x64|x86": ["ERR-601"],
    r"CFile.*uninitialized": ["ERR-602"],
}


def setup_logging():
    """Setup logging for the hook."""
    logging.basicConfig(
        level=logging.WARNING,
        format='%(levelname)s: %(message)s',
        stream=sys.stderr
    )


def load_global_memory() -> str:
    """Load global memory file.

    Returns:
        Content of the global memory file or empty string if not found
    """
    # Try global memory first
    global_path = os.getenv("GLOBAL_CLAUDE_MEMORY", str(DEFAULT_GLOBAL_MEMORY_PATH))
    memory_file = Path(global_path)

    if memory_file.exists():
        try:
            return memory_file.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError) as e:
            logging.warning(f"Failed to read global memory: {e}")

    # Fallback to project memory
    if PROJECT_MEMORY_PATH.exists():
        try:
            return PROJECT_MEMORY_PATH.read_text(encoding="utf-8", errors="replace")
        except (OSError, UnicodeDecodeError) as e:
            logging.warning(f"Failed to read project memory: {e}")

    return ""


def extract_rules_from_memory(memory_content: str) -> list[dict]:
    """Extract all ERR rules from memory content.

    Args:
        memory_content: The memory file content

    Returns:
        List of rule dictionaries with id, title, problem, solution, prevention
    """
    rules = []

    # Find all ERR-XXX sections
    lines = memory_content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]

        # Match ERR-XXX header
        match = re.match(r'###\s+(ERR-\d+):\s*(.+)', line)
        if match:
            rule = {
                'id': match.group(1),
                'title': match.group(2).strip(),
                'problem': '',
                'solution': '',
                'prevention': '',
            }

            # Parse following lines
            i += 1
            while i < len(lines):
                next_line = lines[i]

                # Stop at next rule or section
                if next_line.startswith('### ERR-') or next_line.startswith('## '):
                    break

                if '**Problem**:' in next_line:
                    rule['problem'] = next_line.split('**Problem**:', 1)[1].strip()
                elif '**Solution**:' in next_line:
                    rule['solution'] = next_line.split('**Solution**:', 1)[1].strip()
                elif '**Prevention**:' in next_line:
                    rule['prevention'] = next_line.split('**Prevention**:', 1)[1].strip()

                i += 1

            rules.append(rule)
        else:
            i += 1

    return rules


def find_relevant_rules(
    rules: list[dict],
    tool_name: str,
    tool_input: dict,
) -> list[dict]:
    """Find relevant rules based on tool and input.

    Args:
        rules: All available rules
        tool_name: Name of the tool being called
        tool_input: Input parameters for the tool

    Returns:
        List of relevant rules sorted by relevance
    """
    relevant_rules = []
    tool_input_str = json.dumps(tool_input, case_sensitive=False).lower()

    # Get keywords for this tool
    keywords = TOOL_KEYWORDS.get(tool_name, [])

    # Score each rule
    for rule in rules:
        score = 0
        rule_text = f"{rule['id']} {rule['title']} {rule['problem']} {rule['solution']}".lower()

        # Check if rule ID is in error patterns
        for pattern, err_ids in ERROR_PATTERNS.items():
            if rule['id'] in err_ids:
                if re.search(pattern, tool_input_str):
                    score += 10  # High priority for pattern matches
                if re.search(pattern, rule_text):
                    score += 5

        # Check keyword matches
        for keyword in keywords:
            if keyword in rule_text:
                score += 2
            if keyword in tool_input_str and keyword in rule_text:
                score += 3

        # Check for direct tool name mentions
        if tool_name.lower() in rule_text:
            score += 5

        # Check file path mentions
        if 'file_path' in tool_input:
            file_path = str(tool_input['file_path']).lower()
            if 'file' in rule_text:
                score += 2

            # Check for specific file extensions
            if '.' in file_path:
                ext = file_path.rsplit('.', 1)[-1]
                if ext in rule_text or ext.upper() in rule_text:
                    score += 3

        # Check command mentions for Bash
        if tool_name == "Bash" and 'command' in tool_input:
            command = str(tool_input['command']).lower()
            if 'git' in command and 'git' in rule_text:
                score += 5
            if 'npm' in command and 'npm' in rule_text:
                score += 3
            if 'python' in command and 'python' in rule_text:
                score += 3

        # Check Task tool mentions
        if tool_name == "Task" and 'subagent_type' in tool_input:
            subagent = tool_input['subagent_type'].lower()
            if subagent in rule_text:
                score += 3

        # Only include rules with a score
        if score > 0:
            rule['relevance_score'] = score
            relevant_rules.append(rule)

    # Sort by relevance score
    relevant_rules.sort(key=lambda r: r.get('relevance_score', 0), reverse=True)

    return relevant_rules


def format_rule_display(rule: dict, compact: bool = False) -> str:
    """Format a rule for display.

    Args:
        rule: Rule dictionary
        compact: If True, show compact format

    Returns:
        Formatted rule string
    """
    if compact:
        return f"  • {rule['id']}: {rule['title']}"

    lines = [
        f"  {rule['id']}: {rule['title']}",
    ]

    if rule.get('solution'):
        lines.append(f"    → {rule['solution'][:100]}{'...' if len(rule['solution']) > 100 else ''}")

    return "\n".join(lines)


def main() -> None:
    """Main entry point for PreToolUse hook.

    Reads tool call information, finds relevant ERR rules,
    and displays them before tool execution.
    """
    # Read input from stdin
    try:
        input_data = sys.stdin.read()
        if not input_data.strip():
            input_data = "{}"
        tool_data = json.loads(input_data) if input_data.strip() else {}
    except json.JSONDecodeError:
        logging.warning("Failed to parse stdin as JSON")
        tool_data = {}

    # Extract tool information
    tool_name = tool_data.get("tool", "")
    tool_input = tool_data.get("input", {})

    if not tool_name:
        # No tool info, just continue
        result = {"continue": True}
        print(json.dumps(result))
        return

    # Load global memory
    memory_content = load_global_memory()

    if not memory_content:
        # No memory available, continue
        result = {"continue": True}
        print(json.dumps(result))
        return

    # Extract rules
    rules = extract_rules_from_memory(memory_content)

    if not rules:
        # No rules found, continue
        result = {"continue": True}
        print(json.dumps(result))
        return

    # Find relevant rules
    relevant = find_relevant_rules(rules, tool_name, tool_input)

    # Build output
    output_lines = []
    system_message_parts = []

    if relevant:
        # Show top 5 most relevant rules
        top_rules = relevant[:5]

        header = f"\n🔒 Relevant ERR Rules for {tool_name}:"
        output_lines.append(header)
        system_message_parts.append(header)

        for rule in top_rules:
            rule_text = format_rule_display(rule, compact=True)
            output_lines.append(rule_text)
            system_message_parts.append(rule_text)

        # Add hint about full rules
        hint = f"\n  (Showing {len(top_rules)} of {len(relevant)} relevant rules)"
        output_lines.append(hint)
        system_message_parts.append(hint)

    # Combine output
    system_message = "\n".join(system_message_parts)

    result = {
        "continue": True,
        "systemMessage": system_message,
        "hookSpecificOutput": {
            "tool": tool_name,
            "relevant_rules_count": len(relevant),
            "shown_rules": len(top_rules) if relevant else 0,
        }
    }

    # Also print to stderr for visibility
    if output_lines:
        print("\n".join(output_lines), file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
