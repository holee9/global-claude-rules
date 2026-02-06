#!/usr/bin/env python3
"""
Vector Cache Module

Manages caching of embedding vectors for semantic rule matching.
Provides fast load/save operations with automatic invalidation.

Features:
- NumPy compressed format (.npz) for efficient storage
- JSON metadata for rule tracking
- Automatic cache invalidation based on age
- Incremental update support
- Atomic write operations
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np


# =============================================================================
# Constants
# =============================================================================
CACHE_DIR = Path.home() / ".claude" / "cache" / "semantic_vectors"
CACHE_VALIDITY = timedelta(hours=24)

# Cache file names
EMBEDDINGS_FILE = "embeddings.npz"
METADATA_FILE = "metadata.json"
TIMESTAMP_FILE = "timestamp.txt"
VERSION_FILE = "version.txt"

CACHE_VERSION = "1.0.0"  # Increment to invalidate all caches


def setup_logging() -> logging.Logger:
    """Setup logging for the cache."""
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
    """Check if numpy is available.

    Returns:
        True if dependencies are available, False otherwise
    """
    try:
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False


HAS_NUMPY = _check_dependencies()


# =============================================================================
# Vector Cache Class
# =============================================================================
class VectorCache:
    """Manages caching of embedding vectors.

    This class provides:
    - Saving/loading embeddings in compressed format
    - Metadata tracking for rule IDs
    - Automatic invalidation based on age
    - Version tracking for cache invalidation
    - Atomic write operations
    """

    def __init__(self, cache_dir: Path | None = None) -> None:
        """Initialize the vector cache.

        Args:
            cache_dir: Directory for cache files (default: ~/.claude/cache/semantic_vectors)
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Ensure cache directory exists."""
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            logger.warning(f"Failed to create cache directory: {e}")

    @property
    def embeddings_path(self) -> Path:
        """Get path to embeddings file."""
        return self.cache_dir / EMBEDDINGS_FILE

    @property
    def metadata_path(self) -> Path:
        """Get path to metadata file."""
        return self.cache_dir / METADATA_FILE

    @property
    def timestamp_path(self) -> Path:
        """Get path to timestamp file."""
        return self.cache_dir / TIMESTAMP_FILE

    @property
    def version_path(self) -> Path:
        """Get path to version file."""
        return self.cache_dir / VERSION_FILE

    def is_valid(self) -> bool:
        """Check if cache is valid and can be used.

        Returns:
            True if cache exists and is within validity period
        """
        # Check all required files exist
        if not all(
            p.exists()
            for p in [
                self.embeddings_path,
                self.metadata_path,
                self.timestamp_path,
                self.version_path,
            ]
        ):
            return False

        # Check version matches
        try:
            cached_version = self.version_path.read_text(encoding="utf-8").strip()
            if cached_version != CACHE_VERSION:
                logger.info(
                    f"Cache version mismatch: {cached_version} != {CACHE_VERSION}"
                )
                return False
        except (OSError, UnicodeDecodeError):
            return False

        # Check timestamp is within validity period
        try:
            timestamp_str = self.timestamp_path.read_text(encoding="utf-8").strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now() - timestamp

            if age < CACHE_VALIDITY:
                return True
            else:
                logger.info(f"Cache expired (age: {age})")
                return False

        except (OSError, UnicodeDecodeError, ValueError) as e:
            logger.warning(f"Failed to read cache timestamp: {e}")
            return False

    def save(
        self,
        embeddings: "np.ndarray",
        metadata: dict[str, Any],
    ) -> bool:
        """Save embeddings and metadata to cache.

        Args:
            embeddings: NumPy array of embeddings
            metadata: Metadata dictionary (rule_ids, count, etc.)

        Returns:
            True if save succeeded, False otherwise
        """
        if not HAS_NUMPY:
            logger.warning("NumPy not available, cannot save cache")
            return False

        try:
            import numpy as np

            # Save embeddings to temporary file first (atomic write)
            temp_embeddings = self.embeddings_path.with_suffix(".tmp")
            np.savez_compressed(temp_embeddings, embeddings=embeddings)

            # Save metadata to temporary file
            temp_metadata = self.metadata_path.with_suffix(".tmp")
            temp_metadata.write_text(
                json.dumps(metadata, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # Save timestamp
            temp_timestamp = self.timestamp_path.with_suffix(".tmp")
            temp_timestamp.write_text(datetime.now().isoformat(), encoding="utf-8")

            # Save version
            temp_version = self.version_path.with_suffix(".tmp")
            temp_version.write_text(CACHE_VERSION, encoding="utf-8")

            # Atomic rename
            temp_embeddings.replace(self.embeddings_path)
            temp_metadata.replace(self.metadata_path)
            temp_timestamp.replace(self.timestamp_path)
            temp_version.replace(self.version_path)

            logger.info(f"Cache saved: {len(embeddings)} embeddings")
            return True

        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
            # Clean up temp files
            for temp_path in [
                self.embeddings_path.with_suffix(".tmp"),
                self.metadata_path.with_suffix(".tmp"),
                self.timestamp_path.with_suffix(".tmp"),
                self.version_path.with_suffix(".tmp"),
            ]:
                try:
                    if temp_path.exists():
                        temp_path.unlink()
                except OSError:
                    pass
            return False

    def load(self) -> tuple["np.ndarray | None", dict[str, Any] | None]:
        """Load embeddings and metadata from cache.

        Returns:
            Tuple of (embeddings, metadata), or (None, None) if load failed
        """
        if not HAS_NUMPY:
            logger.warning("NumPy not available, cannot load cache")
            return None, None

        if not self.is_valid():
            return None, None

        try:
            import numpy as np

            # Load embeddings
            data = np.load(self.embeddings_path)
            embeddings = data["embeddings"]

            # Load metadata
            metadata_text = self.metadata_path.read_text(encoding="utf-8")
            metadata = json.loads(metadata_text)

            logger.info(f"Cache loaded: {len(embeddings)} embeddings")
            return embeddings, metadata

        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return None, None

    def invalidate(self) -> bool:
        """Invalidate the cache by deleting all cache files.

        Returns:
            True if invalidation succeeded, False otherwise
        """
        try:
            for file_path in self.cache_dir.glob("*"):
                if file_path.is_file():
                    file_path.unlink()

            logger.info("Cache invalidated")
            return True

        except OSError as e:
            logger.warning(f"Failed to invalidate cache: {e}")
            return False

    def get_age(self) -> timedelta | None:
        """Get the age of the cache.

        Returns:
            Age of the cache, or None if cache doesn't exist
        """
        if not self.timestamp_path.exists():
            return None

        try:
            timestamp_str = self.timestamp_path.read_text(encoding="utf-8").strip()
            timestamp = datetime.fromisoformat(timestamp_str)
            return datetime.now() - timestamp
        except (OSError, UnicodeDecodeError, ValueError):
            return None

    def get_metadata(self) -> dict[str, Any] | None:
        """Get just the metadata without loading embeddings.

        Returns:
            Metadata dictionary, or None if not available
        """
        if not self.metadata_path.exists():
            return None

        try:
            metadata_text = self.metadata_path.read_text(encoding="utf-8")
            return json.loads(metadata_text)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None

    def needs_update(self, current_rule_ids: list[str]) -> bool:
        """Check if cache needs updating based on current rules.

        Args:
            current_rule_ids: List of current rule IDs

        Returns:
            True if cache needs updating, False otherwise
        """
        if not self.is_valid():
            return True

        metadata = self.get_metadata()
        if metadata is None:
            return True

        cached_rule_ids = metadata.get("rule_ids", [])
        return set(current_rule_ids) != set(cached_rule_ids)


# =============================================================================
# Singleton instance
# =============================================================================
_global_cache: VectorCache | None = None


def get_cache() -> VectorCache:
    """Get or create the global cache instance.

    Returns:
        The global VectorCache instance
    """
    global _global_cache

    if _global_cache is None:
        _global_cache = VectorCache()

    return _global_cache


def reset_cache() -> None:
    """Reset the global cache instance."""
    global _global_cache
    _global_cache = None


# =============================================================================
# CLI for testing
# =============================================================================
def main() -> None:
    """CLI entry point for testing the cache."""
    import argparse

    parser = argparse.ArgumentParser(description="Vector Cache CLI")
    parser.add_argument("--status", action="store_true", help="Show cache status")
    parser.add_argument("--invalidate", action="store_true", help="Invalidate cache")
    parser.add_argument("--info", action="store_true", help="Show cache info")

    args = parser.parse_args()

    cache = VectorCache()

    if args.invalidate:
        if cache.invalidate():
            print("Cache invalidated successfully")
        else:
            print("Failed to invalidate cache")

    if args.status:
        if cache.is_valid():
            age = cache.get_age()
            print(f"Cache: VALID (age: {age})")
        else:
            print("Cache: INVALID or MISSING")

    if args.info:
        metadata = cache.get_metadata()
        if metadata:
            print(f"Cache info:")
            print(f"  Rule count: {len(metadata.get('rule_ids', []))}")
            print(f"  Created: {metadata.get('created_at', 'unknown')}")
        else:
            print("No cache info available")


if __name__ == "__main__":
    main()
