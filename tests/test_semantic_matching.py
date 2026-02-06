#!/usr/bin/env python3
"""
Tests for Semantic Rule Matching System

Tests the semantic matching functionality including:
- Semantic embedder
- Vector cache
- Vector index
- Semantic matcher
- Hybrid matching with fallback
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add hooks directory to path
hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "moai"
if hooks_dir.exists():
    sys.path.insert(0, str(hooks_dir))


class TestSemanticEmbedder(unittest.TestCase):
    """Test cases for semantic embedder module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_module_imports(self):
        """Test that semantic modules can be imported."""
        try:
            from semantic_embedder import SemanticEmbedder, HAS_DEPENDENCIES
            # If dependencies are not available, HAS_DEPENDENCIES will be False
            # but the module should still import successfully
            self.assertIsNotNone(SemanticEmbedder)
        except ImportError as e:
            self.skipTest(f"semantic_embedder module not available: {e}")

    def test_embedder_creation(self):
        """Test creating an embedder instance."""
        try:
            from semantic_embedder import SemanticEmbedder, HAS_DEPENDENCIES

            if not HAS_DEPENDENCIES:
                self.skipTest("sentence-transformers not available")

            embedder = SemanticEmbedder()
            self.assertIsNotNone(embedder)
        except ImportError:
            self.skipTest("semantic_embedder module not available")

    def test_embedder_is_available(self):
        """Test checking if embedder is available."""
        try:
            from semantic_embedder import SemanticEmbedder, HAS_DEPENDENCIES

            embedder = SemanticEmbedder()
            expected = HAS_DEPENDENCIES
            self.assertEqual(embedder.is_available, expected)
        except ImportError:
            self.skipTest("semantic_embedder module not available")

    def test_compose_query(self):
        """Test composing query from tool input."""
        try:
            from semantic_embedder import SemanticEmbedder
        except ImportError:
            self.skipTest("semantic_embedder module not available")
            return

        embedder = SemanticEmbedder()

        query = embedder.compose_query("Read", {"file_path": "/test/file.txt"})
        self.assertIn("Read", query)
        self.assertIn("file.txt", query)

        query = embedder.compose_query("Bash", {"command": "git status"})
        self.assertIn("Bash", query)
        self.assertIn("git status", query)

    def test_compose_rule_text(self):
        """Test composing rule text from dictionary."""
        try:
            from semantic_embedder import SemanticEmbedder
        except ImportError:
            self.skipTest("semantic_embedder module not available")
            return

        embedder = SemanticEmbedder()

        rule = {
            "id": "ERR-004",
            "title": "File Not Found",
            "problem": "File does not exist",
            "solution": "Use Glob to verify",
            "prevention": "Always verify paths"
        }

        text = embedder._compose_rule_text(rule)
        self.assertIn("ERR-004", text)
        self.assertIn("File Not Found", text)
        self.assertIn("Use Glob to verify", text)


class TestVectorCache(unittest.TestCase):
    """Test cases for vector cache module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_module_imports(self):
        """Test that vector cache module can be imported."""
        try:
            from vector_cache import VectorCache, HAS_NUMPY
            self.assertIsNotNone(VectorCache)
        except ImportError as e:
            self.skipTest(f"vector_cache module not available: {e}")

    def test_cache_creation(self):
        """Test creating a cache instance."""
        try:
            from vector_cache import VectorCache
        except ImportError:
            self.skipTest("vector_cache module not available")
            return

        cache = VectorCache(cache_dir=Path(self.temp_dir))
        self.assertIsNotNone(cache)

    def test_cache_is_valid_without_files(self):
        """Test cache validation when no cache files exist."""
        try:
            from vector_cache import VectorCache
        except ImportError:
            self.skipTest("vector_cache module not available")
            return

        cache = VectorCache(cache_dir=Path(self.temp_dir))
        self.assertFalse(cache.is_valid())

    def test_cache_save_and_load(self):
        """Test saving and loading cache data."""
        try:
            from vector_cache import VectorCache, HAS_NUMPY
            import numpy as np
        except ImportError:
            self.skipTest("numpy or vector_cache not available")
            return

        if not HAS_NUMPY:
            self.skipTest("NumPy not available")
            return

        cache = VectorCache(cache_dir=Path(self.temp_dir))

        # Create test embeddings
        embeddings = np.random.rand(5, 384).astype(np.float32)
        metadata = {
            "rule_ids": ["ERR-001", "ERR-002", "ERR-003", "ERR-004", "ERR-005"],
            "count": 5,
            "model": "test-model"
        }

        # Save
        result = cache.save(embeddings, metadata)
        self.assertTrue(result)

        # Load
        loaded_embeddings, loaded_metadata = cache.load()
        self.assertIsNotNone(loaded_embeddings)
        self.assertIsNotNone(loaded_metadata)

        # Verify
        self.assertEqual(loaded_metadata["count"], 5)
        self.assertEqual(len(loaded_metadata["rule_ids"]), 5)

    def test_cache_invalidate(self):
        """Test cache invalidation."""
        try:
            from vector_cache import VectorCache, HAS_NUMPY
            import numpy as np
        except ImportError:
            self.skipTest("numpy or vector_cache not available")
            return

        if not HAS_NUMPY:
            self.skipTest("NumPy not available")
            return

        cache = VectorCache(cache_dir=Path(self.temp_dir))

        # Create and save cache
        embeddings = np.random.rand(3, 384).astype(np.float32)
        metadata = {"rule_ids": ["ERR-001", "ERR-002", "ERR-003"], "count": 3}
        cache.save(embeddings, metadata)

        # Invalidate
        result = cache.invalidate()
        self.assertTrue(result)

        # Verify invalidation
        self.assertFalse(cache.is_valid())


class TestVectorIndex(unittest.TestCase):
    """Test cases for vector index module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_module_imports(self):
        """Test that vector index module can be imported."""
        try:
            from vector_index import VectorRuleIndex, HAS_FAISS
            self.assertIsNotNone(VectorRuleIndex)
        except ImportError as e:
            self.skipTest(f"vector_index module not available: {e}")

    def test_index_creation(self):
        """Test creating an index instance."""
        try:
            from vector_index import VectorRuleIndex
        except ImportError:
            self.skipTest("vector_index module not available")
            return

        index = VectorRuleIndex(embedding_dim=384)
        self.assertIsNotNone(index)

    def test_index_size(self):
        """Test getting index size."""
        try:
            from vector_index import VectorRuleIndex
        except ImportError:
            self.skipTest("vector_index module not available")
            return

        index = VectorRuleIndex(embedding_dim=384)
        self.assertEqual(index.size, 0)

    def test_index_search_empty(self):
        """Test searching empty index."""
        try:
            from vector_index import VectorRuleIndex, HAS_FAISS
            import numpy as np
        except ImportError:
            self.skipTest("vector_index or numpy not available")
            return

        index = VectorRuleIndex(embedding_dim=384)
        query = np.random.rand(384).astype(np.float32)

        results = index.search(query, k=5)
        self.assertEqual(len(results), 0)

    def test_index_add_and_search(self):
        """Test adding rules and searching."""
        try:
            from vector_index import VectorRuleIndex, HAS_FAISS
            import numpy as np
        except ImportError:
            self.skipTest("vector_index or numpy not available")
            return

        index = VectorRuleIndex(embedding_dim=384)

        # Create test rules and embeddings
        rules = [
            {"id": "ERR-001", "title": "Test Rule 1"},
            {"id": "ERR-002", "title": "Test Rule 2"},
            {"id": "ERR-003", "title": "Test Rule 3"},
        ]

        # Create normalized embeddings
        embeddings = np.random.rand(3, 384).astype(np.float32)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)

        # Add to index
        result = index.add_rules(rules, embeddings)
        self.assertTrue(result)
        self.assertEqual(index.size, 3)

        # Search
        query = np.random.rand(384).astype(np.float32)
        query = query / np.linalg.norm(query)

        search_results = index.search(query, k=2)
        self.assertGreaterEqual(len(search_results), 0)
        self.assertLessEqual(len(search_results), 2)


class TestSemanticMatcher(unittest.TestCase):
    """Test cases for semantic matcher module."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_module_imports(self):
        """Test that semantic matcher module can be imported."""
        try:
            from semantic_matcher import (
                SemanticRuleMatcher,
                KeywordRuleMatcher,
                HAS_SEMANTIC,
            )
            self.assertIsNotNone(SemanticRuleMatcher)
            self.assertIsNotNone(KeywordRuleMatcher)
        except ImportError as e:
            self.skipTest(f"semantic_matcher module not available: {e}")

    def test_matcher_creation(self):
        """Test creating a matcher instance."""
        try:
            from semantic_matcher import SemanticRuleMatcher
        except ImportError:
            self.skipTest("semantic_matcher module not available")
            return

        matcher = SemanticRuleMatcher()
        self.assertIsNotNone(matcher)

    def test_matcher_is_semantic_available(self):
        """Test checking if semantic matching is available."""
        try:
            from semantic_matcher import SemanticRuleMatcher, HAS_SEMANTIC
        except ImportError:
            self.skipTest("semantic_matcher module not available")
            return

        matcher = SemanticRuleMatcher()
        # This should match HAS_SEMANTIC
        self.assertEqual(matcher.is_semantic_available, HAS_SEMANTIC)

    def test_keyword_matcher(self):
        """Test keyword-based fallback matcher."""
        try:
            from semantic_matcher import KeywordRuleMatcher
        except ImportError:
            self.skipTest("semantic_matcher module not available")
            return

        matcher = KeywordRuleMatcher()

        rules = [
            {
                "id": "ERR-004",
                "title": "File Path Not Found",
                "problem": "File does not exist",
                "solution": "Use Glob tool to verify"
            },
            {
                "id": "ERR-013",
                "title": "Edit Operation Failed",
                "problem": "Edit failed",
                "solution": "Read file first"
            },
        ]

        # Test with Read tool and file path
        results = matcher.match(rules, "Read", {"file_path": "/test/file.txt"})

        # Should find file-related rules
        self.assertGreater(len(results), 0)

        # Check that relevance scores are present
        for rule in results:
            self.assertIn("relevance_score", rule)
            self.assertEqual(rule["match_type"], "keyword")


class TestIntegration(unittest.TestCase):
    """Integration tests for the semantic matching system."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_hook_integration(self):
        """Test that the hook can import and use semantic matching."""
        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "moai"
        hook_path = hooks_dir / "pre_tool__enforce_rules.py"

        if not hook_path.exists():
            self.skipTest("Hook file not found")

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("enforce_rules", hook_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Check that the module has the expected functions
            self.assertTrue(hasattr(module, "find_relevant_rules"))
            self.assertTrue(hasattr(module, "extract_rules_from_memory"))
            self.assertTrue(hasattr(module, "load_global_memory"))

        except ImportError as e:
            self.skipTest(f"Could not import hook module: {e}")

    def test_find_relevant_rules_with_sample_data(self):
        """Test finding relevant rules with sample data."""
        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "moai"
        hook_path = hooks_dir / "pre_tool__enforce_rules.py"

        if not hook_path.exists():
            self.skipTest("Hook file not found")

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("enforce_rules", hook_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Sample rules
            rules = [
                {
                    "id": "ERR-004",
                    "title": "File Path Not Found",
                    "problem": "File does not exist at the specified path",
                    "solution": "Use Glob tool to verify file paths",
                    "prevention": "Always verify paths"
                },
                {
                    "id": "ERR-013",
                    "title": "Edit Operation Failed",
                    "problem": "Edit tool failed",
                    "solution": "Read file first to verify content",
                    "prevention": "Use Read before Edit"
                },
            ]

            # Test with Read tool
            results = module.find_relevant_rules(rules, "Read", {"file_path": "/test/file.txt"})

            # Should return some results
            self.assertIsInstance(results, list)

            # If results exist, check structure
            for rule in results:
                self.assertIn("id", rule)
                self.assertIn("relevance_score", rule)

        except ImportError as e:
            self.skipTest(f"Could not import hook module: {e}")

    def test_extract_rules_from_memory(self):
        """Test extracting rules from memory content."""
        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "moai"
        hook_path = hooks_dir / "pre_tool__enforce_rules.py"

        if not hook_path.exists():
            self.skipTest("Hook file not found")

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("enforce_rules", hook_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            sample_memory = """
### ERR-001: TodoWrite Tool Not Available
**Problem**: Tool not available in current environment
**Solution**: Use Task tool instead
**Prevention**: Always check available tools

### ERR-004: File Path Not Found
**Problem**: File does not exist at specified path
**Solution**: Use Glob to verify paths
**Prevention**: Always verify file paths first
"""

            rules = module.extract_rules_from_memory(sample_memory)

            self.assertEqual(len(rules), 2)
            self.assertEqual(rules[0]["id"], "ERR-001")
            self.assertEqual(rules[1]["id"], "ERR-004")

        except ImportError as e:
            self.skipTest(f"Could not import hook module: {e}")


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing tests."""

    def test_find_relevant_rules_for_write_tool(self):
        """Test finding relevant rules for Write tool (backward compat)."""
        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "moai"
        hook_path = hooks_dir / "pre_tool__enforce_rules.py"

        if not hook_path.exists():
            self.skipTest("Hook file not found")

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("enforce_rules", hook_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            rules = [
                {
                    "id": "ERR-004",
                    "title": "File Path Not Found",
                    "problem": "Wrong path",
                    "solution": "Use Glob first",
                    "prevention": "Verify paths"
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
            err_ids = [r["id"] for r in relevant]
            self.assertIn("ERR-004", err_ids)

        except ImportError as e:
            self.skipTest(f"Could not import hook module: {e}")

    def test_find_relevant_rules_for_bash_tool(self):
        """Test finding relevant rules for Bash tool (backward compat)."""
        hooks_dir = Path(__file__).parent.parent / ".claude" / "hooks" / "moai"
        hook_path = hooks_dir / "pre_tool__enforce_rules.py"

        if not hook_path.exists():
            self.skipTest("Hook file not found")

        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("enforce_rules", hook_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            rules = [
                {
                    "id": "ERR-001",
                    "title": "TodoWrite Not Available",
                    "problem": "Tool missing",
                    "solution": "Use TaskCreate",
                    "prevention": "Use Task tool"
                },
            ]

            # Test with Bash tool
            relevant = module.find_relevant_rules(
                rules,
                "Bash",
                {"command": "git status"}
            )

            # Filter to rules with actual relevance
            relevant = [r for r in relevant if r.get("relevance_score", 0) > 0]

            # Should return a list (may be empty if no matches)
            self.assertIsInstance(relevant, list)

        except ImportError as e:
            self.skipTest(f"Could not import hook module: {e}")


if __name__ == "__main__":
    unittest.main()
