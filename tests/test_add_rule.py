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

        self.assertIn("001~099", get_category_for_number(1))
        self.assertIn("001~099", get_category_for_number(99))
        self.assertIn("100~199", get_category_for_number(100))
        self.assertIn("100~199", get_category_for_number(150))
        self.assertIn("200~299", get_category_for_number(200))
        self.assertIn("300~399", get_category_for_number(300))
        self.assertIn("400~499", get_category_for_number(400))
        self.assertIn("500~599", get_category_for_number(500))
        self.assertIn("600~699", get_category_for_number(600))

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
            with patch('sys.exit') as mock_exit:
                try:
                    main()
                except SystemExit:
                    pass
                # Exit code should be 1 for error
                mock_exit.assert_called_with(1)

    def test_dry_run_mode(self):
        """Test dry-run mode doesn't modify files."""
        # This is a conceptual test - actual implementation would
        # require mocking file operations
        pass


if __name__ == "__main__":
    unittest.main()
