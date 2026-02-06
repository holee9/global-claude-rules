#!/usr/bin/env python3
"""
Vector Index Module

FAISS-based vector index for fast semantic similarity search.
Provides efficient nearest neighbor search for rule matching.

Features:
- FAISS IndexFlatIP for cosine similarity (via L2 normalization)
- Batch add operations
- Top-K search
- Index persistence (save/load)
- Graceful fallback when FAISS is unavailable
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np


# =============================================================================
# Constants
# =============================================================================
# Default embedding dimension (all-MiniLM-L6-v2)
DEFAULT_EMBEDDING_DIM = 384


def setup_logging() -> logging.Logger:
    """Setup logging for the index."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
    return logger


logger = setup_logging()


# =============================================================================
# Dependency Check
# =============================================================================
def _check_dependencies() -> bool:
    """Check if faiss and numpy are available.

    Returns:
        True if dependencies are available, False otherwise
    """
    try:
        import faiss  # noqa: F401
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False


HAS_FAISS = _check_dependencies()


# =============================================================================
# Simple Fallback Index (when FAISS is unavailable)
# =============================================================================
class SimpleVectorIndex:
    """Simple NumPy-based fallback index when FAISS is unavailable.

    Uses brute-force cosine similarity search.
    Less efficient but works without FAISS dependency.
    """

    def __init__(self, embedding_dim: int = DEFAULT_EMBEDDING_DIM):
        """Initialize the simple index.

        Args:
            embedding_dim: Dimension of embedding vectors
        """
        self.embedding_dim = embedding_dim
        self.embeddings: list["np.ndarray"] = []
        self.rules: list[dict[str, Any]] = []
        self.rule_id_to_idx: dict[str, int] = {}

    def add(self, embedding: "np.ndarray", rule: dict[str, Any]) -> None:
        """Add a single embedding and rule to the index.

        Args:
            embedding: Normalized embedding vector
            rule: Rule dictionary
        """
        idx = len(self.rules)
        self.embeddings.append(embedding)
        self.rules.append(rule)
        self.rule_id_to_idx[rule["id"]] = idx

    def add_batch(
        self,
        embeddings: "np.ndarray",
        rules: list[dict[str, Any]],
    ) -> None:
        """Add multiple embeddings and rules to the index.

        Args:
            embeddings: Array of embedding vectors (should be normalized)
            rules: List of rule dictionaries
        """
        import numpy as np

        for i, rule in enumerate(rules):
            idx = len(self.rules)
            self.embeddings.append(embeddings[i])
            self.rules.append(rule)
            self.rule_id_to_idx[rule["id"]] = idx

    def search(
        self,
        query_embedding: "np.ndarray",
        k: int = 5,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search for top-K similar rules.

        Args:
            query_embedding: Query embedding vector (should be normalized)
            k: Number of results to return

        Returns:
            List of (rule, score) tuples sorted by score (descending)
        """
        if not self.embeddings:
            return []

        import numpy as np

        # Compute cosine similarity (dot product of normalized vectors)
        embeddings_array = np.array(self.embeddings)
        scores = np.dot(embeddings_array, query_embedding)

        # Get top-K indices
        top_k_indices = np.argsort(scores)[-k:][::-1]

        # Build results
        results = [
            (self.rules[idx], float(scores[idx]))
            for idx in top_k_indices
            if 0 <= idx < len(self.rules)
        ]

        return results

    def clear(self) -> None:
        """Clear all data from the index."""
        self.embeddings.clear()
        self.rules.clear()
        self.rule_id_to_idx.clear()

    @property
    def size(self) -> int:
        """Get the number of rules in the index."""
        return len(self.rules)


# =============================================================================
# FAISS Vector Index
# =============================================================================
class VectorRuleIndex:
    """FAISS-based vector index for fast similarity search.

    This class provides:
    - FAISS IndexFlatIP for inner product (cosine with normalized vectors)
    - Batch add operations
    - Top-K search with similarity scores
    - Index persistence
    - Automatic fallback to simple index when FAISS unavailable
    """

    def __init__(self, embedding_dim: int = DEFAULT_EMBEDDING_DIM) -> None:
        """Initialize the vector index.

        Args:
            embedding_dim: Dimension of embedding vectors
        """
        self.embedding_dim = embedding_dim
        self.rules: list[dict[str, Any]] = []
        self.rule_id_to_idx: dict[str, int] = {}
        self._use_fallback = not HAS_FAISS

        if self._use_fallback:
            logger.warning("FAISS not available, using simple fallback index")
            self._index = SimpleVectorIndex(embedding_dim)
        else:
            self._init_faiss_index()

    def _init_faiss_index(self) -> None:
        """Initialize the FAISS index."""
        try:
            import faiss

            # Use IndexFlatIP (Inner Product) for cosine similarity
            # Vectors should be L2 normalized before adding
            self._index = faiss.IndexFlatIP(self.embedding_dim)
            logger.info(f"FAISS index initialized: {self.embedding_dim} dimensions")
        except Exception as e:
            logger.warning(f"Failed to initialize FAISS: {e}, using fallback")
            self._use_fallback = True
            self._index = SimpleVectorIndex(self.embedding_dim)

    def add_rules(
        self,
        rules: list[dict[str, Any]],
        embeddings: "np.ndarray",
    ) -> bool:
        """Add multiple rules and their embeddings to the index.

        Args:
            rules: List of rule dictionaries
            embeddings: NumPy array of embedding vectors (should be normalized)

        Returns:
            True if add succeeded, False otherwise
        """
        try:
            if self._use_fallback:
                self._index.add_batch(embeddings, rules)
            else:
                import numpy as np

                # Add to FAISS index
                self._index.add(embeddings.astype(np.float32))

                # Track rules
                for i, rule in enumerate(rules):
                    idx = len(self.rules)
                    self.rule_id_to_idx[rule["id"]] = idx
                    self.rules.append(rule)

            return True

        except Exception as e:
            logger.warning(f"Failed to add rules to index: {e}")
            return False

    def add_rule(
        self,
        rule: dict[str, Any],
        embedding: "np.ndarray",
    ) -> bool:
        """Add a single rule and its embedding to the index.

        Args:
            rule: Rule dictionary
            embedding: Embedding vector (should be normalized)

        Returns:
            True if add succeeded, False otherwise
        """
        return self.add_rules([rule], embedding.reshape(1, -1))

    def search(
        self,
        query_embedding: "np.ndarray",
        k: int = 5,
        min_score: float = 0.0,
    ) -> list[tuple[dict[str, Any], float]]:
        """Search for top-K similar rules.

        Args:
            query_embedding: Query embedding vector (should be normalized)
            k: Number of results to return
            min_score: Minimum similarity score (0.0 to 1.0)

        Returns:
            List of (rule, score) tuples sorted by score (descending)
        """
        try:
            if self._use_fallback:
                results = self._index.search(query_embedding, k)
            else:
                import numpy as np

                # Reshape query for FAISS
                query = query_embedding.reshape(1, -1).astype(np.float32)

                # Search
                scores, indices = self._index.search(query, k)

                # Build results
                results = []
                for score, idx in zip(scores[0], indices[0]):
                    if 0 <= idx < len(self.rules):
                        if float(score) >= min_score:
                            results.append((self.rules[idx], float(score)))

            return results

        except Exception as e:
            logger.warning(f"Search failed: {e}")
            return []

    def save(self, path: Path) -> bool:
        """Save the FAISS index to disk.

        Args:
            path: Directory to save the index

        Returns:
            True if save succeeded, False otherwise
        """
        if self._use_fallback:
            logger.warning("Cannot save fallback index")
            return False

        try:
            import faiss

            path.mkdir(parents=True, exist_ok=True)
            index_path = path / "index.faiss"
            faiss.write_index(self._index, str(index_path))

            # Save rules metadata
            metadata_path = path / "rules.json"
            import json

            metadata_path.write_text(
                json.dumps(
                    {
                        "rules": self.rules,
                        "rule_id_to_idx": self.rule_id_to_idx,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            logger.info(f"Index saved to {path}")
            return True

        except Exception as e:
            logger.warning(f"Failed to save index: {e}")
            return False

    def load(self, path: Path) -> bool:
        """Load the FAISS index from disk.

        Args:
            path: Directory containing the index

        Returns:
            True if load succeeded, False otherwise
        """
        if self._use_fallback:
            logger.warning("Cannot load into fallback index")
            return False

        try:
            import faiss
            import json

            index_path = path / "index.faiss"
            metadata_path = path / "rules.json"

            if not index_path.exists() or not metadata_path.exists():
                logger.warning("Index files not found")
                return False

            # Load FAISS index
            self._index = faiss.read_index(str(index_path))

            # Load rules metadata
            metadata_text = metadata_path.read_text(encoding="utf-8")
            metadata = json.loads(metadata_text)

            self.rules = metadata["rules"]
            self.rule_id_to_idx = {
                k: int(v) for k, v in metadata["rule_id_to_idx"].items()
            }

            logger.info(f"Index loaded from {path} ({len(self.rules)} rules)")
            return True

        except Exception as e:
            logger.warning(f"Failed to load index: {e}")
            return False

    def clear(self) -> None:
        """Clear all data from the index."""
        self.rules.clear()
        self.rule_id_to_idx.clear()

        if self._use_fallback:
            self._index.clear()
        else:
            # Reinitialize FAISS index
            self._init_faiss_index()

    @property
    def size(self) -> int:
        """Get the number of rules in the index."""
        return len(self.rules)

    @property
    def is_faiss_available(self) -> bool:
        """Check if FAISS is being used (not fallback)."""
        return not self._use_fallback


# =============================================================================
# CLI for testing
# =============================================================================
def main() -> None:
    """CLI entry point for testing the index."""
    import argparse

    parser = argparse.ArgumentParser(description="Vector Index CLI")
    parser.add_argument("--test", action="store_true", help="Run test search")
    parser.add_argument("--dim", type=int, default=384, help="Embedding dimension")

    args = parser.parse_args()

    if args.test:
        import numpy as np

        index = VectorRuleIndex(embedding_dim=args.dim)

        # Add some test data
        test_rules = [
            {"id": "ERR-001", "title": "File Not Found"},
            {"id": "ERR-002", "title": "Edit Failed"},
            {"id": "ERR-003", "title": "Permission Denied"},
        ]

        test_embeddings = np.random.rand(3, args.dim).astype(np.float32)
        # L2 normalize
        test_embeddings = test_embeddings / np.linalg.norm(
            test_embeddings, axis=1, keepdims=True
        )

        index.add_rules(test_rules, test_embeddings)

        # Test search
        query = np.random.rand(args.dim).astype(np.float32)
        query = query / np.linalg.norm(query)

        results = index.search(query, k=2)

        print(f"Test search results:")
        for rule, score in results:
            print(f"  {rule['id']}: {score:.4f}")

        print(f"\nIndex size: {index.size}")
        print(f"Using FAISS: {index.is_faiss_available}")


if __name__ == "__main__":
    main()
