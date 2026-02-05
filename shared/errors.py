#!/usr/bin/env python3
"""
Shared Error Handling Module for Global Claude Rules

Provides consistent exception types across all scripts.
"""

from __future__ import annotations


class GlobalRulesError(Exception):
    """Base exception for Global Rules system."""

    def __init__(self, message: str, details: dict | None = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} - {self.details}"
        return self.message


class FileOperationError(GlobalRulesError):
    """File operation failed."""

    pass


class GitOperationError(GlobalRulesError):
    """Git operation failed."""

    pass


class ValidationError(GlobalRulesError):
    """Validation failed."""

    pass


class ConfigurationError(GlobalRulesError):
    """Configuration error."""

    pass


class NetworkError(GlobalRulesError):
    """Network operation failed."""

    pass
