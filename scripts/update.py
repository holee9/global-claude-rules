#!/usr/bin/env python3
"""
Global Claude Rules - Auto Update Script

Automatically updates the global rules system by:
- Pulling latest changes from git
- Running install.py --force for reinstallation
- Showing changelog summary
- Version checking before update

Usage:
    python scripts/update.py
    python scripts/update.py --dry-run
    python scripts/update.py --no-install

Features:
- Git-based update from remote repository
- Automatic reinstallation after pull
- Changelog summary display
- Version conflict detection
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def disable():
        """Disable colors."""
        Colors.HEADER = ''
        Colors.OKBLUE = ''
        Colors.OKCYAN = ''
        Colors.OKGREEN = ''
        Colors.WARNING = ''
        Colors.FAIL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''


def setup_colors():
    """Setup colors based on platform."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
        except (AttributeError, OSError):
            Colors.disable()


def print_header(text: str):
    """Print a header."""
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


def get_script_dir() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent.resolve()


def get_current_version() -> str:
    """Get current version from install.py.

    Returns:
        Version string or "unknown"
    """
    install_script = get_script_dir() / "scripts" / "install.py"
    if not install_script.exists():
        return "unknown"

    try:
        content = install_script.read_text(encoding="utf-8")
        # Look for version in the install script
        match = re.search(r'"version"\s*:\s*"([\d.]+)"', content)
        if match:
            return match.group(1)

        # Fallback to print statement
        match = re.search(r'Global Claude Rules Installer v([\d.]+)', content)
        if match:
            return match.group(1)
    except (OSError, UnicodeDecodeError):
        pass

    return "unknown"


def check_git_repository() -> bool:
    """Check if current directory is a git repository.

    Returns:
        True if .git directory exists
    """
    script_dir = get_script_dir()
    git_dir = script_dir / ".git"
    return git_dir.exists() and git_dir.is_dir()


def get_git_remote() -> str | None:
    """Get the git remote URL.

    Returns:
        Remote URL or None
    """
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=get_script_dir()
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return None


def get_current_branch() -> str:
    """Get current git branch.

    Returns:
        Branch name or "unknown"
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=get_script_dir()
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return "unknown"


def get_local_commits_ahead() -> int:
    """Get number of local commits ahead of remote.

    Returns:
        Number of commits ahead
    """
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "@{u}..HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=get_script_dir()
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError, ValueError):
        pass

    return 0


def has_uncommitted_changes() -> bool:
    """Check if there are uncommitted changes.

    Returns:
        True if there are uncommitted changes
    """
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=get_script_dir()
        )
        if result.returncode == 0:
            return bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return False


def git_fetch() -> bool:
    """Fetch latest changes from remote.

    Returns:
        True if successful
    """
    try:
        print_info("Fetching latest changes from remote...")
        result = subprocess.run(
            ["git", "fetch", "origin"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=get_script_dir()
        )
        if result.returncode == 0:
            print_success("Fetched latest changes")
            return True
        else:
            print_error(f"Git fetch failed: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print_error(f"Git fetch error: {e}")
        return False


def get_commits_behind() -> list[str]:
    """Get commit messages for commits we're behind.

    Returns:
        List of commit messages
    """
    try:
        result = subprocess.run(
            ["git", "log", "@{u}..HEAD", "--oneline"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=get_script_dir()
        )

        # Actually we want the OTHER direction - commits on remote that we don't have
        result = subprocess.run(
            ["git", "log", "HEAD..@{u}", "--oneline"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=get_script_dir()
        )

        if result.returncode == 0:
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return []


def git_pull() -> bool:
    """Pull latest changes from remote.

    Returns:
        True if successful
    """
    try:
        print_info("Pulling latest changes...")
        result = subprocess.run(
            ["git", "pull", "origin", get_current_branch()],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=get_script_dir()
        )
        if result.returncode == 0:
            print_success("Pulled latest changes")
            return True
        else:
            print_error(f"Git pull failed: {result.stderr}")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print_error(f"Git pull error: {e}")
        return False


def run_install(force: bool = False, dry_run: bool = False) -> bool:
    """Run the install script to update global files.

    Args:
        force: Pass --force flag to install.py
        dry_run: Pass --dry-run flag to install.py

    Returns:
        True if successful
    """
    install_script = get_script_dir() / "scripts" / "install.py"

    if not install_script.exists():
        print_error(f"Install script not found: {install_script}")
        return False

    try:
        cmd = [sys.executable, str(install_script)]
        if force:
            cmd.append("--force")
        if dry_run:
            cmd.append("--dry-run")

        print_info(f"Running install script...")
        if dry_run:
            print_info(f"Command: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        # Print output
        if result.stdout:
            print(result.stdout)

        if result.returncode == 0:
            print_success("Installation completed")
            return True
        else:
            print_error(f"Installation failed: {result.stderr}")
            return False

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
        print_error(f"Install script error: {e}")
        return False


def get_changelog(since: str | None = None) -> list[str]:
    """Get changelog entries since a commit.

    Args:
        since: Commit hash to get changelog since (None for last 5)

    Returns:
        List of changelog entries
    """
    try:
        if since:
            result = subprocess.run(
                ["git", "log", f"{since}..HEAD", "--oneline", "--format=%s"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=get_script_dir()
            )
        else:
            result = subprocess.run(
                ["git", "log", "-5", "--oneline", "--format=%s"],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=get_script_dir()
            )

        if result.returncode == 0:
            return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return []


def check_update_needed(days_threshold: int = 7) -> tuple[bool, str]:
    """Check if an update is needed based on time since last update.

    Args:
        days_threshold: Days before update is recommended

    Returns:
        Tuple of (needs_update, last_update_date)
    """
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=get_script_dir()
        )

        if result.returncode == 0:
            # Parse date: 2024-01-15 10:30:00 +0000
            date_str = result.stdout.strip().split()[0]
            try:
                last_date = datetime.strptime(date_str, "%Y-%m-%d")
                days_since = (datetime.now() - last_date).days

                return days_since >= days_threshold, date_str
            except ValueError:
                pass

    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    return True, "unknown"


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update Global Claude Rules System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/update.py              # Full update (pull + install)
  python scripts/update.py --dry-run     # Preview changes
  python scripts/update.py --no-install  # Only pull, don't install
  python scripts/update.py --check       # Only check if update needed
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--no-install",
        action="store_true",
        help="Skip installation after pull"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check if update is needed"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Force installation even if no updates"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Days threshold before recommending update (default: 7)"
    )

    args = parser.parse_args()

    # Setup colors
    setup_colors()

    print_header("Global Claude Rules Update")

    # Get current version
    current_version = get_current_version()
    print_info(f"Current version: {current_version}")

    # Check if we're in a git repository
    if not check_git_repository():
        print_warning("Not in a git repository")
        print_info("To enable updates, clone this repository with git")
        return 0

    # Get git info
    remote = get_git_remote()
    branch = get_current_branch()

    if remote:
        print_info(f"Remote: {remote}")
    print_info(f"Branch: {branch}")

    # Check for uncommitted changes
    if has_uncommitted_changes():
        print_warning("You have uncommitted changes")
        response = input(f"  Continue anyway? [y/N]: ").strip().lower()
        if response not in ('y', 'yes'):
            print_info("Update cancelled")
            return 0

    # Check for local commits ahead
    commits_ahead = get_local_commits_ahead()
    if commits_ahead > 0:
        print_warning(f"You have {commits_ahead} local commit(s) ahead of remote")
        response = input(f"  Continue anyway? [y/N]: ").strip().lower()
        if response not in ('y', 'yes'):
            print_info("Update cancelled")
            return 0

    # Check if update is needed
    needs_update, last_update = check_update_needed(args.days)
    if args.check:
        if needs_update:
            print(f"Update recommended (last: {last_update})")
            return 1
        else:
            print(f"Update not needed (last: {last_update})")
            return 0

    print()

    # Fetch from remote
    if not git_fetch():
        print_error("Failed to fetch from remote")
        return 1

    # Check what's new
    commits_behind = get_commits_behind()
    if commits_behind and commits_behind != ['']:
        print_header("New Changes Available")
        for commit in commits_behind[:10]:
            print(f"  • {commit}")
        if len(commits_behind) > 10:
            print(f"  ... and {len(commits_behind) - 10} more")
        print()

        # Ask for confirmation
        if not args.dry_run:
            response = input(f"Apply {len(commits_behind)} update(s)? [Y/n]: ").strip().lower()
            if response in ('n', 'no'):
                print_info("Update cancelled")
                return 0
    else:
        print_success("Already up to date")
        if not args.force:
            print_info("Use --force to reinstall anyway")
            return 0

    if args.dry_run:
        print_header("Dry Run - No Changes Made")
        print_info("Run without --dry-run to apply updates")
        return 0

    # Pull changes
    if not git_pull():
        print_error("Failed to pull updates")
        return 1

    print_success("Repository updated")

    # Run install script
    if not args.no_install:
        print()
        if not run_install(force=True, dry_run=args.dry_run):
            print_error("Installation failed")
            return 1

    print_header("Update Complete")
    print_success("Global Claude Rules system updated")
    print()
    print_info("Start a new Claude Code session to use the updated rules")

    return 0


if __name__ == "__main__":
    sys.exit(main())
