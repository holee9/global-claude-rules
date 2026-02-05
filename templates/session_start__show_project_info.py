#!/usr/bin/env python3
# SessionStart Hook: Enhanced Project Information
"""SessionStart Hook: Enhanced Project Information

Claude Code Event: SessionStart
Purpose: Display enhanced project status with Git info, test status, and SPEC progress
Execution: Triggered automatically when Claude Code session begins

Enhanced Features:
- Environment-aware path detection (cross-platform)
- Optimized timeout handling with unified manager
- Efficient Git operations with connection pooling and caching
- Enhanced error handling with graceful degradation
- Risk assessment with performance metrics
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# =============================================================================
# Windows UTF-8 Encoding Fix (Issue #249)
# =============================================================================
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, OSError):
        pass

# =============================================================================
# Environment-Aware Path Detection
# =============================================================================
def get_global_memory_path() -> Path:
    """Get the global memory path based on environment.

    Priority:
    1. Environment variable GLOBAL_CLAUDE_MEMORY
    2. Default: ~/.claude/memory.md (home directory)

    Returns:
        Path to global memory file
    """
    # Check environment variable first
    if path_env := os.getenv("GLOBAL_CLAUDE_MEMORY"):
        return Path(path_env)

    # Default to home directory
    return Path.home() / ".claude" / "memory.md"


def get_global_guide_path() -> Path:
    """Get the global guide path based on environment.

    Priority:
    1. Environment variable GLOBAL_CLAUDE_GUIDE
    2. Windows: D:/GLOBAL_RULES_GUIDE.md (fallback)
    3. Default: ~/.claude/GLOBAL_RULES_GUIDE.md

    Returns:
        Path to global guide file
    """
    # Check environment variable first
    if path_env := os.getenv("GLOBAL_CLAUDE_GUIDE"):
        return Path(path_env)

    # Windows-specific default path
    if sys.platform == "win32":
        # Try D: drive first (common Windows setup)
        d_drive_path = Path("D:/GLOBAL_RULES_GUIDE.md")
        if d_drive_path.exists():
            return d_drive_path

    # Default to home directory
    return Path.home() / ".claude" / "GLOBAL_RULES_GUIDE.md"


def get_claude_config_path() -> Path:
    """Get the Claude Code configuration directory path.

    Returns:
        Path to .claude directory
    """
    # Check environment variable first
    if path_env := os.getenv("CLAUDE_CONFIG_DIR"):
        return Path(path_env)

    # Default to home directory
    return Path.home() / ".claude"


# =============================================================================
# Constants - Risk Assessment Thresholds
# =============================================================================
RISK_SCORE_HIGH = 20
RISK_SCORE_MEDIUM = 10
GIT_CHANGES_HIGH_THRESHOLD = 20
GIT_CHANGES_MEDIUM_THRESHOLD = 10
SPEC_PROGRESS_LOW = 50
SPEC_PROGRESS_MEDIUM = 80
RISK_GIT_CHANGES_HIGH = 10
RISK_GIT_CHANGES_MEDIUM = 5
RISK_SPEC_LOW = 15
RISK_SPEC_MEDIUM = 8
RISK_TEST_FAILED = 12
RISK_COVERAGE_UNKNOWN = 5
SETUP_MESSAGE_RESCAN_DAYS = 7
AUTO_SYNC_INTERVAL_DAYS = 7
AUTO_SYNC_CACHE_FILE = Path.home() / ".claude" / "cache" / "auto_sync.json"

# =============================================================================
# Setup import path for shared modules
# =============================================================================
HOOKS_DIR = Path(__file__).parent
LIB_DIR = HOOKS_DIR / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

try:
    from lib.file_utils import check_file_size
    from lib.path_utils import find_project_root
except ImportError:
    # Fallback implementations
    def check_file_size(file_path: Path, max_size_mb: int = 10) -> tuple[bool, str]:
        """Check if file size is within safe limits."""
        try:
            size = file_path.stat().st_size
            if size > max_size_mb * 1024 * 1024:
                return False, f"File too large: {size / 1024 / 1024:.1f}MB"
            return True, ""
        except OSError:
            return False, "Cannot access file"

    def find_project_root() -> Path:
        """Find project root by looking for .moai directory."""
        cwd = Path.cwd()
        for parent in [cwd] + list(cwd.parents):
            if (parent / ".moai").exists():
                return parent
            if (parent / ".git").exists():
                return parent
        return cwd

# Import unified timeout manager and Git operations manager
try:
    from lib.git_operations_manager import GitOperationType, get_git_manager
    from lib.timeout import TimeoutError as PlatformTimeoutError
    from lib.unified_timeout_manager import (
        HookTimeoutConfig,
        HookTimeoutError,
        TimeoutPolicy,
        get_timeout_manager,
        hook_timeout_context,
    )
except ImportError:
    def get_timeout_manager():
        return None

    def hook_timeout_context(hook_name, config=None):
        import contextlib
        @contextlib.contextmanager
        def dummy_context():
            yield
        return dummy_context()

    class HookTimeoutConfig:
        def __init__(self, **kwargs):
            pass

    class TimeoutPolicy:
        FAST = "fast"
        NORMAL = "normal"
        SLOW = "slow"

    class HookTimeoutError(Exception):
        pass

    def get_git_manager():
        return None

    class GitOperationType:
        BRANCH = "branch"
        LOG = "log"
        STATUS = "status"

    class PlatformTimeoutError(Exception):
        pass


# Import config cache
try:
    from core.config_cache import get_cached_config, get_cached_spec_progress
except ImportError:
    try:
        import yaml as yaml_fallback
        HAS_YAML_FALLBACK = True
    except ImportError:
        HAS_YAML_FALLBACK = False

    def _simple_yaml_parse(content: str) -> dict:
        """Simple YAML parser for basic configs."""
        result = {}
        current_section = None
        lines = content.split("\n")

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            indent = len(line) - len(line.lstrip())

            if ":" in stripped:
                key_part, _, value_part = stripped.partition(":")
                key = key_part.strip()
                value = value_part.strip()
                was_quoted = False

                if value.startswith('"'):
                    close_quote = value.find('"', 1)
                    if close_quote > 0:
                        value = value[1:close_quote]
                        was_quoted = True
                elif value.startswith("'"):
                    close_quote = value.find("'", 1)
                    if close_quote > 0:
                        value = value[1:close_quote]
                        was_quoted = True

                if indent == 0:
                    if value or was_quoted:
                        result[key] = _parse_simple_value(value)
                    else:
                        current_section = key
                        result[current_section] = {}
                elif current_section and indent > 0:
                    if value or was_quoted:
                        result[current_section][key] = _parse_simple_value(value)

        return result

    def _parse_simple_value(value: str):
        if not value:
            return ""
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        try:
            if "." in value:
                return float(value)
            return int(value)
        except ValueError:
            pass
        return value

    def _merge_configs(base: dict, override: dict) -> dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = _merge_configs(result[key], value)
            else:
                result[key] = value
        return result

    def _load_yaml_file(file_path: Path) -> dict:
        if not file_path.exists():
            return {}
        is_safe, _ = check_file_size(file_path)
        if not is_safe:
            return {}
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
            if HAS_YAML_FALLBACK:
                return yaml_fallback.safe_load(content) or {}
            else:
                return _simple_yaml_parse(content)
        except Exception:
            return {}

    def get_cached_config():
        project_root = find_project_root()
        config_dir = project_root / ".moai" / "config"
        main_config_path = config_dir / "config.yaml"
        config = _load_yaml_file(main_config_path)

        if not config:
            json_config_path = config_dir / "config.json"
            if json_config_path.exists():
                is_safe, _ = check_file_size(json_config_path)
                if is_safe:
                    try:
                        config = json.loads(json_config_path.read_text(encoding="utf-8", errors="replace"))
                    except (json.JSONDecodeError, OSError):
                        config = {}

        sections_dir = config_dir / "sections"
        if sections_dir.exists():
            section_files = [
                ("user.yaml", "user"),
                ("language.yaml", "language"),
                ("git-strategy.yaml", "git_strategy"),
                ("project.yaml", "project"),
                ("quality.yaml", "quality"),
                ("system.yaml", "system"),
            ]
            for filename, key in section_files:
                section_path = sections_dir / filename
                section_data = _load_yaml_file(section_path)
                if section_data:
                    config = _merge_configs(config, section_data)

        return config if config else None

    def get_cached_spec_progress():
        project_root = find_project_root()
        specs_dir = project_root / ".moai" / "specs"

        if not specs_dir.exists():
            return {"completed": 0, "total": 0, "percentage": 0}
        try:
            spec_folders = [d for d in specs_dir.iterdir() if d.is_dir() and d.name.startswith("SPEC-")]
            total = len(spec_folders)
            completed = 0
            for folder in spec_folders:
                spec_file = folder / "spec.md"
                if not spec_file.exists():
                    continue
                try:
                    content = spec_file.read_text(encoding="utf-8", errors="replace")
                    if content.startswith("---"):
                        yaml_end = content.find("---", 3)
                        if yaml_end > 0:
                            yaml_content = content[3:yaml_end]
                            if "status: completed" in yaml_content:
                                completed += 1
                except (OSError, UnicodeDecodeError):
                    pass

            percentage = (completed / total * 100) if total > 0 else 0
            return {
                "completed": completed,
                "total": total,
                "percentage": round(percentage, 0),
            }
        except (OSError, PermissionError):
            return {"completed": 0, "total": 0, "percentage": 0}


def should_show_setup_messages() -> bool:
    """Determine whether to show setup completion messages."""
    config = get_cached_config()
    if not config:
        return True
    if not config.get("project", {}).get("initialized", False):
        return True
    session_config = config.get("session", {})
    suppress = session_config.get("suppress_setup_messages", False)
    if not suppress:
        return True
    suppressed_at_str = session_config.get("setup_messages_suppressed_at")
    if not suppressed_at_str:
        return True
    try:
        suppressed_at = datetime.fromisoformat(suppressed_at_str)
        now = datetime.now(suppressed_at.tzinfo) if suppressed_at.tzinfo else datetime.now()
        days_passed = (now - suppressed_at).days
        return days_passed >= SETUP_MESSAGE_RESCAN_DAYS
    except (ValueError, TypeError):
        return True


def check_git_initialized() -> bool:
    """Check if git repository is initialized."""
    try:
        project_root = find_project_root()
        git_dir = project_root / ".git"
        return git_dir.exists() and git_dir.is_dir()
    except Exception:
        return False


def get_git_info() -> dict[str, Any]:
    """Get comprehensive git information."""
    if not check_git_initialized():
        return {
            "branch": "Git not initialized",
            "last_commit": "Git not initialized",
            "commit_time": "",
            "changes": 0,
            "git_initialized": False,
        }

    git_manager = get_git_manager()
    if git_manager:
        try:
            project_info = git_manager.get_project_info(use_cache=True)
            branch = project_info.get("branch", "unknown")
            last_commit = project_info.get("last_commit", "unknown")

            if not branch or branch == "unknown":
                branch = "No commits yet"
            if not last_commit or last_commit == "unknown":
                last_commit = "No commits yet"

            return {
                "branch": branch,
                "last_commit": last_commit,
                "commit_time": project_info.get("commit_time", "unknown"),
                "changes": project_info.get("changes", 0),
                "git_initialized": True,
            }
        except Exception as e:
            logging.warning(f"Git manager failed: {e}")

    # Fallback
    try:
        import concurrent.futures
        from concurrent.futures import ThreadPoolExecutor, as_completed

        git_commands = [
            (["git", "branch", "--show-current"], "branch"),
            (["git", "rev-parse", "--abbrev-ref", "HEAD"], "head_ref"),
            (["git", "rev-parse", "--short", "HEAD"], "head_commit"),
            (["git", "log", "--pretty=format:%h %s", "-1"], "last_commit"),
            (["git", "log", "--pretty=format:%ar", "-1"], "commit_time"),
            (["git", "status", "--porcelain"], "changes_raw"),
        ]

        results = {}
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(_run_git_command_fallback, cmd): key for cmd, key in git_commands}
            try:
                for future in as_completed(futures, timeout=8):
                    key = futures[future]
                    try:
                        results[key] = future.result()
                    except (TimeoutError, RuntimeError):
                        results[key] = ""
            except concurrent.futures.TimeoutError:
                for future, key in futures.items():
                    if future.done():
                        try:
                            if key not in results:
                                results[key] = future.result()
                        except (TimeoutError, RuntimeError):
                            results[key] = ""

        branch = results.get("branch", "")
        head_ref = results.get("head_ref", "")
        if not branch and head_ref == "HEAD":
            branch = f"HEAD detached at {results.get('head_commit', '')}"
        elif not branch:
            branch = "No commits yet"

        last_commit = results.get("last_commit", "")
        if not last_commit:
            last_commit = "No commits yet"

        return {
            "branch": branch,
            "last_commit": last_commit,
            "commit_time": results.get("commit_time", ""),
            "changes": (len(results.get("changes_raw", "").splitlines()) if results.get("changes_raw") else 0),
            "git_initialized": True,
        }

    except (RuntimeError, OSError, TimeoutError):
        return {
            "branch": "Error reading git info",
            "last_commit": "Error reading git info",
            "commit_time": "",
            "changes": 0,
            "git_initialized": True,
        }


def _run_git_command_fallback(cmd: list[str]) -> str:
    """Fallback git command execution."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError, OSError):
        return ""


def get_git_strategy_info(config: dict) -> dict:
    """Get git strategy information from config."""
    if not config:
        return {"git_flow": "unknown", "auto_branch": "unknown"}

    git_strategy = config.get("git_strategy", {})
    mode = git_strategy.get("mode", "manual")
    branch_creation = git_strategy.get("branch_creation", {})
    auto_enabled = branch_creation.get("auto_enabled", False)
    auto_branch_display = "Yes" if auto_enabled else "No"

    return {"git_flow": mode, "auto_branch": auto_branch_display}


def _parse_version(version_str: str) -> tuple[int, ...]:
    """Parse version string to comparable tuple."""
    try:
        clean = version_str.lstrip("v")
        parts = [int(x) for x in re.split(r"[^\d]+", clean) if x.isdigit()]
        return tuple(parts) if parts else (0,)
    except (ValueError, AttributeError, TypeError):
        return (0,)


def _is_newer_version(newer: str, older: str) -> bool:
    """Compare two versions."""
    newer_parts = _parse_version(newer)
    older_parts = _parse_version(older)
    return newer_parts > older_parts


def check_version_update() -> tuple[str, bool]:
    """Check if version update is available."""
    try:
        import importlib.metadata
        try:
            installed_version = importlib.metadata.version("moai-adk")
        except importlib.metadata.PackageNotFoundError:
            return "(latest)", False

        version_cache_file = find_project_root() / ".moai" / "cache" / "version-check.json"
        latest_version = None

        if version_cache_file.exists():
            try:
                cache_data = json.loads(version_cache_file.read_text(encoding="utf-8", errors="replace"))
                latest_version = cache_data.get("latest")
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                pass

        if not latest_version:
            return "(latest)", False

        if _is_newer_version(latest_version, installed_version):
            return f"⬆️ {latest_version} available", True
        elif _is_newer_version(installed_version, latest_version):
            return "(dev)", False
        else:
            return "(latest)", False

    except (ImportError, AttributeError, TypeError):
        return "(latest)", False


def get_test_info() -> dict[str, Any]:
    """Get test coverage and status information."""
    return {"coverage": "unknown", "status": "❓"}


def get_spec_progress() -> dict[str, Any]:
    """Get SPEC progress information."""
    return get_cached_spec_progress()


def calculate_risk(git_info: dict, spec_progress: dict, test_info: dict) -> str:
    """Calculate overall project risk level."""
    risk_score = 0

    if git_info["changes"] > GIT_CHANGES_HIGH_THRESHOLD:
        risk_score += RISK_GIT_CHANGES_HIGH
    elif git_info["changes"] > GIT_CHANGES_MEDIUM_THRESHOLD:
        risk_score += RISK_GIT_CHANGES_MEDIUM

    if spec_progress["percentage"] < SPEC_PROGRESS_LOW:
        risk_score += RISK_SPEC_LOW
    elif spec_progress["percentage"] < SPEC_PROGRESS_MEDIUM:
        risk_score += RISK_SPEC_MEDIUM

    if test_info["status"] != "✅":
        risk_score += RISK_TEST_FAILED
    elif test_info["coverage"] == "unknown":
        risk_score += RISK_COVERAGE_UNKNOWN

    if risk_score >= RISK_SCORE_HIGH:
        return "HIGH"
    elif risk_score >= RISK_SCORE_MEDIUM:
        return "MEDIUM"
    else:
        return "LOW"


def get_language_info(config: dict) -> dict:
    """Get language configuration information."""
    if not config:
        return {
            "conversation_language": "en",
            "language_name": "English",
        }

    lang_config = config.get("language", {})
    return {
        "conversation_language": lang_config.get("conversation_language", "en"),
        "language_name": lang_config.get("conversation_language_name", "Unknown"),
    }


def load_user_personalization() -> dict:
    """Load user personalization settings."""
    try:
        from src.moai_adk.core.language_config_resolver import get_resolver
        resolver = get_resolver(str(find_project_root()))
        config = resolver.resolve_config()

        user_name = config.get("user_name", "")
        has_valid_name = user_name and not user_name.startswith("{{")

        personalization = {
            "user_name": user_name if has_valid_name else "",
            "conversation_language": config.get("conversation_language", "en"),
            "conversation_language_name": config.get("conversation_language_name", "English"),
            "agent_prompt_language": config.get("agent_prompt_language", "en"),
            "is_korean": config.get("conversation_language") == "ko",
            "has_personalization": has_valid_name,
            "config_source": config.get("config_source", "default"),
            "personalized_greeting": (resolver.get_personalized_greeting(config) if has_valid_name else ""),
            "needs_setup": not has_valid_name,
        }

        template_vars = resolver.export_template_variables(config)
        personalization_cache_file = find_project_root() / ".moai" / "cache" / "personalization.json"
        try:
            personalization_cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_data = {
                "personalization": personalization,
                "template_variables": template_vars,
                "resolved_at": datetime.now().isoformat(),
                "config_source": config.get("config_source", "default"),
            }
            personalization_cache_file.write_text(json.dumps(cache_data, ensure_ascii=False, indent=2))
        except (OSError, PermissionError):
            pass

        return personalization

    except ImportError:
        import os
        config = get_cached_config()
        user_name = os.getenv("MOAI_USER_NAME")
        conversation_lang = os.getenv("MOAI_CONVERSATION_LANG")

        if user_name is None and config:
            user_name = config.get("user", {}).get("name", "")
        if conversation_lang is None and config:
            conversation_lang = config.get("language", {}).get("conversation_language", "en")

        has_valid_name = user_name and not user_name.startswith("{{")

        lang_name_map = {
            "ko": "Korean", "en": "English", "ja": "Japanese", "zh": "Chinese",
            "es": "Spanish", "fr": "French", "de": "German", "ru": "Russian",
        }
        lang_name = lang_name_map.get(conversation_lang, "Unknown")

        return {
            "user_name": user_name if has_valid_name else "",
            "conversation_language": conversation_lang or "en",
            "conversation_language_name": lang_name,
            "is_korean": conversation_lang == "ko",
            "has_personalization": has_valid_name,
            "config_source": "fallback",
            "personalized_greeting": (
                f"{user_name}님" if has_valid_name and conversation_lang == "ko"
                else user_name if has_valid_name else ""
            ),
            "needs_setup": not has_valid_name,
        }


def inject_global_rules() -> str:
    """Inject global memory and project-specific rules into session context."""
    parts = []

    # Use environment-aware path detection
    global_memory_path = get_global_memory_path()

    if global_memory_path.exists():
        try:
            global_content = global_memory_path.read_text(encoding="utf-8", errors="replace")

            essential_rules = []
            lines = global_content.split("\n")
            current_err = None
            in_essential_section = False

            for i, line in enumerate(lines):
                if "## 4. Common Errors Across All Projects" in line or "ERR-001:" in line:
                    in_essential_section = True

                if in_essential_section and line.startswith("## ") and "Common Errors" not in line:
                    if "ERR-" not in line:
                        break

                if in_essential_section:
                    essential_rules.append(line)
                    if "ERR-017:" in line:
                        essential_rules = essential_rules[:-1]
                        break

            if essential_rules:
                parts.append("\n## 🌍 GLOBAL RULES (Auto-loaded)")
                parts.append("## Common Errors Across All Projects (Claude Code Working)")
                parts.extend(essential_rules[:300])

            quick_ref_match = re.search(
                r"\| Error ID \|.*?\n(\|.*?\|.*?\|.*?\|\n)+",
                global_content,
                re.MULTILINE
            )
            if quick_ref_match:
                parts.append("\n## Error Quick Reference")
                parts.append(quick_ref_match.group(0))

        except (OSError, UnicodeDecodeError):
            parts.append("\n⚠️ Global Memory: Unable to read")

    # Read project-specific memory
    project_memory_path = find_project_root() / ".claude" / "memory.md"
    if project_memory_path.exists():
        try:
            project_content = project_memory_path.read_text(encoding="utf-8", errors="replace")
            parts.append("\n## 📁 PROJECT-SPECIFIC RULES")
            parts.append(project_content[:500])
        except (OSError, UnicodeDecodeError):
            pass

    lessons_path = find_project_root() / "doc" / "LESSONS_LEARNED.md"
    if lessons_path.exists():
        try:
            lessons_content = lessons_path.read_text(encoding="utf-8", errors="replace")
            err_entries = re.findall(r"### ERR-\d+:.*?(?=### ERR-\d+:|##|\Z)", lessons_content, re.DOTALL)
            if err_entries:
                parts.append("\n## 📋 Project Lessons Learned")
                for entry in err_entries[:3]:
                    parts.append(entry.strip())
        except (OSError, UnicodeDecodeError):
            pass

    return "\n".join(parts)


def get_global_memory_summary() -> str:
    """Get summary of global memory rules."""
    global_memory_path = get_global_memory_path()
    global_guide_path = get_global_guide_path()

    output_lines = []

    if global_memory_path.exists():
        try:
            content = global_memory_path.read_text(encoding="utf-8", errors="replace")
            err_matches = re.findall(r"### ERR-(\d+):", content)
            err_count = len(set(err_matches))

            date_match = re.search(r"\*\*Last Updated\*\*: (\d{4}-\d{2}-\d{2})", content)
            last_updated = date_match.group(1) if date_match else "Unknown"

            output_lines.append(f"   📚 Global Memory: {err_count} error rules (Last: {last_updated})")
        except (OSError, UnicodeDecodeError):
            output_lines.append("   ⚠️ Global Memory: Unable to read")
    else:
        output_lines.append("   ⚠️ Global Memory: File not found")

    if global_guide_path.exists():
        try:
            content = global_guide_path.read_text(encoding="utf-8", errors="replace")
            version_match = re.search(r"\*\*Version\*\*: ([\d.]+)", content)
            version = version_match.group(1) if version_match else "Unknown"
            output_lines.append(f"   📖 Global Guide: v{version}")
        except (OSError, UnicodeDecodeError):
            pass

    return "\n".join(output_lines) if output_lines else ""


def get_last_auto_sync_time() -> datetime | None:
    """Get the last successful auto-sync time from cache.

    Returns:
        Last sync datetime or None
    """
    if AUTO_SYNC_CACHE_FILE.exists():
        try:
            cache_data = json.loads(AUTO_SYNC_CACHE_FILE.read_text(encoding="utf-8", errors="replace"))
            last_sync = cache_data.get("last_sync")
            if last_sync:
                return datetime.fromisoformat(last_sync)
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def save_auto_sync_time() -> None:
    """Save current time as last auto-sync time."""
    try:
        AUTO_SYNC_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {
            "last_sync": datetime.now().isoformat(),
            "project_root": str(find_project_root()),
        }
        AUTO_SYNC_CACHE_FILE.write_text(
            json.dumps(cache_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    except (OSError, PermissionError):
        pass


def should_auto_sync() -> bool:
    """Check if auto-sync should run based on time interval.

    Returns:
        True if enough time has passed since last sync
    """
    last_sync = get_last_auto_sync_time()
    if not last_sync:
        return True

    days_since = (datetime.now() - last_sync).days
    return days_since >= AUTO_SYNC_INTERVAL_DAYS


def background_auto_sync() -> None:
    """Perform background auto-sync of rules.

    This function runs git pull in the background to update rules.
    It gracefully handles failures and doesn't block session start.
    """
    try:
        import threading

        def sync_in_background():
            try:
                project_root = find_project_root()
                os.chdir(project_root)

                # Check if we're in a git repo with remote
                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode != 0:
                    return  # No remote configured

                # Check if there are remote changes
                subprocess.run(
                    ["git", "fetch", "origin"],
                    capture_output=True,
                    timeout=30
                )

                result = subprocess.run(
                    ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"],
                    capture_output=True,
                    timeout=5
                )

                if result.returncode == 0:
                    behind, _ = result.stdout.strip().split("\t")
                    if int(behind) > 0:
                        # Has remote changes, pull with rebase
                        subprocess.run(
                            ["git", "pull", "--rebase", "-X", "ours", "origin"],
                            capture_output=True,
                            timeout=60
                        )
                        save_auto_sync_time()

            except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
                pass  # Silent failure - don't interrupt session

        # Start background thread
        thread = threading.Thread(target=sync_in_background, daemon=True)
        thread.start()

    except ImportError:
        pass


def format_session_output() -> str:
    """Format the complete session start output."""
    git_info = get_git_info()
    config = get_cached_config()
    personalization = load_user_personalization()

    try:
        result = subprocess.run(["moai", "--version"], capture_output=True, text=True, check=True, timeout=5)
        version_match = re.search(r"(\d+\.\d+\.\d+)", result.stdout)
        moai_version = version_match.group(1) if version_match else "unknown"
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        moai_version = "unknown"
        if config:
            moai_version = config.get("moai", {}).get("version", "unknown")

    lang_info = get_language_info(config)
    git_strategy = get_git_strategy_info(config)
    version_status, _has_update = check_version_update()

    output = [
        "🚀 MoAI-ADK Session Started",
        f"   📦 Version: {moai_version} {version_status}",
        f"   🔄 Changes: {git_info['changes']}",
        f"   🌿 Branch: {git_info['branch']}",
        f"   🔧 Github-Flow: {git_strategy['git_flow']} | Auto Branch: {git_strategy['auto_branch']}",
        f"   🔨 Last Commit: {git_info['last_commit']}",
        f"   🌐 Language: {lang_info['language_name']} ({lang_info['conversation_language']})",
    ]

    global_memory_summary = get_global_memory_summary()
    if global_memory_summary:
        output.append(global_memory_summary)

    conv_lang = personalization.get("conversation_language", "en")

    if personalization.get("needs_setup", False):
        setup_messages = {
            "ko": "   👋 환영합니다! '/moai:0-project' 명령어로 프로젝트 문서를 생성해주세요",
            "ja": "   👋 ようこそ！'/moai:0-project' コマンドでプロジェクトドキュメントを生成してください",
            "zh": "   👋 欢迎！请运行 '/moai:0-project' 命令生成项目文档",
            "en": "   👋 Welcome! Please run '/moai:0-project' to generate project documentation",
        }
        output.append(setup_messages.get(conv_lang, setup_messages["en"]))
    elif personalization["has_personalization"]:
        user_greeting = personalization.get("personalized_greeting", "")
        user_name = personalization.get("user_name", "")
        display_name = user_greeting if user_greeting else user_name

        ko_suffix = "" if display_name.endswith("님") else "님"
        ja_suffix = "" if display_name.endswith("さん") else "さん"

        welcome_back_messages = {
            "ko": f"   👋 다시 오신 것을 환영합니다, {display_name}{ko_suffix}!",
            "ja": f"   👋 おかえりなさい、{display_name}{ja_suffix}！",
            "zh": f"   👋 欢迎回来，{display_name}！",
            "en": f"   👋 Welcome back, {display_name}!",
        }
        output.append(welcome_back_messages.get(conv_lang, welcome_back_messages["en"]))

    return "\n".join(output)


def main() -> None:
    """Main entry point for enhanced SessionStart hook."""
    timeout_config = HookTimeoutConfig(
        policy=TimeoutPolicy.NORMAL,
        custom_timeout_ms=5000,
        retry_count=1,
        retry_delay_ms=200,
        graceful_degradation=True,
        memory_limit_mb=100,
    )

    def execute_session_start():
        input_data = sys.stdin.read() if not sys.stdin.isatty() else "{}"
        _ = json.loads(input_data) if input_data.strip() else {}

        # Background auto-sync if needed
        if should_auto_sync():
            background_auto_sync()

        show_messages = should_show_setup_messages()
        session_output = format_session_output() if show_messages else ""
        global_rules = inject_global_rules()

        full_system_message = session_output
        if global_rules:
            full_system_message += global_rules

        result: dict[str, Any] = {
            "continue": True,
            "systemMessage": full_system_message,
            "performance": {
                "git_manager_used": get_git_manager() is not None,
                "timeout_manager_used": get_timeout_manager() is not None,
                "global_rules_loaded": len(global_rules) > 0,
                "global_rules_chars": len(global_rules),
            },
        }

        return result

    timeout_manager = get_timeout_manager()
    if timeout_manager:
        try:
            result = timeout_manager.execute_with_timeout(
                "session_start__show_project_info",
                execute_session_start,
                config=timeout_config,
            )
            print(json.dumps(result, ensure_ascii=False))
            sys.exit(0)

        except HookTimeoutError as e:
            timeout_response: dict[str, Any] = {
                "continue": True,
                "systemMessage": "⚠️ Session start timeout - continuing without project info",
                "error_details": {
                    "hook_id": e.hook_id,
                    "timeout_seconds": e.timeout_seconds,
                    "execution_time": e.execution_time,
                    "will_retry": e.will_retry,
                },
            }
            print(json.dumps(timeout_response, ensure_ascii=False))
            print(f"SessionStart hook timeout: {e}", file=sys.stderr)
            sys.exit(1)

        except Exception as e:
            error_response: dict[str, Any] = {
                "continue": True,
                "systemMessage": "⚠️ Session start encountered an error - continuing",
                "error_details": {
                    "error_type": type(e).__name__,
                    "message": str(e),
                    "graceful_degradation": True,
                },
            }
            print(json.dumps(error_response, ensure_ascii=False))
            print(f"SessionStart error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            from lib.timeout import CrossPlatformTimeout
            from lib.timeout import TimeoutError as PlatformTimeoutError

            timeout = CrossPlatformTimeout(5)
            timeout.start()

            try:
                result = execute_session_start()
                print(json.dumps(result))
                sys.exit(0)

            except PlatformTimeoutError:
                timeout_response_legacy: dict[str, Any] = {
                    "continue": True,
                    "systemMessage": "⚠️ Session start timeout - continuing without project info",
                }
                print(json.dumps(timeout_response_legacy))
                print("SessionStart hook timeout after 5 seconds", file=sys.stderr)
                sys.exit(1)

            finally:
                timeout.cancel()

        except ImportError:
            try:
                result = execute_session_start()
                print(json.dumps(result))
                sys.exit(0)
            except Exception as e:
                print(
                    json.dumps(
                        {
                            "continue": True,
                            "systemMessage": "⚠️ Session start completed with errors",
                            "error": str(e),
                        }
                    )
                )
                sys.exit(0)

        except json.JSONDecodeError as e:
            json_error_response: dict[str, Any] = {
                "continue": True,
                "hookSpecificOutput": {"error": f"JSON parse error: {e}"},
            }
            print(json.dumps(json_error_response))
            print(f"SessionStart JSON parse error: {e}", file=sys.stderr)
            sys.exit(1)

        except Exception as e:
            general_error_response: dict[str, Any] = {
                "continue": True,
                "hookSpecificOutput": {"error": f"SessionStart error: {e}"},
            }
            print(json.dumps(general_error_response))
            print(f"SessionStart unexpected error: {e}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
