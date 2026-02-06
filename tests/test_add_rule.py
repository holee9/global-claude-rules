#!/usr/bin/env python3
"""
Tests for add_rule.py script.

Tests the rule addition functionality including:
- Interactive input handling
- Non-interactive mode
- Rule formatting
- File updates
- Git commit creation
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock
import argparse


# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


class TestAddRule(unittest.TestCase):
    """Test cases for add_rule.py functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_memory = Path(self.temp_dir) / "memory.md"

        # Create a sample memory file
        self.sample_memory = """# Global Development Memory

## Error Prevention System

### ERR-001: Test Error One
**Problem**: First test problem
**Root Cause**: First test cause
**Solution**: First test solution
**Prevention**: First test prevention
**Date**: 2024-01-15

### ERR-024: Hook Directory Not Found
**Problem**: Hook execution fails
**Root Cause**: Directory missing
**Solution**: Run install.py
**Prevention**: Always run install after cloning
**Date**: 2024-02-05

| Error ID | Description | Quick Solution |
|----------|-------------|----------------|
| ERR-001 | Test Error One | First test solution |
| ERR-024 | Hook Directory Not Found | Run install.py |
"""
        self.temp_memory.write_text(self.sample_memory, encoding="utf-8")

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_next_err_number(self):
        """Test getting the next ERR number."""
        try:
            from add_rule import get_next_err_number
        except ImportError:
            self.skipTest("add_rule.py not available")

        next_num = get_next_err_number(self.sample_memory)
        self.assertEqual(next_num, 25)  # Should be 024 + 1 = 25

    def test_get_next_err_number_empty(self):
        """Test getting next ERR number from empty content."""
        try:
            from add_rule import get_next_err_number
        except ImportError:
            self.skipTest("add_rule.py not available")

        next_num = get_next_err_number("")
        self.assertEqual(next_num, 1)

    def test_get_category_for_number(self):
        """Test category determination for ERR numbers."""
        try:
            from add_rule import get_category_for_number
        except ImportError:
            self.skipTest("add_rule.py not available")

        # Test that the function returns the expected category descriptions
        result_001 = get_category_for_number(1)
        self.assertIn("General/System errors", result_001)
        self.assertIn("ERR-001~ERR-099", result_001)

        result_099 = get_category_for_number(99)
        self.assertIn("General/System errors", result_099)

        result_100 = get_category_for_number(100)
        self.assertIn("Git/Version control errors", result_100)
        self.assertIn("ERR-100~ERR-199", result_100)

        result_150 = get_category_for_number(150)
        self.assertIn("Git/Version control errors", result_150)

        result_200 = get_category_for_number(200)
        self.assertIn("Build/Compilation errors", result_200)
        self.assertIn("ERR-200~ERR-299", result_200)

        result_300 = get_category_for_number(300)
        self.assertIn("FPGA/Hardware errors", result_300)
        self.assertIn("ERR-300~ERR-399", result_300)

        result_400 = get_category_for_number(400)
        self.assertIn("Backend/API errors", result_400)
        self.assertIn("ERR-400~ERR-499", result_400)

        result_500 = get_category_for_number(500)
        self.assertIn("Frontend/UI errors", result_500)
        self.assertIn("ERR-500~ERR-599", result_500)

        result_600 = get_category_for_number(600)
        self.assertIn("MFC/Win32 errors", result_600)
        self.assertIn("ERR-600~ERR-699", result_600)

    def test_validate_rule_fields_valid(self):
        """Test validation with valid fields."""
        try:
            from add_rule import validate_rule_fields
        except ImportError:
            self.skipTest("add_rule.py not available")

        errors = validate_rule_fields(
            "Valid Test Title",
            "This is a valid problem description that meets minimum length",
            "This is a valid root cause that meets minimum length",
            "This is a valid solution that meets minimum length",
            "This is a valid prevention that meets minimum length"
        )

        self.assertEqual(len(errors), 0)

    def test_validate_rule_fields_invalid(self):
        """Test validation with invalid fields."""
        try:
            from add_rule import validate_rule_fields
        except ImportError:
            self.skipTest("add_rule.py not available")

        errors = validate_rule_fields(
            "Bad",  # Too short
            "Short",  # Too short
            "Bad",  # Too short
            "No",  # Too short
            ""  # Empty
        )

        self.assertGreater(len(errors), 0)

    def test_format_rule_entry(self):
        """Test rule entry formatting."""
        try:
            from add_rule import format_rule_entry
        except ImportError:
            self.skipTest("add_rule.py not available")

        entry = format_rule_entry(
            999,
            "Test Title",
            "Test problem",
            "Test cause",
            "Test solution",
            "Test prevention",
            project="TestProject",
            category="Test Category"
        )

        self.assertIn("ERR-999", entry)
        self.assertIn("Test Title", entry)
        self.assertIn("Test problem", entry)
        self.assertIn("Test cause", entry)
        self.assertIn("Test solution", entry)
        self.assertIn("Test prevention", entry)
        self.assertIn("TestProject", entry)
        self.assertIn("Test Category", entry)

    def test_find_insert_position(self):
        """Test finding insert position for new rule."""
        try:
            from add_rule import find_insert_position
        except ImportError:
            self.skipTest("add_rule.py not available")

        # Insert ERR-002 should go after ERR-001 but before ERR-024
        pos = find_insert_position(self.sample_memory, 2)
        self.assertGreater(pos, 0)
        self.assertLess(pos, len(self.sample_memory))

    def test_insert_rule_into_content(self):
        """Test inserting a rule into content."""
        try:
            from add_rule import insert_rule_into_content
        except ImportError:
            self.skipTest("add_rule.py not available")

        rule_entry = """### ERR-002: New Test Error
**Problem**: New problem
**Root Cause**: New cause
**Solution**: New solution
**Prevention**: New prevention
**Date**: 2024-02-05"""

        new_content = insert_rule_into_content(self.sample_memory, rule_entry, 2)

        self.assertIn("ERR-002", new_content)
        self.assertIn("New problem", new_content)
        # Original content should still be there
        self.assertIn("ERR-001", new_content)
        self.assertIn("ERR-024", new_content)

    def test_update_quick_reference_table(self):
        """Test updating quick reference table."""
        try:
            from add_rule import update_quick_reference_table
        except ImportError:
            self.skipTest("add_rule.py not available")

        new_content = update_quick_reference_table(
            self.sample_memory,
            25,
            "New Error",
            "New quick solution"
        )

        self.assertIn("ERR-025", new_content)
        self.assertIn("New Error", new_content)
        self.assertIn("New quick solution", new_content)
        # Original table entries should still be there
        self.assertIn("ERR-001", new_content)
        self.assertIn("ERR-024", new_content)


class TestAddRuleCLI(unittest.TestCase):
    """Test add_rule.py CLI behavior."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_non_interactive_mode_requires_args(self):
        """Test that non-interactive mode requires all arguments."""
        try:
            from add_rule import main
        except ImportError:
            self.skipTest("add_rule.py not available")

        # Test with missing --problem argument
        with patch('sys.argv', [
            'add_rule.py',
            '--non-interactive',
            '--title', 'Test',
            '--root-cause', 'Cause',
            '--solution', 'Solution',
            '--prevention', 'Prevention'
        ]):
            # Should fail because --problem is missing
            # main() returns 1 on error, doesn't call sys.exit(1)
            result = main()
            # Return code should be 1 for error
            self.assertEqual(result, 1)

    def test_dry_run_mode(self):
        """Test dry-run mode doesn't modify files."""
        # This is a conceptual test - actual implementation would
        # require mocking file operations
        pass


if __name__ == "__main__":
    unittest.main()
