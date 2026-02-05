#!/usr/bin/env python3
"""
Project Detector Module

Automatically detects project types from filesystem markers.
Used by hooks to filter and show relevant rules based on project context.

Supported detections:
- Frontend/Node.js (package.json)
- Python (requirements.txt, pyproject.toml, setup.py)
- Go (go.mod)
- Rust (Cargo.toml)
- Java (pom.xml, build.gradle)
- C++/C# (*.sln, *.vcxproj, *.csproj)
- Ruby (Gemfile)
- PHP (composer.json)
- Dart/Flutter (pubspec.yaml)
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

# =============================================================================
# Project Type Markers
# =============================================================================
PROJECT_MARKERS = {
    "frontend": [
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "next.config.js",
        "next.config.mjs",
        "vite.config.js",
        "vite.config.ts",
        "tsconfig.json",
    ],
    "python": [
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "poetry.lock",
        "tox.ini",
        ".python-version",
    ],
    "go": [
        "go.mod",
        "go.sum",
    ],
    "rust": [
        "Cargo.toml",
        "Cargo.lock",
    ],
    "java": [
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "settings.gradle",
        "gradlew",
        "gradlew.bat",
    ],
    "cpp": [
        ".sln",
        ".vcxproj",
        "CMakeLists.txt",
        "Makefile",
        "meson.build",
    ],
    "csharp": [
        ".csproj",
        ".sln",
    ],
    "ruby": [
        "Gemfile",
        "Rakefile",
    ],
    "php": [
        "composer.json",
        "artisan",
    ],
    "dart": [
        "pubspec.yaml",
        "pubspec.lock",
    ],
    "elixir": [
        "mix.exs",
    ],
    "scala": [
        "build.sbt",
    ],
}

# Project type to ERR rule mapping
PROJECT_TYPE_RULES = {
    "python": ["ERR-001", "ERR-004", "ERR-008", "ERR-009", "ERR-013", "ERR-022"],
    "fpga": ["ERR-005", "ERR-006", "ERR-007"],
    "frontend": ["ERR-500", "ERR-501"],
    "cpp": ["ERR-003", "ERR-004", "ERR-013"],
    "git": ["ERR-100", "ERR-101", "ERR-102"],
    "mfc": ["ERR-600", "ERR-601", "ERR-602"],
}

# Cache file path
CACHE_DIR = Path.home() / ".claude" / "cache"
PROJECT_CACHE_FILE = CACHE_DIR / "project_detection.json"


def find_project_root() -> Path:
    """Find project root by looking for common markers."""
    cwd = Path.cwd()
    for parent in [cwd] + list(cwd.parents):
        if (parent / ".moai").exists():
            return parent
        if (parent / ".git").exists():
            return parent
        # Check for common project files
        for markers in PROJECT_MARKERS.values():
            for marker in markers:
                if (parent / marker).exists():
                    return parent
    return cwd


def detect_from_files(project_root: Path) -> list[str]:
    """Detect project types from file markers.

    Args:
        project_root: Root directory of the project

    Returns:
        List of detected project types
    """
    detected_types = []

    for project_type, markers in PROJECT_MARKERS.items():
        for marker in markers:
            # Check for exact file match
            if (project_root / marker).exists():
                if project_type not in detected_types:
                    detected_types.append(project_type)
                break

            # Check for wildcard patterns (e.g., *.sln)
            if "*" in marker:
                pattern = marker.replace("*", "")
                if any(f.suffix == pattern or f.name.endswith(pattern)
                       for f in project_root.iterdir() if f.is_file()):
                    if project_type not in detected_types:
                        detected_types.append(project_type)
                    break

    return detected_types


def detect_from_git_remote(project_root: Path) -> str | None:
    """Detect project type from git remote URL.

    Args:
        project_root: Root directory of the project

    Returns:
        Detected project type or None
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=3,
            cwd=project_root
        )
        if result.returncode == 0:
            remote_url = result.stdout.strip().lower()

            # Check for common patterns
            if "python" in remote_url or "django" in remote_url or "flask" in remote_url:
                return "python"
            if "react" in remote_url or "vue" in remote_url or "next" in remote_url:
                return "frontend"
            if "go" in remote_url and "golang" in remote_url:
                return "go"
            if "rust" in remote_url:
                return "rust"
            if "java" in remote_url or "spring" in remote_url:
                return "java"
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def get_cache() -> dict[str, Any]:
    """Get cached project detection data.

    Returns:
        Cache dictionary with timestamp and detection data
    """
    if PROJECT_CACHE_FILE.exists():
        try:
            import json
            cache_data = json.loads(PROJECT_CACHE_FILE.read_text(encoding="utf-8"))

            # Check if cache is still valid (24 hours)
            cached_at = datetime.fromisoformat(cache_data.get("cached_at", ""))
            if datetime.now() - cached_at < timedelta(hours=24):
                return cache_data
        except (json.JSONDecodeError, ValueError, OSError):
            pass

    return {}


def save_cache(data: dict[str, Any]) -> None:
    """Save project detection data to cache.

    Args:
        data: Detection data to cache
    """
    try:
        import json
        PROJECT_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)

        cache_data = {
            "cached_at": datetime.now().isoformat(),
            "project_root": str(find_project_root()),
            **data
        }

        PROJECT_CACHE_FILE.write_text(
            json.dumps(cache_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except (OSError, PermissionError):
        pass


def detect_project_type(project_root: Path | None = None) -> dict[str, Any]:
    """Detect the current project type.

    Args:
        project_root: Project root directory (auto-detected if None)

    Returns:
        Dictionary with detection results:
        {
            "types": ["python", "frontend"],
            "primary": "python",
            "confidence": 0.9,
            "markers": ["requirements.txt", "pyproject.toml"]
        }
    """
    if project_root is None:
        project_root = find_project_root()

    # Check cache first
    cache = get_cache()
    if cache and cache.get("project_root") == str(project_root):
        return {
            "types": cache.get("types", []),
            "primary": cache.get("primary"),
            "confidence": cache.get("confidence", 0.0),
            "markers": cache.get("markers", []),
            "from_cache": True,
        }

    detected = detect_from_files(project_root)

    # Also check git remote for additional hints
    git_type = detect_from_git_remote(project_root)
    if git_type and git_type not in detected:
        detected.append(git_type)

    # Determine primary type (prioritize backend languages)
    priority_order = ["python", "go", "rust", "java", "cpp", "csharp",
                      "ruby", "php", "elixir", "scala", "dart", "frontend"]

    primary = None
    for ptype in priority_order:
        if ptype in detected:
            primary = ptype
            break

    if not primary and detected:
        primary = detected[0]

    # Collect found markers
    markers = []
    if detected:
        for ptype in detected:
            for marker in PROJECT_MARKERS.get(ptype, []):
                if (project_root / marker).exists():
                    markers.append(marker)

    result = {
        "types": detected,
        "primary": primary,
        "confidence": len(detected) / len(PROJECT_MARKERS) if detected else 0.0,
        "markers": markers,
        "from_cache": False,
    }

    # Save to cache
    save_cache(result)

    return result


def get_relevant_rules_for_project(project_type: str | None = None) -> list[str]:
    """Get relevant ERR rule IDs for the detected project type.

    Args:
        project_type: Project type (auto-detected if None)

    Returns:
        List of relevant ERR rule IDs
    """
    if project_type is None:
        detection = detect_project_type()
        project_type = detection.get("primary")

    if not project_type:
        # Return general rules if no specific type detected
        return ["ERR-001", "ERR-002", "ERR-003", "ERR-004"]

    # Get rules for this type
    rules = PROJECT_TYPE_RULES.get(project_type, [])

    # Always include general rules
    general_rules = ["ERR-001", "ERR-002", "ERR-003", "ERR-004"]
    for rule in general_rules:
        if rule not in rules:
            rules.append(rule)

    return rules


def main() -> None:
    """CLI entry point for testing project detection."""
    detection = detect_project_type()

    print("Project Detection Results:")
    print(f"  Root: {find_project_root()}")
    print(f"  Types: {', '.join(detection['types']) or 'None'}")
    print(f"  Primary: {detection['primary'] or 'Unknown'}")
    print(f"  Confidence: {detection['confidence']:.1%}")
    print(f"  Markers: {', '.join(detection['markers']) or 'None'}")
    print(f"  From Cache: {detection['from_cache']}")

    relevant_rules = get_relevant_rules_for_project(detection['primary'])
    print(f"\nRelevant Rules: {', '.join(relevant_rules)}")


if __name__ == "__main__":
    main()
