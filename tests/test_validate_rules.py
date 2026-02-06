#!/usr/bin/env python3
"""
Tests for validate_rules.py script.

Tests the rule validation functionality including:
- Duplicate detection
- Required field validation
- Date format validation
- Category range validation
- Quick reference table validation
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


class TestValidateRules(unittest.TestCase):
    """Test cases for validate_rules.py functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_parse_err_rule(self):
        """Test parsing a single ERR rule."""
        try:
            from validate_rules import parse_err_rule
        except ImportError:
            self.skipTest("validate_rules.py not available")

        content = """
### ERR-001: Test Error Title
**Problem**: This is the problem
**Root Cause**: This is the cause
**Solution**: This is the solution
**Prevention**: This is prevention
**Date**: 2024-01-15
**Project**: TestProject
**Category**: Test Category (ERR-001~ERR-099)

Some other content here
### ERR-002: Another Error
"""

        rule, end_idx = parse_err_rule(content, 1)  # Line 1 is where ERR-001 starts

        self.assertEqual(rule['id'], 'ERR-001')
        self.assertEqual(rule['title'], 'Test Error Title')
        self.assertEqual(rule['problem'], 'This is the problem')
        self.assertEqual(rule['root_cause'], 'This is the cause')
        self.assertEqual(rule['solution'], 'This is the solution')
        self.assertEqual(rule['prevention'], 'This is prevention')
        self.assertEqual(rule['date'], '2024-01-15')
        self.assertEqual(rule['project'], 'TestProject')
        self.assertIn('ERR-001~ERR-099', rule['category'])

    def test_find_all_rules(self):
        """Test finding all rules in content."""
        try:
            from validate_rules import find_all_rules
        except ImportError:
            self.skipTest("validate_rules.py not available")

        content = """
## Section Header

### ERR-001: First Error
**Problem**: Problem 1
**Solution**: Solution 1

### ERR-002: Second Error
**Problem**: Problem 2
**Solution**: Solution 2

### ERR-003: Third Error
**Problem**: Problem 3
**Solution**: Solution 3
"""

        rules = find_all_rules(content)

        self.assertEqual(len(rules), 3)
        self.assertEqual(rules[0]['id'], 'ERR-001')
        self.assertEqual(rules[1]['id'], 'ERR-002')
        self.assertEqual(rules[2]['id'], 'ERR-003')

    def test_validate_date_valid(self):
        """Test date validation with valid dates."""
        try:
            from validate_rules import validate_date
        except ImportError:
            self.skipTest("validate_rules.py not available")

        self.assertTrue(validate_date("2024-01-15"))
        self.assertTrue(validate_date("2023-12-31"))
        self.assertTrue(validate_date("2020-02-29"))  # Leap year
        self.assertTrue(validate_date("1999-01-01"))

    def test_validate_date_invalid(self):
        """Test date validation with invalid dates."""
        try:
            from validate_rules import validate_date
        except ImportError:
            self.skipTest("validate_rules.py not available")

        self.assertFalse(validate_date(""))
        self.assertFalse(validate_date("2024-13-01"))  # Invalid month
        self.assertFalse(validate_date("2024-00-01"))  # Invalid month
        self.assertFalse(validate_date("2024-01-32"))  # Invalid day
        self.assertFalse(validate_date("2024-01-00"))  # Invalid day
        self.assertFalse(validate_date("01-01-2024"))  # Wrong format
        self.assertFalse(validate_date("2024/01/01"))  # Wrong separator
        self.assertFalse(validate_date("not-a-date"))  # Not a date

    def test_validate_category_range(self):
        """Test category range validation."""
        try:
            from validate_rules import validate_category_range
        except ImportError:
            self.skipTest("validate_rules.py not available")

        # General/System errors (001-099)
        self.assertTrue(validate_category_range("ERR-001", "General (ERR-001~ERR-099)"))
        self.assertTrue(validate_category_range("ERR-099", "System errors (ERR-001~ERR-099)"))

        # Git/Version control (100-199)
        self.assertTrue(validate_category_range("ERR-100", "Git errors (ERR-100~ERR-199)"))
        self.assertTrue(validate_category_range("ERR-150", "Version control (ERR-100~ERR-199)"))

        # Build/Compilation (200-299)
        self.assertTrue(validate_category_range("ERR-200", "Build errors (ERR-200~ERR-299)"))

        # FPGA/Hardware (300-399)
        self.assertTrue(validate_category_range("ERR-300", "FPGA errors (ERR-300~ERR-399)"))

        # Backend/API (400-499)
        self.assertTrue(validate_category_range("ERR-400", "Backend errors (ERR-400~ERR-499)"))

        # Frontend/UI (500-599)
        self.assertTrue(validate_category_range("ERR-500", "Frontend errors (ERR-500~ERR-599)"))

        # MFC/Win32 (600-699)
        self.assertTrue(validate_category_range("ERR-600", "MFC errors (ERR-600~ERR-699)"))

    def test_validate_rules_no_errors(self):
        """Test validation with valid rules."""
        try:
            from validate_rules import validate_rules
        except ImportError:
            self.skipTest("validate_rules.py not available")

        content = """
### ERR-001: Valid Error
**Problem**: A valid problem description
**Root Cause**: A valid root cause
**Solution**: A valid solution
**Prevention**: A valid prevention
**Date**: 2024-01-15
**Category**: General (ERR-001~ERR-099)

### ERR-002: Another Valid Error
**Problem**: Another valid problem
**Root Cause**: Another valid cause
**Solution**: Another valid solution
**Prevention**: Another valid prevention
**Date**: 2024-01-15
**Category**: General (ERR-001~ERR-099)
"""

        result = validate_rules(content)

        self.assertTrue(result.is_valid())
        self.assertEqual(len(result.errors), 0)

    def test_validate_rules_with_duplicates(self):
        """Test duplicate detection."""
        try:
            from validate_rules import validate_rules
        except ImportError:
            self.skipTest("validate_rules.py not available")

        content = """
### ERR-001: First Error
**Problem**: Problem 1
**Solution**: Solution 1

### ERR-001: Duplicate Error
**Problem**: This is a duplicate ID
**Solution**: This should be caught
"""

        result = validate_rules(content)

        self.assertFalse(result.is_valid())
        self.assertGreater(len(result.errors), 0)
        self.assertIn('ERR-001', result.duplicates)

    def test_validate_rules_missing_fields(self):
        """Test validation catches missing required fields."""
        try:
            from validate_rules import validate_rules
        except ImportError:
            self.skipTest("validate_rules.py not available")

        content = """
### ERR-001: Incomplete Error
**Problem**: P
**Root Cause**: C
**Solution**: Sol
**Prevention**: Pr

### ERR-002: Another Incomplete
**Problem**: Too short
"""

        result = validate_rules(content)

        # Should have errors for fields that are too short
        self.assertGreater(len(result.errors), 0)

    def test_validate_rules_invalid_dates(self):
        """Test validation catches invalid dates."""
        try:
            from validate_rules import validate_rules
        except ImportError:
            self.skipTest("validate_rules.py not available")

        content = """
### ERR-001: Invalid Date Error
**Problem**: A problem
**Root Cause**: A cause
**Solution**: A solution
**Prevention**: A prevention
**Date**: 2024-13-45

### ERR-002: Wrong Format Date
**Problem**: Another problem
**Root Cause**: Another cause
**Solution**: Another solution
**Prevention**: Another prevention
**Date**: 01/01/2024
"""

        result = validate_rules(content)

        # Should have errors for invalid dates
        date_errors = [e for e in result.errors if e.field == 'date']
        self.assertGreater(len(date_errors), 0)

    def test_validate_quick_reference_table(self):
        """Test quick reference table validation."""
        try:
            from validate_rules import validate_quick_reference_table
        except ImportError:
            self.skipTest("validate_rules.py not available")

        content = """
| Error ID | Description | Quick Solution |
|----------|-------------|----------------|
| ERR-001 | Error One | Solution 1 |
| ERR-002 | Error Two | Solution 2 |

### ERR-001: Error One
**Problem**: Problem 1
**Solution**: Solution 1

### ERR-002: Error Two
**Problem**: Problem 2
**Solution**: Solution 2

### ERR-003: Missing From Table
**Problem**: Problem 3
**Solution**: Solution 3
"""

        rules = [
            {'id': 'ERR-001', 'title': 'Error One'},
            {'id': 'ERR-002', 'title': 'Error Two'},
            {'id': 'ERR-003', 'title': 'Missing From Table'},
        ]

        result = validate_quick_reference_table(content, rules)

        # Should have warning for ERR-003 missing from table
        table_warnings = [w for w in result.warnings if w.field == 'table']
        self.assertGreater(len(table_warnings), 0)

    def test_validation_result_summary(self):
        """Test ValidationResult summary methods."""
        try:
            from validate_rules import ValidationResult
        except ImportError:
            self.skipTest("validate_rules.py not available")

        result = ValidationResult()

        # Initially valid with no issues
        self.assertTrue(result.is_valid())
        self.assertEqual(result.total_issues(), 0)

        # Add an error
        result.add_error('ERR-001', 'title', 'Title too short')

        self.assertFalse(result.is_valid())
        self.assertEqual(result.total_issues(), 1)

        # Add a warning
        result.add_warning('ERR-002', 'date', 'Date missing')

        self.assertFalse(result.is_valid())
        self.assertEqual(result.total_issues(), 2)

        # Check rule tracking
        result.rules_found = ['ERR-001', 'ERR-002']
        self.assertEqual(len(result.rules_found), 2)


class TestValidateRulesCLI(unittest.TestCase):
    """Test validate_rules.py CLI behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_memory = Path(self.temp_dir) / "memory.md"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_validate_file_not_found(self):
        """Test handling of missing file."""
        try:
            from validate_rules import main
        except ImportError:
            self.skipTest("validate_rules.py not available")

        non_existent = Path(self.temp_dir) / "does_not_exist.md"

        with patch('sys.argv', ['validate_rules.py', '--file', str(non_existent)]):
            # main() returns 2 for file not found error
            result = main()
            # Should return 2 for file not found
            self.assertEqual(result, 2)

    def test_validate_valid_file(self):
        """Test validation of a valid file."""
        # Create a valid memory file
        valid_content = """# Global Memory

## Error Prevention System

### ERR-001: Valid Test Error
**Problem**: This is a valid test problem description
**Root Cause**: This is a valid test root cause
**Solution**: This is a valid test solution
**Prevention**: This is a valid test prevention
**Date**: 2024-01-15
**Category**: General (ERR-001~ERR-099)
"""
        self.test_memory.write_text(valid_content, encoding="utf-8")

        try:
            from validate_rules import main
        except ImportError:
            self.skipTest("validate_rules.py not available")

        with patch('sys.argv', ['validate_rules.py', '--file', str(self.test_memory)]):
            # main() returns 0 for valid file
            result = main()
            # Should return 0 for valid file
            self.assertEqual(result, 0)


if __name__ == "__main__":
    # Import patch for CLI tests
    from unittest.mock import patch
    unittest.main()
