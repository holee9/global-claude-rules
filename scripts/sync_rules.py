#!/usr/bin/env python3
"""
Global Claude Rules - Sync Rules Script

Automated synchronization and conflict resolution for ERR rules across multiple machines.

Features:
- Automatic git pull with conflict resolution
- Automatic git push after local changes
- Timestamp-based conflict resolution
- Local-first or remote-first strategies
- Dry-run mode for preview

Usage:
    python scripts/sync_rules.py          # Auto-sync (pull + push if needed)
    python scripts/sync_rules.py --pull   # Pull only
    python scripts/sync_rules.py --push   # Push only
    python scripts/sync_rules.py --dry-run  # Preview changes
    python scripts/sync_rules.py --strategy local  # Local-first conflicts
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Import shared error types
sys.path.insert(0, str(Path(__file__).parent.parent))
try:
    from shared.errors import GitOperationError, FileOperationError
except ImportError:
    # Fallback if shared module not available
    class GitOperationError(Exception):
        pass
    class FileOperationError(Exception):
        pass

# =============================================================================
# Constants
# =============================================================================
CACHE_DIR = Path.home() / ".claude" / "cache"
SYNC_CACHE_FILE = CACHE_DIR / "sync_rules.json"

# Sync strategies
STRATEGY_LOCAL = "local"   # Keep local changes on conflict
STRATEGY_REMOTE = "remote" # Use remote changes on conflict
STRATEGY_MANUAL = "manual" # Stop and let user resolve

# Auto-sync interval (hours)
AUTO_SYNC_INTERVAL = 24


def setup_colors():
    """Setup ANSI colors for terminal output."""
    class Colors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'

    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except (AttributeError, OSError):
            Colors.disable()

    return Colors


Colors = setup_colors()


def print_header(text: str):
    """Print a header with formatting."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str):
    """Print success message."""
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    """Print error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    """Print warning message."""
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def get_project_root() -> Path:
    """Get the project root directory."""
    script_dir = Path(__file__).parent
    return script_dir


def get_last_sync_time() -> datetime | None:
    """Get the last successful sync time from cache.

    Returns:
        Last sync datetime or None
    """
    if SYNC_CACHE_FILE.exists():
        try:
            cache_data = json.loads(SYNC_CACHE_FILE.read_text(encoding="utf-8"))
            last_sync = cache_data.get("last_sync")
            if last_sync:
                return datetime.fromisoformat(last_sync)
        except (json.JSONDecodeError, ValueError):
            pass
    return None


def save_sync_time() -> None:
    """Save current time as last sync time."""
    try:
        SYNC_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        cache_data = {
            "last_sync": datetime.now().isoformat(),
        }
        SYNC_CACHE_FILE.write_text(
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
    last_sync = get_last_sync_time()
    if not last_sync:
        return True

    hours_since = (datetime.now() - last_sync).total_seconds() / 3600
    return hours_since >= AUTO_SYNC_INTERVAL


def check_git_repo() -> bool:
    """Check if current directory is a git repository.

    Returns:
        True if in a git repository
    """
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def check_remote_exists() -> bool:
    """Check if a git remote is configured.

    Returns:
        True if origin remote exists
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def check_has_local_changes() -> bool:
    """Check if there are uncommitted local changes.

    Returns:
        True if there are uncommitted changes
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            timeout=5
        )
        return len(result.stdout.strip()) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def check_ahead_of_remote() -> bool:
    """Check if local branch is ahead of remote.

    Returns:
        True if local has unpushed commits
    """
    try:
        result = subprocess.run(
            ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"],
            capture_output=True,
            timeout=5
        )
        if result.returncode == 0:
            ahead, _behind = result.stdout.strip().split("\t")
            return int(ahead) > 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        pass
    return False


def git_pull_rebase(strategy: str = STRATEGY_LOCAL, dry_run: bool = False) -> bool:
    """Perform git pull with rebase.

    Args:
        strategy: Conflict resolution strategy
        dry_run: If True, don't actually execute

    Returns:
        True if successful
    """
    if dry_run:
        print_info("Would execute: git pull --rebase")
        return True

    try:
        # Fetch first
        print_info("Fetching from remote...")
        result = subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True,
            timeout=30
        )

        if result.returncode != 0:
            print_warning("Fetch failed - continuing with rebase")

        # Check if we can fast-forward
        try:
            result = subprocess.run(
                ["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                behind, _ = result.stdout.strip().split("\t")
                if int(behind) == 0:
                    print_info("Already up to date")
                    return True
        except (ValueError, subprocess.TimeoutExpired):
            pass

        # Do rebase
        print_info("Rebasing local changes...")
        result = subprocess.run(
            ["git", "pull", "--rebase", "origin"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print_success("Pull successful")
            return True

        # Check for conflicts
        if "conflict" in result.stderr.lower() or "conflict" in result.stdout.lower():
            print_warning("Merge conflicts detected")

            if strategy == STRATEGY_LOCAL:
                print_info("Resolving with local-first strategy...")
                # Abort rebase and use local
                subprocess.run(["git", "rebase", "--abort"], capture_output=True, timeout=10)
                subprocess.run(["git", "reset", "--hard", "HEAD"], capture_output=True, timeout=10)
                # Pull with -X ours to prefer local
                result = subprocess.run(
                    ["git", "pull", "-X", "ours", "origin"],
                    capture_output=True,
                    timeout=30
                )
                if result.returncode == 0:
                    print_success("Resolved conflicts (local changes preserved)")
                    return True

            elif strategy == STRATEGY_REMOTE:
                print_info("Resolving with remote-first strategy...")
                subprocess.run(["git", "rebase", "--abort"], capture_output=True, timeout=10)
                # Hard reset to remote
                result = subprocess.run(
                    ["git", "reset", "--hard", "origin/HEAD"],
                    capture_output=True,
                    timeout=10
                )
                if result.returncode == 0:
                    print_success("Resolved conflicts (remote changes used)")
                    return True

            else:
                print_error("Manual conflict resolution required")
                print_info("Run 'git rebase --continue' or 'git rebase --abort'")
                return False

        print_error(f"Pull failed: {result.stderr}")
        return False

    except subprocess.TimeoutExpired:
        print_error("Pull timed out")
        return False
    except (FileNotFoundError, OSError) as e:
        print_error(f"Git command failed: {e}")
        return False


def git_push(dry_run: bool = False) -> bool:
    """Push local commits to remote.

    Args:
        dry_run: If True, don't actually execute

    Returns:
        True if successful
    """
    if dry_run:
        print_info("Would execute: git push")
        return True

    try:
        print_info("Pushing to remote...")
        result = subprocess.run(
            ["git", "push"],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            print_success("Push successful")
            return True

        # Check for specific errors
        if "does not appear to be a git repository" in result.stderr:
            print_error("Not a git repository")

        elif "unable to access" in result.stderr or "could not connect" in result.stderr:
            print_error("Network error - check internet connection")

        elif "rejected" in result.stderr:
            print_error("Push rejected - remote has new commits")
            print_info("Run 'git pull' first to sync")

        else:
            print_error(f"Push failed: {result.stderr}")

        return False

    except subprocess.TimeoutExpired:
        print_error("Push timed out")
        return False
    except (FileNotFoundError, OSError) as e:
        print_error(f"Git command failed: {e}")
        return False


def sync_rules(
    strategy: str = STRATEGY_LOCAL,
    dry_run: bool = False,
    pull_only: bool = False,
    push_only: bool = False,
    force: bool = False
) -> int:
    """Main sync function.

    Args:
        strategy: Conflict resolution strategy
        dry_run: Preview without executing
        pull_only: Only pull from remote
        push_only: Only push to remote
        force: Run sync even if auto-sync interval not met

    Returns:
        Exit code (0 = success)
    """
    print_header("ERR Rules Sync")

    project_root = get_project_root()
    os.chdir(project_root)

    # Check prerequisites
    if not check_git_repo():
        print_error("Not in a git repository")
        return 1

    if not check_remote_exists():
        print_warning("No git remote configured - skipping sync")
        print_info("To set up remote: git remote add origin <url>")
        return 0

    # Check if sync is needed
    if not force and not dry_run:
        if not should_auto_sync():
            last_sync = get_last_sync_time()
            hours_ago = (datetime.now() - last_sync).total_seconds() / 3600 if last_sync else 0
            print_info(f"Last sync {hours_ago:.1f} hours ago (interval: {AUTO_SYNC_INTERVAL}h)")
            print_info("Use --force to sync anyway")
            return 0

    # Check local changes
    has_changes = check_has_local_changes()
    if has_changes:
        print_warning("You have uncommitted changes")
        print_info("Commit or stash changes before syncing")
        return 1

    # Determine what to do
    if push_only:
        return 0 if git_push(dry_run) else 1

    if pull_only:
        result = git_pull_rebase(strategy, dry_run)
        if result:
            save_sync_time()
        return 0 if result else 1

    # Full sync: pull then push if needed
    was_ahead = check_ahead_of_remote()

    # Pull
    pull_success = git_pull_rebase(strategy, dry_run)
    if not pull_success:
        return 1

    # Push if we were ahead or are now ahead
    if was_ahead or check_ahead_of_remote():
        if not git_push(dry_run):
            return 1

    # Save sync time
    if not dry_run:
        save_sync_time()

    print_header("Sync Complete")
    print_success("Rules are synchronized")

    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Sync ERR rules across machines",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/sync_rules.py              # Auto-sync (pull + push)
  python scripts/sync_rules.py --pull       # Pull only
  python scripts/sync_rules.py --push       # Push only
  python scripts/sync_rules.py --dry-run    # Preview changes
  python scripts/sync_rules.py --strategy remote  # Remote-first
        """
    )

    parser.add_argument(
        "--pull",
        action="store_true",
        help="Pull from remote only"
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="Push to remote only"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview without making changes"
    )
    parser.add_argument(
        "--strategy",
        choices=[STRATEGY_LOCAL, STRATEGY_REMOTE, STRATEGY_MANUAL],
        default=STRATEGY_LOCAL,
        help="Conflict resolution strategy (default: local)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force sync even if auto-sync interval not met"
    )

    args = parser.parse_args()

    return sync_rules(
        strategy=args.strategy,
        dry_run=args.dry_run,
        pull_only=args.pull,
        push_only=args.push,
        force=args.force
    )


if __name__ == "__main__":
    sys.exit(main())
