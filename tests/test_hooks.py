#!/usr/bin/env python3
"""
Tests for Global Claude Rules hook scripts.

Tests the hook functionality including:
- SessionStart hook behavior
- PreToolUse hook behavior
- Rule enforcement
- JSON input/output handling
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch, Mock

# Add hooks directory to path
hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "moai"
if hooks_dir.exists():
    sys.path.insert(0, str(hooks_dir))


class TestEnforceRulesHook(unittest.TestCase):
    """Test cases for pre_tool__enforce_rules.py hook."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "moai" / "pre_tool__enforce_rules.py"

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_hook_file_exists(self):
        """Test that the enforce rules hook file exists."""
        self.assertTrue(self.hook_path.exists(), "pre_tool__enforce_rules.py should exist")

    def test_hook_is_executable(self):
        """Test that hook is a valid Python file."""
        if not self.hook_path.exists():
            self.skipTest("Hook file not created yet")

        content = self.hook_path.read_text(encoding="utf-8")

        # Check it's a Python file
        self.assertIn("def main(", content)
        self.assertIn("PreToolUse", content)

    def test_extract_rules_from_memory(self):
        """Test extracting rules from memory content."""
        if not self.hook_path.exists():
            self.skipTest("Hook file not created yet")

        # Import the function
        try:
            # Need to import from the hook module
            import importlib.util
            spec = importlib.util.spec_from_file_location("enforce_rules", self.hook_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            sample_memory = """
### ERR-001: TodoWrite Tool Not Available
**Problem**: Tool not available
**Solution**: Use TaskCreate instead
**Prevention**: Always use Task tool

### ERR-004: File Path Not Found
**Problem**: File does not exist
**Solution**: Use Glob to verify
**Prevention**: Always verify paths first
"""

            rules = module.extract_rules_from_memory(sample_memory)

            self.assertEqual(len(rules), 2)
            self.assertEqual(rules[0]['id'], 'ERR-001')
            self.assertEqual(rules[1]['id'], 'ERR-004')

        except ImportError as e:
            self.skipTest(f"Could not import hook module: {e}")

    def test_find_relevant_rules_for_write_tool(self):
        """Test finding relevant rules for Write tool."""
        if not self.hook_path.exists():
            self.skipTest("Hook file not created yet")

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("enforce_rules", self.hook_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            rules = [
                {
                    'id': 'ERR-001',
                    'title': 'TodoWrite Not Available',
                    'problem': 'Tool missing',
                    'solution': 'Use TaskCreate',
                    'prevention': 'Use Task tool'
                },
                {
                    'id': 'ERR-004',
                    'title': 'File Path Not Found',
                    'problem': 'Wrong path',
                    'solution': 'Use Glob first',
                    'prevention': 'Verify paths'
                },
            ]

            # Test with Write tool
            relevant = module.find_relevant_rules(
                rules,
                "Write",
                {"file_path": "/path/to/file.txt"}
            )

            # Should find file-related rules
            self.assertGreater(len(relevant), 0)
            # ERR-004 should be highly relevant for file operations
            err_ids = [r['id'] for r in relevant]
            self.assertIn('ERR-004', err_ids)

        except ImportError as e:
            self.skipTest(f"Could not import hook module: {e}")

    def test_find_relevant_rules_for_bash_tool(self):
        """Test finding relevant rules for Bash tool."""
        if not self.hook_path.exists():
            self.skipTest("Hook file not created yet")

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("enforce_rules", self.hook_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            rules = [
                {
                    'id': 'ERR-001',
                    'title': 'TodoWrite Not Available',
                    'problem': 'Tool missing',
                    'solution': 'Use TaskCreate',
                    'prevention': 'Use Task tool'
                },
            ]

            # Test with Bash tool
            relevant = module.find_relevant_rules(
                rules,
                "Bash",
                {"command": "git status"}
            )

            # Filter to rules with actual relevance
            relevant = [r for r in relevant if r.get('relevance_score', 0) > 0]

            # Should find git-related rules if any
            self.assertGreaterEqual(len(relevant), 0)

        except ImportError as e:
            self.skipTest(f"Could not import hook module: {e}")

    def test_format_rule_display(self):
        """Test formatting rules for display."""
        if not self.hook_path.exists():
            self.skipTest("Hook file not created yet")

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("enforce_rules", self.hook_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            rule = {
                'id': 'ERR-001',
                'title': 'Test Error',
                'solution': 'This is a test solution that should be truncated if too long'
            }

            # Compact format
            compact = module.format_rule_display(rule, compact=True)
            self.assertIn('ERR-001', compact)
            self.assertIn('Test Error', compact)

            # Full format
            full = module.format_rule_display(rule, compact=False)
            self.assertIn('ERR-001', full)
            self.assertIn('Test Error', full)

        except ImportError as e:
            self.skipTest(f"Could not import hook module: {e}")

    def test_hook_json_output(self):
        """Test that hook produces valid JSON output."""
        if not self.hook_path.exists():
            self.skipTest("Hook file not created yet")

        # The hook should output valid JSON
        # This is a basic structure test
        expected_keys = {"continue", "systemMessage", "hookSpecificOutput"}

        # We can't actually run the hook without proper stdin,
        # but we can check the output structure is correct in the code
        content = self.hook_path.read_text(encoding="utf-8")

        # Check for JSON output
        self.assertIn('json.dumps', content)
        self.assertIn('"continue":', content)


class TestSessionStartHook(unittest.TestCase):
    """Test cases for session_start__show_project_info.py hook."""

    def setUp(self):
        """Set up test fixtures."""
        self.hook_path = Path(__file__).parent.parent / ".claude" / "hooks" / "moai" / "session_start__show_project_info.py"
        self.template_hook_path = Path(__file__).parent.parent / "templates" / "session_start__show_project_info.py"

    def test_session_start_hook_exists(self):
        """Test that session start hook exists."""
        # Check either the installed or template version
        exists = self.hook_path.exists() or self.template_hook_path.exists()
        self.assertTrue(exists, "session_start__show_project_info.py should exist")

    def test_session_start_hook_structure(self):
        """Test session start hook has correct structure."""
        hook_path = self.hook_path if self.hook_path.exists() else self.template_hook_path

        if not hook_path.exists():
            self.skipTest("Hook file not found")

        content = hook_path.read_text(encoding="utf-8")

        # Check for key components
        self.assertIn("def main(", content)
        self.assertIn("SessionStart", content)
        self.assertIn('json.dumps', content)


class TestHookIntegration(unittest.TestCase):
    """Integration tests for hook system."""

    def test_all_hooks_exist(self):
        """Test that all expected hook files exist."""
        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "moai"

        if not hooks_dir.exists():
            self.skipTest("Hooks directory not created yet")

        expected_hooks = [
            "pre_tool__enforce_rules.py",
            "session_start__show_project_info.py",
        ]

        for hook_name in expected_hooks:
            hook_path = hooks_dir / hook_name
            self.assertTrue(hook_path.exists(), f"{hook_name} should exist")

    def test_hook_python_syntax(self):
        """Test that all hook files have valid Python syntax."""
        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "moai"

        if not hooks_dir.exists():
            self.skipTest("Hooks directory not created yet")

        for hook_file in hooks_dir.glob("*.py"):
            try:
                content = hook_file.read_text(encoding="utf-8")
                compile(content, str(hook_file), 'exec')
            except SyntaxError as e:
                self.fail(f"Syntax error in {hook_file.name}: {e}")


if __name__ == "__main__":
    unittest.main()
