#!/usr/bin/env python3
"""
PostToolUse Hook: Error Detection and Rule Suggestion

Claude Code Event: PostToolUse
Purpose: Detect errors in tool output and suggest relevant ERR rules
Execution: Triggered after tool execution completes

Features:
- Detects error patterns in tool output
- Matches errors to relevant ERR rules
- Suggests rules when errors are detected
- Tracks error patterns for analytics
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
DEFAULT_GLOBAL_MEMORY_PATH = Path.home() / ".claude" / "memory.md"
PROJECT_MEMORY_PATH = Path.cwd() / ".claude" / "memory.md"

# Error patterns to ERR rule mappings
ERROR_PATTERNS = {
    # File/Path errors
    r"file\s+not\s+found|no\s+such\s+file|cannot\s+find\s+the\s+file": ["ERR-004", "ERR-022"],
    r"path\s+.*?\s+not\s+found|invalid\s+path": ["ERR-004", "ERR-022"],
    r"permission\s+denied|access\s+denied": ["ERR-004"],

    # Edit/Write errors
    r"edit\s+failed|old_string\s+not\s+found|string\s+not\s+found": ["ERR-003", "ERR-013"],
    r"replacement\s+failed|content\s+does\s+not\s+match": ["ERR-003", "ERR-013", "ERR-023"],

    # Hook errors
    r"hook\s+not\s+found|hook\s+directory|moai.*hook": ["ERR-002", "ERR-024"],

    # Todo/Task errors
    r"todowrite.*not\s+available|todo.*not\s+available": ["ERR-001", "ERR-008"],
    r"task.*not\s+available|agent.*error": ["ERR-001"],

    # Git errors
    r"git.*failed|merge\s+conflict|diverged": ["ERR-100", "ERR-101"],
    r"not\s+a\s+git\s+repository": ["ERR-100"],

    # Encoding errors
    r"utf-?16|unicode.*error|encoding.*error|codec.*error": ["ERR-023"],
    r"rc\s+file|res\s+file.*encoding": ["ERR-023"],

    # Grep/Search errors
    r"pattern\s+not\s+found|no\s+matches|grep.*error": ["ERR-009"],
    r"regex.*error|invalid\s+pattern": ["ERR-009"],

    # Parameter errors
    r"required.*parameter.*missing|missing.*required": ["ERR-008"],
    r"invalid.*parameter|unknown.*argument": ["ERR-008"],

    # Comment/Escape errors
    r"comment.*error|unexpected.*comment": ["ERR-014", "ERR-016"],
    r"escape.*error|backslash.*error": ["ERR-015"],

    # MFC errors
    r"OnInitDialog.*failed|mfc.*error": ["ERR-600"],
    r"dll.*architecture|x64|x86.*mismatch": ["ERR-601"],
    r"CFile.*uninitialized": ["ERR-602"],

    # Port direction (FPGA)
    r"port\s+direction|input.*output.*conflict": ["ERR-005"],

    # Reset/Polarity (FPGA)
    r"reset.*polarity|rst_n.*error": ["ERR-006", "ERR-012"],

    # Undriven signals
    r"undriven.*signal|unconnected.*port": ["ERR-007"],

    # Build errors
    r"compilation.*error|build.*failed|linker.*error": ["ERR-200"],
    r"undefined.*reference|unresolved.*external": ["ERR-200"],
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


def detect_errors_in_output(tool_name: str, tool_output: str, exit_code: int) -> list[str]:
    """Detect error patterns in tool output.

    Args:
        tool_name: Name of the tool that was executed
        tool_output: Output from the tool
        exit_code: Exit code from the tool

    Returns:
        List of detected ERR rule IDs
    """
    detected_rules = []

    # Check if tool failed
    if exit_code != 0:
        # Search for error patterns
        output_lower = tool_output.lower()

        for pattern, rule_ids in ERROR_PATTERNS.items():
            if re.search(pattern, output_lower):
                for rule_id in rule_ids:
                    if rule_id not in detected_rules:
                        detected_rules.append(rule_id)

        # Tool-specific patterns
        if tool_name == "Edit" or tool_name == "Write":
            if "not found" in output_lower or "does not exist" in output_lower:
                if "ERR-004" not in detected_rules:
                    detected_rules.append("ERR-004")

        if tool_name == "Bash":
            # Check for command not found
            if "command not found" in output_lower or "not recognized" in output_lower:
                if "ERR-008" not in detected_rules:
                    detected_rules.append("ERR-008")

            # Check for git errors
            if "git" in tool_output.lower():
                if "conflict" in output_lower or "merge" in output_lower:
                    if "ERR-100" not in detected_rules:
                        detected_rules.append("ERR-100")

    return detected_rules


def format_suggestion_message(detected_rules: list[dict]) -> str:
    """Format the rule suggestion message.

    Args:
        detected_rules: List of rule dictionaries

    Returns:
        Formatted message string
    """
    if not detected_rules:
        return ""

    lines = [
        "\n⚠️ Error Detected - Relevant Rules:",
    ]

    for rule in detected_rules[:5]:  # Show max 5 rules
        lines.append(f"  📌 {rule['id']}: {rule['title']}")
        if rule.get('solution'):
            solution = rule['solution'][:80]
            if len(rule['solution']) > 80:
                solution += "..."
            lines.append(f"     → {solution}")

    if len(detected_rules) > 5:
        lines.append(f"  ... and {len(detected_rules) - 5} more")

    lines.append("")

    return "\n".join(lines)


def track_error_detection(err_ids: list[str]) -> None:
    """Track detected errors for analytics.

    Args:
        err_ids: List of detected ERR rule IDs
    """
    try:
        # Import analytics module
        lib_dir = Path(__file__).parent / "lib"
        if str(lib_dir) not in sys.path:
            sys.path.insert(0, str(lib_dir))

        from rule_analytics import track_rules_view
        track_rules_view(err_ids, context="error_detection")
    except ImportError:
        pass


def main() -> None:
    """Main entry point for PostToolUse hook.

    Reads tool execution result, detects errors,
    and suggests relevant ERR rules.
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
    tool_output = tool_data.get("output", "")
    exit_code = tool_data.get("exitCode", 0)
    tool_error = tool_data.get("error", "")

    # Combine output and error for detection
    full_output = f"{tool_output} {tool_error}"

    if not tool_name:
        # No tool info, just continue
        result = {"continue": True}
        print(json.dumps(result))
        return

    # Load global memory for rule lookup
    memory_content = load_global_memory()

    if not memory_content:
        # No memory available, continue
        result = {"continue": True}
        print(json.dumps(result))
        return

    # Extract all rules
    all_rules = extract_rules_from_memory(memory_content)

    if not all_rules:
        # No rules found, continue
        result = {"continue": True}
        print(json.dumps(result))
        return

    # Detect errors
    detected_err_ids = detect_errors_in_output(tool_name, full_output, exit_code)

    # Build output
    system_message_parts = []
    stderr_lines = []

    if detected_err_ids:
        # Get full rule details
        detected_rules = [
            rule for rule in all_rules
            if rule['id'] in detected_err_ids
        ]

        if detected_rules:
            # Format suggestion message
            message = format_suggestion_message(detected_rules)
            system_message_parts.append(message)
            stderr_lines.append(message)

            # Track for analytics
            track_error_detection(detected_err_ids)

    # Combine output
    system_message = "\n".join(system_message_parts)

    result = {
        "continue": True,
        "systemMessage": system_message,
        "hookSpecificOutput": {
            "tool": tool_name,
            "exit_code": exit_code,
            "detected_errors": detected_err_ids,
            "suggestions_shown": len(detected_err_ids),
        }
    }

    # Also print to stderr for visibility
    if stderr_lines:
        print("\n".join(stderr_lines), file=sys.stderr)

    print(json.dumps(result, ensure_ascii=False))
    sys.exit(0)


if __name__ == "__main__":
    main()
