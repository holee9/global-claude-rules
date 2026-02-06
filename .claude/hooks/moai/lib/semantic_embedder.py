#!/usr/bin/env python3
"""
Semantic Embedder Module

Generates text embeddings using sentence-transformers for semantic similarity.
Supports CPU/GPU acceleration and multilingual models.

Features:
- SentenceTransformer wrapper for embedding generation
- Automatic device detection (CPU/CUDA)
- Batch processing for efficiency
- Model caching to avoid reloads
- Fallback handling for missing dependencies
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import numpy as np


# =============================================================================
# Constants
# =============================================================================
# Default model: fast, English-only, 384 dimensions
DEFAULT_MODEL = "all-MiniLM-L6-v2"

# Alternative models for different use cases
MODEL_OPTIONS = {
    "default": DEFAULT_MODEL,           # Fast, English, 384d, 80MB
    "accurate": "all-mpnet-base-v2",    # Accurate, English, 768d, 420MB
    "multilingual": "paraphrase-multilingual-mpnet-base-v2",  # 100+ languages, 768d, 470MB
}

# Cache directory for models
CACHE_DIR = Path.home() / ".claude" / "cache" / "sentence_transformers"


def setup_logging() -> logging.Logger:
    """Setup logging for the embedder."""
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
    """Check if sentence-transformers is available.

    Returns:
        True if dependencies are available, False otherwise
    """
    try:
        import sentence_transformers  # noqa: F401
        import numpy  # noqa: F401
        return True
    except ImportError:
        return False


HAS_DEPENDENCIES = _check_dependencies()


# =============================================================================
# Semantic Embedder Class
# =============================================================================
class SemanticEmbedder:
    """Generates text embeddings using sentence-transformers.

    This class wraps sentence-transformers to provide:
    - Single and batch text embedding
    - Automatic device detection
    - Model caching
    - Graceful degradation when dependencies are missing
    """

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        device: str | None = None,
        cache_dir: Path | None = None,
    ) -> None:
        """Initialize the semantic embedder.

        Args:
            model_name: Name of the sentence-transformers model to use
            device: Device to use ("cuda", "cpu", or None for auto-detect)
            cache_dir: Directory for caching models
        """
        self.model_name = model_name
        self._cache_dir = cache_dir or CACHE_DIR
        self._device = device
        self._model: Any | None = None
        self._embedding_dim: int | None = None

        # Try to initialize the model
        if HAS_DEPENDENCIES:
            self._initialize_model()
        else:
            logger.warning(
                "sentence-transformers or numpy not available. "
                "Semantic embedding will be disabled."
            )

    def _initialize_model(self) -> None:
        """Initialize the sentence-transformers model."""
        try:
            from sentence_transformers import SentenceTransformer

            # Detect device if not specified
            if self._device is None:
                self._device = self._detect_device()

            # Create cache directory
            self._cache_dir.mkdir(parents=True, exist_ok=True)

            # Load model
            logger.info(f"Loading sentence-transformers model: {self.model_name}")
            self._model = SentenceTransformer(
                self.model_name,
                device=self._device,
                cache_folder=str(self._cache_dir),
            )

            # Get embedding dimension
            self._embedding_dim = self._model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded with embedding dimension: {self._embedding_dim}")

        except Exception as e:
            logger.warning(f"Failed to load sentence-transformers model: {e}")
            self._model = None
            self._embedding_dim = None

    def _detect_device(self) -> str:
        """Detect the best available device (CUDA or CPU).

        Returns:
            "cuda" if available, otherwise "cpu"
        """
        try:
            import torch

            if torch.cuda.is_available():
                logger.info("CUDA detected, using GPU for embeddings")
                return "cuda"
        except ImportError:
            pass

        logger.info("Using CPU for embeddings")
        return "cpu"

    @property
    def is_available(self) -> bool:
        """Check if the embedder is available for use.

        Returns:
            True if dependencies are available and model is loaded
        """
        return HAS_DEPENDENCIES and self._model is not None

    @property
    def embedding_dim(self) -> int:
        """Get the embedding dimension.

        Returns:
            The embedding dimension, or 384 as default if not available

        Raises:
            RuntimeError: If embedder is not available
        """
        if self._embedding_dim is None:
            # Return default dimension for common models
            if "mpnet" in self.model_name.lower():
                return 768
            return 384
        return self._embedding_dim

    def encode(
        self,
        texts: list[str] | str,
        batch_size: int = 32,
        show_progress: bool = False,
    ) -> "np.ndarray | None":
        """Encode text(s) into embedding vectors.

        Args:
            texts: Single text string or list of texts to encode
            batch_size: Batch size for encoding (for multiple texts)
            show_progress: Whether to show progress bar

        Returns:
            NumPy array of embeddings, or None if encoding failed
        """
        if not self.is_available:
            logger.warning("Embedder not available, returning None")
            return None

        try:
            import numpy as np

            # Normalize input to list
            single_input = isinstance(texts, str)
            texts_list = [texts] if single_input else texts

            # Encode
            embeddings = self._model.encode(
                texts_list,
                batch_size=batch_size,
                show_progress_bar=show_progress,
                convert_to_numpy=True,
                normalize_embeddings=True,  # L2 normalize for cosine similarity
            )

            # Return single vector if input was single text
            if single_input:
                return embeddings[0]

            return embeddings

        except Exception as e:
            logger.warning(f"Failed to encode text: {e}")
            return None

    def encode_rule(self, rule: dict[str, Any]) -> "np.ndarray | None":
        """Encode a single rule dictionary into an embedding vector.

        Args:
            rule: Rule dictionary with keys: id, title, problem, solution, prevention

        Returns:
            Embedding vector, or None if encoding failed
        """
        text = self._compose_rule_text(rule)
        return self.encode(text)

    def _compose_rule_text(self, rule: dict[str, Any]) -> str:
        """Compose rule text from rule dictionary.

        Args:
            rule: Rule dictionary

        Returns:
            Composed text string for embedding
        """
        parts = []

        # Add ID and title (always present)
        if "id" in rule:
            parts.append(f"{rule['id']}")
        if "title" in rule:
            parts.append(rule["title"])

        # Add problem description
        if rule.get("problem"):
            parts.append(rule["problem"])

        # Add solution (most important for matching)
        if rule.get("solution"):
            parts.append(rule["solution"])

        # Add prevention if available
        if rule.get("prevention"):
            parts.append(rule["prevention"])

        return ". ".join(parts)

    def compose_query(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
    ) -> str:
        """Compose a query text from tool name and input.

        Args:
            tool_name: Name of the tool being called
            tool_input: Input parameters for the tool

        Returns:
            Composed query text for embedding
        """
        parts = [f"Tool: {tool_name}"]

        # Add file path if present
        if "file_path" in tool_input:
            file_path = str(tool_input["file_path"])
            parts.append(f"File: {file_path}")

            # Add extension separately for better matching
            if "." in file_path:
                ext = file_path.rsplit(".", 1)[-1]
                parts.append(f"Extension: {ext}")

        # Add command if present
        if "command" in tool_input:
            parts.append(f"Command: {tool_input['command']}")

        # Add subagent type if present
        if "subagent_type" in tool_input:
            parts.append(f"Agent: {tool_input['subagent_type']}")

        # Add pattern if present (for Grep)
        if "pattern" in tool_input:
            parts.append(f"Pattern: {tool_input['pattern']}")

        return ". ".join(parts)


# =============================================================================
# Singleton instance for caching
# =============================================================================
_global_embedder: SemanticEmbedder | None = None


def get_embedder(model_name: str = DEFAULT_MODEL) -> SemanticEmbedder:
    """Get or create the global embedder instance.

    Args:
        model_name: Name of the model to use

    Returns:
        The global SemanticEmbedder instance
    """
    global _global_embedder

    if _global_embedder is None or _global_embedder.model_name != model_name:
        _global_embedder = SemanticEmbedder(model_name=model_name)

    return _global_embedder


def reset_embedder() -> None:
    """Reset the global embedder instance."""
    global _global_embedder
    _global_embedder = None


# =============================================================================
# CLI for testing
# =============================================================================
def main() -> None:
    """CLI entry point for testing the embedder."""
    import argparse

    parser = argparse.ArgumentParser(description="Semantic Embedder CLI")
    parser.add_argument("--text", help="Text to encode")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model name")
    parser.add_argument("--list-models", action="store_true", help="List available models")

    args = parser.parse_args()

    if args.list_models:
        print("Available models:")
        for name, model in MODEL_OPTIONS.items():
            print(f"  {name}: {model}")
        return

    if args.text:
        embedder = SemanticEmbedder(model_name=args.model)
        if embedder.is_available:
            embedding = embedder.encode(args.text)
            if embedding is not None:
                print(f"Embedding shape: {embedding.shape}")
                print(f"First 10 values: {embedding[:10]}")
        else:
            print("Embedder not available (missing dependencies)")
    else:
        print("No text provided. Use --text to encode text.")


if __name__ == "__main__":
    main()
