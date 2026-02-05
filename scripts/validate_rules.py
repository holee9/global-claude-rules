#!/usr/bin/env python3
"""
Global Claude Rules - Validate ERR Rules

Validation tool for error prevention rules in the global memory.
Checks for:
- Duplicate ERR IDs
- Missing required fields
- Format consistency
- Date validation
- Category range validation

Usage:
    python scripts/validate_rules.py
    python scripts/validate_rules.py --file templates/memory.md
    python scripts/validate_rules.py --verbose
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import NamedTuple


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def disable():
        """Disable colors."""
        Colors.HEADER = ''
        Colors.OKBLUE = ''
        Colors.OKCYAN = ''
        Colors.OKGREEN = ''
        Colors.WARNING = ''
        Colors.FAIL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''


def setup_colors():
    """Setup colors based on platform."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except (AttributeError, OSError):
            Colors.disable()


def print_header(text: str):
    """Print a header."""
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


class ValidationError(NamedTuple):
    """A validation error with location and message."""
    err_id: str
    field: str
    message: str
    line: int = 0


class ValidationResult:
    """Result of validation with errors and warnings."""

    def __init__(self):
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []
        self.rules_found: list[str] = []
        self.duplicates: dict[str, list[int]] = {}

    def add_error(self, err_id: str, field: str, message: str, line: int = 0):
        """Add an error."""
        self.errors.append(ValidationError(err_id, field, message, line))

    def add_warning(self, err_id: str, field: str, message: str, line: int = 0):
        """Add a warning."""
        self.warnings.append(ValidationError(err_id, field, message, line))

    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def total_issues(self) -> int:
        """Total number of issues."""
        return len(self.errors) + len(self.warnings)


def parse_err_rule(content: str, start_idx: int) -> tuple[dict, int]:
    """Parse a single ERR rule from content.

    Args:
        content: The file content
        start_idx: Starting index of the rule (ERR-XXX)

    Returns:
        Tuple of (rule_dict, end_idx)
    """
    lines = content.split("\n")
    rule = {
        'id': '',
        'title': '',
        'problem': '',
        'root_cause': '',
        'solution': '',
        'prevention': '',
        'date': '',
        'project': '',
        'category': '',
        'line': start_idx + 1,
    }

    # Extract ERR ID and title from header
    header_match = re.search(r'### (ERR-\d+):\s*(.+)', lines[start_idx])
    if header_match:
        rule['id'] = header_match.group(1)
        rule['title'] = header_match.group(2).strip()

    # Parse following lines until next ERR or section end
    i = start_idx + 1
    while i < len(lines):
        line = lines[i]

        # Stop at next ERR rule or major section
        if re.match(r'###\s+ERR-\d+:', line) or line.startswith('## '):
            break

        # Parse fields
        if '**Problem**:' in line:
            rule['problem'] = line.split('**Problem**:', 1)[1].strip()
        elif '**Root Cause**:' in line:
            rule['root_cause'] = line.split('**Root Cause**:', 1)[1].strip()
        elif '**Solution**:' in line:
            rule['solution'] = line.split('**Solution**:', 1)[1].strip()
        elif '**Prevention**:' in line:
            rule['prevention'] = line.split('**Prevention**:', 1)[1].strip()
        elif '**Date**:' in line:
            rule['date'] = line.split('**Date**:', 1)[1].strip()
        elif '**Project**:' in line:
            rule['project'] = line.split('**Project**:', 1)[1].strip()
        elif '**Category**:' in line:
            rule['category'] = line.split('**Category**:', 1)[1].strip()

        i += 1

    return rule, i


def find_all_rules(content: str) -> list[dict]:
    """Find all ERR rules in the content.

    Args:
        content: The file content

    Returns:
        List of rule dictionaries
    """
    rules = []
    lines = content.split("\n")

    for i, line in enumerate(lines):
        if re.match(r'###\s+ERR-\d+:', line):
            rule, _ = parse_err_rule(content, i)
            if rule['id']:
                rules.append(rule)

    return rules


def validate_date(date_str: str) -> bool:
    """Validate date format (YYYY-MM-DD).

    Args:
        date_str: Date string to validate

    Returns:
        True if valid, False otherwise
    """
    if not date_str:
        return False

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_category_range(err_id: str, category: str) -> bool:
    """Validate that category matches ERR number range.

    Args:
        err_id: The ERR ID (e.g., ERR-001)
        category: The category string

    Returns:
        True if category matches range, False otherwise
    """
    num_match = re.search(r'ERR-(\d+)', err_id)
    if not num_match:
        return False

    num = int(num_match.group(1))
    category_lower = category.lower()

    # Check if category mentions the correct range
    if 1 <= num <= 99:
        return "001~099" in category or "general" in category_lower or "system" in category_lower
    elif 100 <= num <= 199:
        return "100~199" in category or "git" in category_lower or "version" in category_lower
    elif 200 <= num <= 299:
        return "200~299" in category or "build" in category_lower or "compilation" in category_lower
    elif 300 <= num <= 399:
        return "300~399" in category or ("fpga" in category_lower or "hardware" in category_lower)
    elif 400 <= num <= 499:
        return "400~499" in category or "backend" in category_lower or "api" in category_lower
    elif 500 <= num <= 599:
        return "500~599" in category or "frontend" in category_lower or "ui" in category_lower
    elif 600 <= num <= 699:
        return "600~699" in category or "mfc" in category_lower or "win32" in category_lower

    # For numbers outside standard ranges, don't validate category
    return True


def validate_rules(content: str, verbose: bool = False) -> ValidationResult:
    """Validate all ERR rules in the content.

    Args:
        content: The file content
        verbose: Enable verbose output

    Returns:
        ValidationResult with all issues found
    """
    result = ValidationResult()
    rules = find_all_rules(content)
    result.rules_found = [r['id'] for r in rules]

    if verbose:
        print_info(f"Found {len(rules)} ERR rules to validate")

    # Check for duplicates
    id_counts: dict[str, int] = {}
    id_positions: dict[str, list[int]] = {}

    for rule in rules:
        err_id = rule['id']
        id_counts[err_id] = id_counts.get(err_id, 0) + 1

        if err_id not in id_positions:
            id_positions[err_id] = []
        id_positions[err_id].append(rule['line'])

    for err_id, count in id_counts.items():
        if count > 1:
            result.duplicates[err_id] = id_positions[err_id]
            result.add_error(err_id, "id", f"Duplicate ERR ID (found {count} times)")

    # Validate each rule
    required_fields = {
        'title': 'Title',
        'problem': 'Problem',
        'root_cause': 'Root Cause',
        'solution': 'Solution',
        'prevention': 'Prevention',
    }

    for rule in rules:
        err_id = rule['id']

        # Check required fields
        for field, field_name in required_fields.items():
            value = rule.get(field, '')
            if not value or len(value) < 5:
                result.add_error(err_id, field, f"{field_name} is too short or missing (min 5 chars)", rule['line'])

        # Validate date format
        if rule['date']:
            if not validate_date(rule['date']):
                result.add_error(err_id, 'date', f"Invalid date format: {rule['date']} (use YYYY-MM-DD)", rule['line'])
        else:
            result.add_warning(err_id, 'date', "Date field is missing", rule['line'])

        # Validate category range
        if rule['category']:
            if not validate_category_range(err_id, rule['category']):
                result.add_warning(err_id, 'category',
                    f"Category '{rule['category']}' may not match ERR number range", rule['line'])

        # Check for common formatting issues
        title = rule.get('title', '')
        if title and not title[0].isupper():
            result.add_warning(err_id, 'title', "Title should start with capital letter", rule['line'])

    return result


def validate_quick_reference_table(content: str, rules: list[dict]) -> ValidationResult:
    """Validate the quick reference table matches the rules.

    Args:
        content: The file content
        rules: List of parsed rules

    Returns:
        ValidationResult with table issues
    """
    result = ValidationResult()

    # Find the quick reference table
    table_match = re.search(
        r'\| Error ID \| Description \| Quick Solution \|\n((?:\|.*?\|.*?\|.*?\|\n)+)',
        content
    )

    if not table_match:
        result.add_warning("TABLE", "table", "Quick reference table not found")
        return result

    table_content = table_match.group(0)
    table_err_ids = set(re.findall(r'\|(ERR-\d+)\|', table_content))

    # Check for rules missing from table
    rule_ids = {r['id'] for r in rules}

    missing_from_table = rule_ids - table_err_ids
    for err_id in missing_from_table:
        result.add_warning(err_id, "table", f"Rule not found in quick reference table")

    extra_in_table = table_err_ids - rule_ids
    for err_id in extra_in_table:
        result.add_warning(err_id, "table", f"Table entry has no corresponding rule")

    return result


def print_validation_result(result: ValidationResult, verbose: bool = False):
    """Print validation results.

    Args:
        result: The validation result
        verbose: Enable verbose output
    """
    print_header("Validation Results")

    # Summary
    if result.is_valid() and not result.warnings:
        print_success("All validations passed!")
        print_info(f"Checked {len(result.rules_found)} ERR rules")
        return

    # Print errors
    if result.errors:
        print_error(f"Found {len(result.errors)} error(s):\n")
        for error in result.errors:
            line_info = f" (line {error.line})" if error.line > 0 else ""
            print(f"  {Colors.FAIL}✗{Colors.ENDC} {error.err_id}: {error.field}{line_info}")
            print(f"    {error.message}")

        if result.warnings:
            print()

    # Print warnings
    if result.warnings:
        print_warning(f"Found {len(result.warnings)} warning(s):\n")
        for warning in result.warnings:
            line_info = f" (line {warning.line})" if warning.line > 0 else ""
            print(f"  {Colors.WARNING}⚠{Colors.ENDC} {warning.err_id}: {warning.field}{line_info}")
            print(f"    {warning.message}")

    # Summary
    print_header("Summary")
    print(f"  Total rules: {len(result.rules_found)}")
    print(f"  Errors: {len(result.errors)}")
    print(f"  Warnings: {len(result.warnings)}")

    if result.duplicates:
        print(f"\n  Duplicate IDs:")
        for err_id, positions in result.duplicates.items():
            print(f"    {err_id}: lines {positions}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate ERR rules in Global Claude Rules",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exit codes:
  0: Validation passed (no errors)
  1: Validation failed (errors found)
  2: File not found or read error
        """
    )
    parser.add_argument(
        "--file",
        "-f",
        default="templates/memory.md",
        help="Path to memory.md file (default: templates/memory.md)"
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Quiet mode (only print errors)"
    )

    args = parser.parse_args()

    # Setup colors
    setup_colors()

    file_path = Path(args.file)

    if not file_path.exists():
        print_error(f"File not found: {file_path}")
        return 2

    # Read file
    try:
        content = file_path.read_text(encoding="utf-8")
    except OSError as e:
        print_error(f"Failed to read file: {e}")
        return 2

    if args.verbose and not args.quiet:
        print_info(f"Validating: {file_path}")

    # Validate rules
    result = validate_rules(content, args.verbose)

    # Also validate quick reference table
    rules = find_all_rules(content)
    table_result = validate_quick_reference_table(content, rules)
    result.warnings.extend(table_result.warnings)

    # Print results
    if not args.quiet:
        print_validation_result(result, args.verbose)
    elif result.errors:
        # Only print errors in quiet mode
        for error in result.errors:
            print(f"{error.err_id}: {error.message}", file=sys.stderr)

    return 0 if result.is_valid() else 1


if __name__ == "__main__":
    sys.exit(main())
