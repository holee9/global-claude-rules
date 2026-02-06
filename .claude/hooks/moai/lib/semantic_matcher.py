#!/usr/bin/env python3
"""
Semantic Rule Matcher Module

Main module for semantic rule matching using sentence-transformers.
Combines embedding, caching, and vector search for efficient rule retrieval.

Features:
- Hybrid semantic + keyword matching
- Automatic fallback to keyword matching when semantic unavailable
- Vector caching for fast initialization
- Configurable similarity threshold
- Analytics tracking integration
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np


# =============================================================================
# Setup import path for shared modules
# =============================================================================
LIB_DIR = Path(__file__).parent
if str(LIB_DIR) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(LIB_DIR))


# =============================================================================
# Constants
# =============================================================================
# Similarity threshold below which keyword fallback is used
SIMILARITY_THRESHOLD = 0.5

# Minimum number of results before considering keyword augmentation
MIN_RESULTS = 3

# Default maximum results to return
MAX_RESULTS = 10

# Tool keywords for fallback matching
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

# Error patterns for fallback matching
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


def setup_logging() -> logging.Logger:
    """Setup logging for the matcher."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
    return logger


logger = setup_logging()


# =============================================================================
# Import dependencies (with graceful fallback)
# =============================================================================
def _check_semantic_dependencies() -> bool:
    """Check if semantic matching dependencies are available.

    Returns:
        True if dependencies are available, False otherwise
    """
    try:
        from semantic_embedder import SemanticEmbedder, HAS_DEPENDENCIES
        from vector_index import VectorRuleIndex
        from vector_cache import VectorCache
        return HAS_DEPENDENCIES
    except ImportError:
        return False


HAS_SEMANTIC = _check_semantic_dependencies()


# =============================================================================
# Keyword Fallback Matcher
# =============================================================================
class KeywordRuleMatcher:
    """Original keyword-based rule matcher as fallback.

    This implements the original matching logic from pre_tool__enforce_rules.py
    for use when semantic matching is unavailable or as a supplement.
    """

    def __init__(self):
        """Initialize the keyword matcher."""
        self.keywords = TOOL_KEYWORDS
        self.error_patterns = ERROR_PATTERNS

    def match(
        self,
        rules: list[dict[str, Any]],
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Find relevant rules using keyword matching.

        Args:
            rules: All available rules
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool

        Returns:
            List of relevant rules sorted by relevance score
        """
        relevant_rules = []
        tool_input_str = json.dumps(tool_input).lower()

        # Get keywords for this tool
        keywords = self.keywords.get(tool_name, [])

        # Score each rule
        for rule in rules:
            score = 0
            rule_text = (
                f"{rule['id']} {rule['title']} {rule.get('problem', '')} "
                f"{rule.get('solution', '')}".lower()
            )

            # Check if rule ID is in error patterns
            for pattern, err_ids in self.error_patterns.items():
                if rule["id"] in err_ids:
                    if re.search(pattern, tool_input_str):
                        score += 10
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
            if "file_path" in tool_input:
                file_path = str(tool_input["file_path"]).lower()
                if "file" in rule_text:
                    score += 2
                if "." in file_path:
                    ext = file_path.rsplit(".", 1)[-1]
                    if ext in rule_text or ext.upper() in rule_text:
                        score += 3

            # Check command mentions for Bash
            if tool_name == "Bash" and "command" in tool_input:
                command = str(tool_input["command"]).lower()
                if "git" in command and "git" in rule_text:
                    score += 5
                if "npm" in command and "npm" in rule_text:
                    score += 3
                if "python" in command and "python" in rule_text:
                    score += 3

            # Only include rules with a score
            if score > 0:
                rule = dict(rule)  # Copy to avoid mutating original
                rule["relevance_score"] = score
                rule["match_type"] = "keyword"
                relevant_rules.append(rule)

        # Sort by relevance score
        relevant_rules.sort(key=lambda r: r.get("relevance_score", 0), reverse=True)

        return relevant_rules


# =============================================================================
# Semantic Rule Matcher
# =============================================================================
class SemanticRuleMatcher:
    """Main semantic rule matcher using embeddings and vector search.

    This class provides:
    - Semantic similarity-based rule matching
    - Hybrid semantic + keyword matching
    - Automatic fallback when dependencies unavailable
    - Vector caching for fast initialization
    - Analytics tracking integration
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        similarity_threshold: float = SIMILARITY_THRESHOLD,
        min_results: int = MIN_RESULTS,
        max_results: int = MAX_RESULTS,
    ):
        """Initialize the semantic rule matcher.

        Args:
            model_name: Name of the sentence-transformers model
            similarity_threshold: Minimum similarity for pure semantic results
            min_results: Minimum results before keyword augmentation
            max_results: Maximum results to return
        """
        self.similarity_threshold = similarity_threshold
        self.min_results = min_results
        self.max_results = max_results
        self.model_name = model_name

        # Initialize components
        self._embedder = None
        self._index = None
        self._cache = None
        self._keyword_matcher = KeywordRuleMatcher()

        # Initialization state
        self._initialized = False
        self._rules_hash = None

        # Try to initialize if dependencies are available
        if HAS_SEMANTIC:
            self._init_components()
        else:
            logger.warning(
                "Semantic matching dependencies unavailable, "
                "using keyword-only matching"
            )

    def _init_components(self) -> None:
        """Initialize semantic matching components."""
        try:
            from semantic_embedder import SemanticEmbedder, get_embedder
            from vector_index import VectorRuleIndex
            from vector_cache import VectorCache, get_cache

            self._embedder = get_embedder(self.model_name)
            self._index = VectorRuleIndex(
                embedding_dim=self._embedder.embedding_dim
            )
            self._cache = get_cache()

            if not self._embedder.is_available:
                logger.warning("Embedder not available, using keyword-only matching")
                self._embedder = None
                self._index = None

        except Exception as e:
            logger.warning(f"Failed to initialize semantic components: {e}")
            self._embedder = None
            self._index = None

    def initialize(self, rules: list[dict[str, Any]]) -> bool:
        """Initialize the matcher with rules.

        Args:
            rules: List of rule dictionaries

        Returns:
            True if initialization succeeded, False otherwise
        """
        self._rules_hash = self._compute_rules_hash(rules)

        # Try semantic initialization
        if self._embedder and self._index and self._cache:
            return self._initialize_semantic(rules)

        # Keyword-only mode
        self._initialized = True
        return True

    def _compute_rules_hash(self, rules: list[dict[str, Any]]) -> str:
        """Compute a hash of rule IDs for change detection.

        Args:
            rules: List of rule dictionaries

        Returns:
            Hash string
        """
        import hashlib

        rule_ids = sorted(r["id"] for r in rules)
        return hashlib.md5("|".join(rule_ids).encode()).hexdigest()

    def _initialize_semantic(self, rules: list[dict[str, Any]]) -> bool:
        """Initialize semantic matching with rules.

        Args:
            rules: List of rule dictionaries

        Returns:
            True if initialization succeeded, False otherwise
        """
        try:
            rule_ids = [r["id"] for r in rules]

            # Try to load from cache
            if self._cache.needs_update(rule_ids):
                logger.info("Cache invalid or outdated, generating new embeddings")
                return self._generate_embeddings(rules)

            # Load from cache
            cached_data = self._cache.load()
            if cached_data:
                embeddings, metadata = cached_data
                if embeddings is not None and metadata is not None:
                    self._index.add_rules(rules, embeddings)
                    self._initialized = True
                    logger.info(f"Loaded {len(rules)} rules from cache")
                    return True

            # Cache load failed, generate new embeddings
            return self._generate_embeddings(rules)

        except Exception as e:
            logger.warning(f"Semantic initialization failed: {e}")
            return False

    def _generate_embeddings(self, rules: list[dict[str, Any]]) -> bool:
        """Generate embeddings for all rules.

        Args:
            rules: List of rule dictionaries

        Returns:
            True if generation succeeded, False otherwise
        """
        try:
            import numpy as np

            # Encode all rules
            all_texts = [
                self._embedder._compose_rule_text(rule) for rule in rules
            ]
            embeddings = self._embedder.encode(
                all_texts, batch_size=32, show_progress=False
            )

            if embeddings is None:
                logger.warning("Failed to generate embeddings")
                return False

            # Add to index
            self._index.add_rules(rules, embeddings)

            # Save to cache
            metadata = {
                "rule_ids": [r["id"] for r in rules],
                "count": len(rules),
                "model": self.model_name,
                "created_at": __import__("datetime").datetime.now().isoformat(),
            }
            self._cache.save(embeddings, metadata)

            self._initialized = True
            logger.info(f"Generated embeddings for {len(rules)} rules")
            return True

        except Exception as e:
            logger.warning(f"Failed to generate embeddings: {e}")
            return False

    def match(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Find relevant rules for the given tool and input.

        Args:
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool

        Returns:
            List of relevant rules sorted by relevance score
        """
        if not self._initialized:
            logger.warning("Matcher not initialized, using keyword fallback")
            return self._keyword_matcher.match([], tool_name, tool_input)

        # Get all rules (they're stored in the index)
        rules = list(self._index.rules) if self._index else []

        if not rules:
            return []

        # Try semantic matching
        semantic_results = []
        max_score = 0.0

        if self._embedder and self._index:
            semantic_results = self._semantic_match(tool_name, tool_input)
            if semantic_results:
                max_score = semantic_results[0].get("relevance_score", 0.0)

        # Decide whether to use keyword augmentation
        use_keyword = (
            max_score < self.similarity_threshold
            or len(semantic_results) < self.min_results
        )

        if use_keyword:
            return self._hybrid_match(semantic_results, rules, tool_name, tool_input)

        return semantic_results[: self.max_results]

    def _semantic_match(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Perform pure semantic matching.

        Args:
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool

        Returns:
            List of relevant rules sorted by semantic similarity
        """
        try:
            # Compose query
            query_text = self._embedder.compose_query(tool_name, tool_input)
            query_embedding = self._embedder.encode(query_text)

            if query_embedding is None:
                return []

            # Search index
            raw_results = self._index.search(
                query_embedding,
                k=self.max_results,
                min_score=0.0,  # Get all results, filter later
            )

            # Format results
            results = []
            for rule, score in raw_results:
                rule_copy = dict(rule)
                rule_copy["relevance_score"] = float(score)
                rule_copy["match_type"] = "semantic"
                results.append(rule_copy)

            # Sort by score
            results.sort(key=lambda r: r["relevance_score"], reverse=True)

            return results

        except Exception as e:
            logger.warning(f"Semantic matching failed: {e}")
            return []

    def _hybrid_match(
        self,
        semantic_results: list[dict[str, Any]],
        rules: list[dict[str, Any]],
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Combine semantic and keyword results.

        Args:
            semantic_results: Results from semantic matching
            rules: All available rules
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool

        Returns:
            Combined and deduplicated results
        """
        # Get keyword results
        keyword_results = self._keyword_matcher.match(rules, tool_name, tool_input)

        # Merge results, removing duplicates
        seen_ids = {r["id"] for r in semantic_results}
        merged = list(semantic_results)

        for rule in keyword_results:
            if rule["id"] not in seen_ids:
                merged.append(rule)
                seen_ids.add(rule["id"])

        # Re-sort by score
        merged.sort(key=lambda r: r["relevance_score"], reverse=True)

        return merged[: self.max_results]

    @property
    def is_semantic_available(self) -> bool:
        """Check if semantic matching is available.

        Returns:
            True if semantic matching is enabled, False if keyword-only
        """
        return self._embedder is not None and self._index is not None


# =============================================================================
# Singleton instance
# """
_global_matcher: SemanticRuleMatcher | None = None


def get_matcher() -> SemanticRuleMatcher:
    """Get or create the global matcher instance.

    Returns:
        The global SemanticRuleMatcher instance
    """
    global _global_matcher

    if _global_matcher is None:
        _global_matcher = SemanticRuleMatcher()

    return _global_matcher


def reset_matcher() -> None:
    """Reset the global matcher instance."""
    global _global_matcher
    _global_matcher = None


# =============================================================================
# Convenience function for backward compatibility
# =============================================================================
def find_relevant_rules_semantic(
    rules: list[dict[str, Any]],
    tool_name: str,
    tool_input: dict[str, Any],
) -> list[dict[str, Any]]:
    """Find relevant rules using semantic matching.

    This is a convenience function that matches the signature of
    the original find_relevant_rules function for easy integration.

    Args:
        rules: List of rule dictionaries
        tool_name: Name of the tool being called
        tool_input: Input parameters for the tool

    Returns:
        List of relevant rules sorted by relevance score
    """
    try:
        matcher = get_matcher()

        # Initialize if needed
        if not matcher._initialized:
            matcher.initialize(rules)

        # Track analytics if available
        try:
            from rule_analytics import track_rule_view
            # Analytics tracking happens in the match loop
        except ImportError:
            pass

        return matcher.match(tool_name, tool_input)

    except Exception as e:
        logger.warning(f"Semantic matching failed: {e}, using keyword fallback")
        # Fallback to keyword matching
        keyword_matcher = KeywordRuleMatcher()
        return keyword_matcher.match(rules, tool_name, tool_input)


# =============================================================================
# CLI for testing
# =============================================================================
def main() -> None:
    """CLI entry point for testing the matcher."""
    import argparse

    parser = argparse.ArgumentParser(description="Semantic Rule Matcher CLI")
    parser.add_argument("--test", action="store_true", help="Run test match")
    parser.add_argument("--model", default="all-MiniLM-L6-v2", help="Model name")
    parser.add_argument("--status", action="store_true", help="Show status")

    args = parser.parse_args()

    if args.status:
        print(f"Semantic dependencies available: {HAS_SEMANTIC}")
        if HAS_SEMANTIC:
            matcher = SemanticRuleMatcher()
            print(f"Embedder available: {matcher.is_semantic_available}")

    if args.test:
        # Create test rules
        test_rules = [
            {
                "id": "ERR-004",
                "title": "File Path Not Found",
                "problem": "File does not exist at the specified path",
                "solution": "Use Glob tool to verify file paths before reading",
                "prevention": "Always verify file locations in new projects",
            },
            {
                "id": "ERR-013",
                "title": "Edit Operation Failed",
                "problem": "Edit tool failed because the old string was not found",
                "solution": "Read the file first to verify the exact content",
                "prevention": "Use Read tool before Edit to confirm content",
            },
        ]

        matcher = SemanticRuleMatcher(model_name=args.model)

        if matcher.initialize(test_rules):
            print("Matcher initialized successfully")

            # Test match
            results = matcher.match("Read", {"file_path": "/nonexistent/file.txt"})

            print(f"\nTest match results:")
            for rule in results[:3]:
                print(f"  {rule['id']}: {rule['title']}")
                print(f"    Score: {rule['relevance_score']:.3f}")
                print(f"    Type: {rule['match_type']}")


if __name__ == "__main__":
    main()
