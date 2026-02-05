#!/usr/bin/env python3
"""
Shared utilities for Global Claude Rules.
"""

from .errors import (
    GlobalRulesError,
    FileOperationError,
    GitOperationError,
    ValidationError,
    ConfigurationError,
    NetworkError,
)

__all__ = [
    "GlobalRulesError",
    "FileOperationError",
    "GitOperationError",
    "ValidationError",
    "ConfigurationError",
    "NetworkError",
]
