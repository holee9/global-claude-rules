#!/usr/bin/env python3
"""
Global Claude Rules - Add ERR Rule CLI

Interactive CLI tool for adding error prevention rules to the global memory.
Automatically assigns ERR-XXX numbers, validates format, and updates all files.

Usage:
    python scripts/add_rule.py
    python scripts/add_rule.py --non-interactive
    python scripts/add_rule.py --no-commit

Features:
- Interactive input for all required fields
- Auto ERR-XXX number assignment
- Format validation
- Updates both template and global memory files
- Optional git commit creation
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for cross-platform terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def disable():
        """Disable colors (for Windows cmd.exe without ANSI support)."""
        Colors.HEADER = ''
        Colors.OKBLUE = ''
        Colors.OKCYAN = ''
        Colors.OKGREEN = ''
        Colors.WARNING = ''
        Colors.FAIL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''


def setup_colors():
    """Setup colors based on platform and terminal support."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except (AttributeError, OSError):
            Colors.disable()


def print_header(text: str):
    """Print a header with formatting."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def get_script_dir() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.resolve()


def get_claude_dir() -> Path:
    """Get the Claude Code configuration directory."""
    if env_dir := os.getenv("CLAUDE_CONFIG_DIR"):
        return Path(env_dir)
    return Path.home() / ".claude"


def get_template_memory_path() -> Path:
    """Get the template memory.md path."""
    return get_script_dir() / "templates" / "memory.md"


def get_global_memory_path() -> Path:
    """Get the global memory.md path."""
    return get_claude_dir() / "memory.md"


def verify_write_access(path: Path) -> tuple[bool, str]:
    """Verify file can be written to target location.

    Args:
        path: Target file path

    Returns:
        Tuple of (success, error_message)
    """
    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Test write access by creating a temporary file
        test_file = path.parent / f".write_test_{os.getpid()}"
        test_file.touch()
        test_file.unlink()

        return True, ""

    except PermissionError as e:
        return False, f"Permission denied: {e}"
    except OSError as e:
        return False, f"Cannot write to {path.parent}: {e}"


def get_next_err_number(content: str) -> int:
    """Get the next available ERR number by parsing existing rules.

    Args:
        content: The memory.md file content

    Returns:
        The next available ERR number (highest existing + 1)
    """
    # Find all ERR-XXX patterns
    matches = re.findall(r'ERR-(\d+)', content)
    if not matches:
        return 1  # Start with ERR-001 if no rules exist

    # Get the highest number
    max_num = max(int(m) for m in matches)
    return max_num + 1


def get_category_for_number(err_num: int) -> str:
    """Determine the category based on ERR number range.

    Args:
        err_num: The ERR number

    Returns:
        Category description
    """
    if 1 <= err_num <= 99:
        return "General/System errors (ERR-001~ERR-099)"
    elif 100 <= err_num <= 199:
        return "Git/Version control errors (ERR-100~ERR-199)"
    elif 200 <= err_num <= 299:
        return "Build/Compilation errors (ERR-200~ERR-299)"
    elif 300 <= err_num <= 399:
        return "FPGA/Hardware errors (ERR-300~ERR-399)"
    elif 400 <= err_num <= 499:
        return "Backend/API errors (ERR-400~ERR-499)"
    elif 500 <= err_num <= 599:
        return "Frontend/UI errors (ERR-500~ERR-599)"
    elif 600 <= err_num <= 699:
        return "MFC/Win32 errors (ERR-600~ERR-699)"
    else:
        return "Other errors"


def validate_rule_fields(title: str, problem: str, root_cause: str,
                         solution: str, prevention: str) -> list[str]:
    """Validate rule fields for completeness and format.

    Args:
        title: Short title for the error
        problem: Problem description
        root_cause: Root cause analysis
        solution: How to fix the error
        prevention: How to prevent in future

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    if not title or len(title.strip()) < 5:
        errors.append("Title must be at least 5 characters long")

    if not problem or len(problem.strip()) < 10:
        errors.append("Problem description must be at least 10 characters long")

    if not root_cause or len(root_cause.strip()) < 10:
        errors.append("Root cause must be at least 10 characters long")

    if not solution or len(solution.strip()) < 10:
        errors.append("Solution must be at least 10 characters long")

    if not prevention or len(prevention.strip()) < 10:
        errors.append("Prevention must be at least 10 characters long")

    return errors


def format_rule_entry(err_num: int, title: str, problem: str, root_cause: str,
                      solution: str, prevention: str, project: str = "",
                      category: str = "") -> str:
    """Format a rule entry as markdown.

    Args:
        err_num: The ERR number
        title: Short title
        problem: Problem description
        root_cause: Root cause
        solution: Solution
        prevention: Prevention measures
        project: Project name (optional)
        category: Category (optional)

    Returns:
        Formatted markdown string
    """
    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        f"### ERR-{err_num:03d}: {title}",
        f"**Problem**: {problem}",
        f"**Root Cause**: {root_cause}",
        f"**Solution**: {solution}",
        f"**Prevention**: {prevention}",
        f"**Date**: {date_str}",
    ]

    if project:
        lines.append(f"**Project**: {project}")

    if category:
        lines.append(f"**Category**: {category}")

    return "\n".join(lines)


def find_insert_position(content: str, err_num: int) -> int:
    """Find the appropriate position to insert a new rule.

    Rules should be inserted in numerical order within their category section.

    Args:
        content: The memory.md file content
        err_num: The ERR number being added

    Returns:
        Character position where the new rule should be inserted
    """
    lines = content.split("\n")

    # Find the appropriate section based on ERR number
    if err_num < 100:
        section_start = None
        for i, line in enumerate(lines):
            if "## 4. Common Errors Across All Projects" in line or \
               ("ERR-001:" in line and section_start is None):
                if section_start is None:
                    section_start = i
            elif section_start is not None:
                # Found a rule, check if we should insert before it
                match = re.search(r'ERR-(\d+):', line)
                if match and int(match.group(1)) > err_num:
                    # Insert before this rule
                    return sum(len(l) + 1 for l in lines[:i])

        # Insert at the end of the section
        if section_start is not None:
            # Find the end of this section
            for i in range(section_start, len(lines)):
                if lines[i].startswith("## ") and "Common Errors" not in lines[i]:
                    return sum(len(l) + 1 for l in lines[:i])

    # For other categories, insert before the Quick Reference table
    for i, line in enumerate(lines):
        if "### Error Quick Reference Table" in line or \
           "Error Quick Reference Table" in line:
            return sum(len(l) + 1 for l in lines[:i])

    # Default: append to end
    return len(content)


def insert_rule_into_content(content: str, rule_entry: str, err_num: int) -> str:
    """Insert a new rule into the content at the appropriate position.

    Args:
        content: Original memory.md content
        rule_entry: Formatted rule entry
        err_num: The ERR number

    Returns:
        Updated content with the new rule
    """
    insert_pos = find_insert_position(content, err_num)

    # Insert the rule with proper spacing
    before = content[:insert_pos].rstrip()
    after = content[insert_pos:]

    # Ensure proper spacing
    new_content = f"{before}\n\n{rule_entry}\n\n{after}"

    return new_content


def update_quick_reference_table(content: str, err_num: int, title: str,
                                 quick_solution: str) -> str:
    """Update the quick reference table with the new rule.

    Args:
        content: Original memory.md content
        err_num: The ERR number
        title: Short title
        quick_solution: Quick solution summary

    Returns:
        Updated content with new table entry
    """
    # Find the table and add a new row
    table_pattern = r'(\| Error ID \| Description \| Quick Solution \|\n\|.*?\|.*?\|.*?\|\n)'
    match = re.search(table_pattern, content)

    if not match:
        return content

    # Create new table row
    new_row = f"| ERR-{err_num:03d} | {title} | {quick_solution} |"

    # Insert after the separator row
    table_end = match.end()
    before = content[:table_end]
    after = content[table_end:]

    return f"{before}\n{new_row}{after}"


def interactive_input() -> dict:
    """Collect rule information through interactive prompts.

    Returns:
        Dictionary with rule fields
    """
    print_header("Add New ERR Rule")

    print_info("Please provide the following information for the new error rule.\n")

    rule_data = {}

    # Title
    while True:
        title = input(f"{Colors.OKCYAN}Short Title:{Colors.ENDC} ").strip()
        if title and len(title) >= 5:
            rule_data['title'] = title
            break
        print_error("Title must be at least 5 characters long. Please try again.")

    # Problem
    while True:
        print(f"\n{Colors.OKCYAN}Problem Description:{Colors.ENDC}")
        print("  What went wrong? (Press Enter twice to finish)")
        problem_lines = []
        while True:
            line = input("  ")
            if line == "" and problem_lines and problem_lines[-1] == "":
                problem_lines.pop()  # Remove the empty line
                break
            problem_lines.append(line)
        problem = " ".join(problem_lines)

        if len(problem) >= 10:
            rule_data['problem'] = problem
            break
        print_error("Problem must be at least 10 characters long. Please try again.")

    # Root Cause
    while True:
        print(f"\n{Colors.OKCYAN}Root Cause:{Colors.ENDC}")
        print("  Why did it happen? (Press Enter twice to finish)")
        cause_lines = []
        while True:
            line = input("  ")
            if line == "" and cause_lines and cause_lines[-1] == "":
                cause_lines.pop()
                break
            cause_lines.append(line)
        root_cause = " ".join(cause_lines)

        if len(root_cause) >= 10:
            rule_data['root_cause'] = root_cause
            break
        print_error("Root cause must be at least 10 characters long. Please try again.")

    # Solution
    while True:
        print(f"\n{Colors.OKCYAN}Solution:{Colors.ENDC}")
        print("  How did you fix it? (Press Enter twice to finish)")
        solution_lines = []
        while True:
            line = input("  ")
            if line == "" and solution_lines and solution_lines[-1] == "":
                solution_lines.pop()
                break
            solution_lines.append(line)
        solution = " ".join(solution_lines)

        if len(solution) >= 10:
            rule_data['solution'] = solution
            break
        print_error("Solution must be at least 10 characters long. Please try again.")

    # Prevention
    while True:
        print(f"\n{Colors.OKCYAN}Prevention:{Colors.ENDC}")
        print("  How to avoid this in the future? (Press Enter twice to finish)")
        prevention_lines = []
        while True:
            line = input("  ")
            if line == "" and prevention_lines and prevention_lines[-1] == "":
                prevention_lines.pop()
                break
            prevention_lines.append(line)
        prevention = " ".join(prevention_lines)

        if len(prevention) >= 10:
            rule_data['prevention'] = prevention
            break
        print_error("Prevention must be at least 10 characters long. Please try again.")

    # Optional fields
    print(f"\n{Colors.OKCYAN}Project Name (optional):{Colors.ENDC} ")
    project = input().strip()
    rule_data['project'] = project

    # Quick solution summary (default to first 50 chars of solution)
    quick_solution = solution[:47] + "..." if len(solution) > 50 else solution
    print(f"\n{Colors.OKCYAN}Quick Solution (default: {quick_solution}):{Colors.ENDC} ")
    custom_quick = input().strip()
    if custom_quick:
        rule_data['quick_solution'] = custom_quick
    else:
        rule_data['quick_solution'] = quick_solution

    return rule_data


def create_git_commit(err_num: int, title: str) -> bool:
    """Create a git commit for the new rule.

    Args:
        err_num: The ERR number
        title: Rule title

    Returns:
        True if commit successful, False otherwise
    """
    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print_warning("Not in a git repository, skipping commit")
            return False

        # Add the modified files
        subprocess.run(
            ["git", "add", "templates/memory.md"],
            capture_output=True,
            timeout=10
        )

        # Try to add global memory if it exists
        global_memory = get_global_memory_path()
        if global_memory.exists():
            subprocess.run(
                ["git", "add", str(global_memory)],
                capture_output=True,
                timeout=10
            )

        # Create commit
        commit_msg = f"docs: Add ERR-{err_num:03d} {title}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            print_success(f"Git commit created: {commit_msg}")
            return True
        else:
            print_warning("Git commit failed (possibly no changes to commit)")
            return False

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print_warning(f"Git operation failed: {e}")
        return False


def auto_push_rules(dry_run: bool = False) -> bool:
    """Automatically push rule changes to remote repository.

    Args:
        dry_run: If True, only simulate the push

    Returns:
        True if push successful or not needed, False otherwise
    """
    try:
        # Check if we're in a git repository
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            return False  # Not a git repo

        # Check if remote exists
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode != 0:
            print_info("No git remote configured - skipping push")
            return True  # Not an error, just no remote

        if dry_run:
            print_info("Would push to remote (dry-run)")
            return True

        print_info("Pushing to remote...")
        result = subprocess.run(
            ["git", "push"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print_success("Pushed to remote successfully")
            return True

        # Handle specific errors
        if "unable to access" in result.stderr or "could not connect" in result.stderr:
            print_warning("Network error - changes committed locally only")
        elif "rejected" in result.stderr:
            print_warning("Push rejected - changes committed locally only")
            print_info("Run 'git pull' then 'git push' to sync")
        else:
            print_warning(f"Push failed: {result.stderr[-100:]}")

        return True  # Commit succeeded even if push failed

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print_warning(f"Push operation failed: {e}")
        return True  # Commit succeeded even if push failed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Add new ERR rule to Global Claude Rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/add_rule.py              # Interactive mode
  python scripts/add_rule.py --non-interactive \\
      --title "File Not Found" \\
      --problem "File path was incorrect" \\
      --root-cause "Wrong directory assumption" \\
      --solution "Use Glob to verify paths" \\
      --prevention "Always verify paths first"
        """
    )
    parser.add_argument(
        "--non-interactive",
        action="store_true",
        help="Run in non-interactive mode (requires all --* args)"
    )
    parser.add_argument(
        "--title",
        help="Short title for the error"
    )
    parser.add_argument(
        "--problem",
        help="Problem description"
    )
    parser.add_argument(
        "--root-cause",
        help="Root cause analysis"
    )
    parser.add_argument(
        "--solution",
        help="How to fix the error"
    )
    parser.add_argument(
        "--prevention",
        help="How to prevent in future"
    )
    parser.add_argument(
        "--project",
        default="",
        help="Project name (optional)"
    )
    parser.add_argument(
        "--quick-solution",
        help="Quick solution summary for reference table"
    )
    parser.add_argument(
        "--no-commit",
        action="store_true",
        help="Skip git commit creation"
    )
    parser.add_argument(
        "--no-push",
        action="store_true",
        help="Skip automatic git push after commit"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without writing files"
    )

    args = parser.parse_args()

    # Setup colors
    setup_colors()

    # Validate non-interactive mode
    if args.non_interactive:
        missing = []
        if not args.title:
            missing.append("--title")
        if not args.problem:
            missing.append("--problem")
        if not args.root_cause:
            missing.append("--root-cause")
        if not args.solution:
            missing.append("--solution")
        if not args.prevention:
            missing.append("--prevention")

        if missing:
            print_error(f"Non-interactive mode requires: {', '.join(missing)}")
            return 1

        rule_data = {
            'title': args.title,
            'problem': args.problem,
            'root_cause': args.root_cause,
            'solution': args.solution,
            'prevention': args.prevention,
            'project': args.project,
            'quick_solution': args.quick_solution or args.solution[:50],
        }
    else:
        rule_data = interactive_input()

    # Validate fields
    validation_errors = validate_rule_fields(
        rule_data['title'],
        rule_data['problem'],
        rule_data['root_cause'],
        rule_data['solution'],
        rule_data['prevention']
    )

    if validation_errors:
        for error in validation_errors:
            print_error(error)
        return 1

    # Get file paths
    template_path = get_template_memory_path()
    global_path = get_global_memory_path()

    if not template_path.exists():
        print_error(f"Template memory file not found: {template_path}")
        return 1

    # Read current content
    template_content = template_path.read_text(encoding="utf-8")

    # Get next ERR number
    next_num = get_next_err_number(template_content)
    category = get_category_for_number(next_num)

    print_header("New Rule Summary")
    print(f"  {Colors.OKCYAN}Error ID:{Colors.ENDC} ERR-{next_num:03d}")
    print(f"  {Colors.OKCYAN}Category:{Colors.ENDC} {category}")
    print(f"  {Colors.OKCYAN}Title:{Colors.ENDC} {rule_data['title']}")
    print()

    # Format the rule entry
    rule_entry = format_rule_entry(
        next_num,
        rule_data['title'],
        rule_data['problem'],
        rule_data['root_cause'],
        rule_data['solution'],
        rule_data['prevention'],
        rule_data.get('project', ''),
        category
    )

    if args.dry_run:
        print_header("Dry Run - Preview")
        print(rule_entry)
        print()
        print_info("No files were modified. Run without --dry-run to add the rule.")
        return 0

    # Update template memory
    print_info("Updating template memory.md...")
    new_template_content = insert_rule_into_content(
        template_content,
        rule_entry,
        next_num
    )

    # Update quick reference table
    new_template_content = update_quick_reference_table(
        new_template_content,
        next_num,
        rule_data['title'],
        rule_data.get('quick_solution', rule_data['solution'][:50])
    )

    # Verify write access before writing
    can_write, error_msg = verify_write_access(template_path)
    if not can_write:
        print_error(f"Cannot write to template: {error_msg}")
        return 1

    # Write template memory
    template_path.write_text(new_template_content, encoding="utf-8")
    print_success(f"Updated: {template_path}")

    # Update global memory if it exists
    if global_path.exists():
        print_info("Updating global memory.md...")

        # Verify write access before writing
        can_write, error_msg = verify_write_access(global_path)
        if not can_write:
            print_warning(f"Cannot write to global memory: {error_msg}")
            print_info("Skipping global memory update")
        else:
            global_content = global_path.read_text(encoding="utf-8")

            new_global_content = insert_rule_into_content(
                global_content,
                rule_entry,
                next_num
            )

            new_global_content = update_quick_reference_table(
                new_global_content,
                next_num,
                rule_data['title'],
                rule_data.get('quick_solution', rule_data['solution'][:50])
            )

            global_path.write_text(new_global_content, encoding="utf-8")
        print_success(f"Updated: {global_path}")

    # Create git commit
    if not args.no_commit:
        if create_git_commit(next_num, rule_data['title']):
            # Auto-push after successful commit
            if not args.no_push:
                auto_push_rules(args.dry_run)

    print_header("Rule Added Successfully")
    print_success(f"ERR-{next_num:03d}: {rule_data['title']}")
    print()
    print_info("To apply changes globally, run:")
    print("  python scripts/install.py --force")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
