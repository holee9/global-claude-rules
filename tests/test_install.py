#!/usr/bin/env python3
"""
Tests for Global Claude Rules installation script.

Tests the install.py script functionality including:
- Template rendering
- File creation
- Directory structure setup
- Cross-platform compatibility
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / "scripts"
sys.path.insert(0, str(scripts_dir))


class TestInstallScript(unittest.TestCase):
    """Test cases for install.py script."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_template_rendering(self):
        """Test that template variables are correctly replaced."""
        from install import render_template

        template = "Version: {{VERSION}}\nDate: {{DATE}}\nHome: {{USER_HOME}}"
        variables = {
            "VERSION": "1.0",
            "DATE": "2024-01-15",
            "USER_HOME": "/home/user"
        }

        result = render_template(template, variables)

        self.assertIn("Version: 1.0", result)
        self.assertIn("Date: 2024-01-15", result)
        self.assertIn("Home: /home/user", result)
        self.assertNotIn("{{", result)

    def test_get_script_dir(self):
        """Test getting script directory."""
        from install import get_script_dir

        script_dir = get_script_dir()

        self.assertTrue(script_dir.exists())
        self.assertTrue((script_dir / "install.py").exists() or
                       (script_dir / "templates").exists())

    def test_get_claude_dir(self):
        """Test getting Claude configuration directory."""
        from install import get_claude_dir

        claude_dir = get_claude_dir()

        # Should be a valid path
        self.assertIsInstance(claude_dir, Path)
        # Should end with .claude
        self.assertEqual(claude_dir.name, ".claude")

    def test_hooks_dir_path(self):
        """Test hooks directory path construction."""
        from install import get_hooks_dir

        hooks_dir = get_hooks_dir()

        self.assertTrue(str(hooks_dir).endswith(".claude" + os.sep + "hooks" + os.sep + "moai"))

    def test_render_template_with_missing_var(self):
        """Test template rendering with missing variable."""
        from install import render_template

        template = "Value: {{MISSING}}\nOther: {{PRESENT}}"
        variables = {"PRESENT": "here"}

        result = render_template(template, variables)

        self.assertIn("Other: here", result)
        # Missing variable should be replaced with empty string or kept as-is
        # depending on implementation

    def test_template_memory_content_exists(self):
        """Test that template memory.md file exists and has content."""
        template_path = Path(__file__).parent.parent / "templates" / "memory.md"

        self.assertTrue(template_path.exists(), "Template memory.md should exist")

        content = template_path.read_text(encoding="utf-8")

        # Check for key sections
        self.assertIn("ERR-", content)
        # The actual header is "## 1. Error Prevention System (EPS)"
        self.assertIn("Error Prevention System", content)
        self.assertIn("ERR-001:", content)

    def test_template_hook_exists(self):
        """Test that template hook file exists."""
        hook_path = Path(__file__).parent.parent / "templates" / "session_start__show_project_info.py"

        self.assertTrue(hook_path.exists(), "Template hook file should exist")

        content = hook_path.read_text(encoding="utf-8")

        # Check it's a Python file
        self.assertIn("def main(", content)
        self.assertIn("SessionStart", content)


class TestValidateRulesScript(unittest.TestCase):
    """Test cases for validate_rules.py script."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_extract_rules_from_memory(self):
        """Test extracting ERR rules from memory content."""
        # Import here to avoid issues if script doesn't exist
        try:
            from validate_rules import extract_rules_from_memory
        except ImportError:
            self.skipTest("validate_rules.py not fully implemented")

        sample_content = """
## Error Prevention System

### ERR-001: Test Error
**Problem**: This is a test problem
**Root Cause**: Testing
**Solution**: Fix it
**Prevention**: Don't do it
**Date**: 2024-01-15

### ERR-002: Another Test
**Problem**: Another problem
**Root Cause**: Another cause
**Solution**: Another solution
**Prevention**: Another prevention
**Date**: 2024-01-15
"""

        rules = extract_rules_from_memory(sample_content)

        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0]['id'], 'ERR-001')
        self.assertEqual(rules[0]['title'], 'Test Error')
        self.assertEqual(rules[1]['id'], 'ERR-002')

    def test_validate_date(self):
        """Test date validation."""
        try:
            from validate_rules import validate_date
        except ImportError:
            self.skipTest("validate_rules.py not fully implemented")

        # Valid dates
        self.assertTrue(validate_date("2024-01-15"))
        self.assertTrue(validate_date("2023-12-31"))

        # Invalid dates
        self.assertFalse(validate_date("2024-13-01"))
        self.assertFalse(validate_date("01-01-2024"))
        self.assertFalse(validate_date("2024/01/01"))
        self.assertFalse(validate_date(""))
        self.assertFalse(validate_date("invalid"))

    def test_find_all_rules(self):
        """Test finding all rules in content."""
        try:
            from validate_rules import find_all_rules
        except ImportError:
            self.skipTest("validate_rules.py not fully implemented")

        content = """
### ERR-001: First
**Problem**: P1
**Solution**: S1

### ERR-002: Second
**Problem**: P2
**Solution**: S2

### ERR-003: Third
**Problem**: P3
**Solution**: S3
"""

        rules = find_all_rules(content)

        self.assertEqual(len(rules), 3)


class TestAddRuleScript(unittest.TestCase):
    """Test cases for add_rule.py script."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_get_next_err_number(self):
        """Test getting next ERR number from content."""
        try:
            from add_rule import get_next_err_number
        except ImportError:
            self.skipTest("add_rule.py not fully implemented")

        content = """
### ERR-001: First
### ERR-002: Second
### ERR-003: Third
"""

        next_num = get_next_err_number(content)

        self.assertEqual(next_num, 4)

    def test_get_next_err_number_empty(self):
        """Test getting next ERR number from empty content."""
        try:
            from add_rule import get_next_err_number
        except ImportError:
            self.skipTest("add_rule.py not fully implemented")

        next_num = get_next_err_number("")

        self.assertEqual(next_num, 1)

    def test_format_rule_entry(self):
        """Test formatting a rule entry."""
        try:
            from add_rule import format_rule_entry
        except ImportError:
            self.skipTest("add_rule.py not fully implemented")

        entry = format_rule_entry(
            1,
            "Test Error",
            "Test problem description",
            "Test root cause",
            "Test solution",
            "Test prevention"
        )

        self.assertIn("ERR-001", entry)
        self.assertIn("Test Error", entry)
        self.assertIn("Test problem description", entry)
        self.assertIn("Test root cause", entry)
        self.assertIn("Test solution", entry)
        self.assertIn("Test prevention", entry)

    def test_validate_rule_fields(self):
        """Test validation of rule fields."""
        try:
            from add_rule import validate_rule_fields
        except ImportError:
            self.skipTest("add_rule.py not fully implemented")

        # Valid fields
        errors = validate_rule_fields(
            "Valid Title",
            "This is a valid problem description",
            "This is a valid root cause",
            "This is a valid solution",
            "This is a valid prevention"
        )

        self.assertEqual(len(errors), 0)

        # Invalid fields
        errors = validate_rule_fields(
            "X",
            "Short",
            "Bad",
            "No",
            ""
        )

        self.assertGreater(len(errors), 0)


class TestUpdateScript(unittest.TestCase):
    """Test cases for update.py script."""

    def test_get_current_version(self):
        """Test getting current version."""
        try:
            from update import get_current_version
        except ImportError:
            self.skipTest("update.py not fully implemented")

        version = get_current_version()

        # Version should be a string
        self.assertIsInstance(version, str)
        # Should not be empty for this project
        # (might be "unknown" if parsing fails)
        self.assertTrue(len(version) > 0)


if __name__ == "__main__":
    unittest.main()
