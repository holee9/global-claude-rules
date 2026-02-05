#!/usr/bin/env python3
"""
Global Claude Rules Uninstallation Script

Removes installed global Claude Code rules files.
Use with caution - this will delete your configuration files!

Usage:
    python scripts/uninstall.py [--dry-run] [--keep-memory]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    OKCYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str):
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{'=' * 60}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{Colors.BOLD}{'=' * 60}{Colors.ENDC}\n")


def print_success(text: str):
    print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")


def print_error(text: str):
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")


def print_warning(text: str):
    print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")


def print_info(text: str):
    print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")


def get_claude_dir() -> Path:
    """Get the Claude Code configuration directory."""
    if env_dir := os.getenv("CLAUDE_CONFIG_DIR"):
        return Path(env_dir)
    return Path.home() / ".claude"


def get_hooks_dir() -> Path:
    """Get the hooks directory."""
    return get_claude_dir() / "hooks" / "moai"


def confirm_action(prompt: str, default: bool = False) -> bool:
    """Ask user for confirmation."""
    while True:
        suffix = " [Y/n]" if default else " [y/N]"
        response = input(f"{prompt}{suffix}: ").strip().lower()
        if not response:
            return default
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print_warning("Please enter 'y' or 'n'")


def remove_file(file_path: Path, dry_run: bool = False) -> bool:
    """Remove a single file."""
    if not file_path.exists():
        print_info(f"Not found: {file_path}")
        return True

    if dry_run:
        print_info(f"[DRY RUN] Would remove: {file_path}")
        return True

    try:
        file_path.unlink()
        print_success(f"Removed: {file_path}")
        return True
    except OSError as e:
        print_error(f"Failed to remove {file_path}: {e}")
        return False


def remove_directory(dir_path: Path, dry_run: bool = False) -> bool:
    """Remove a directory if empty."""
    if not dir_path.exists():
        return True

    if not list(dir_path.iterdir()):
        # Directory is empty
        if dry_run:
            print_info(f"[DRY RUN] Would remove empty directory: {dir_path}")
            return True

        try:
            dir_path.rmdir()
            print_success(f"Removed empty directory: {dir_path}")
        except OSError:
            pass  # Non-critical

    return True


def main():
    """Main uninstallation function."""
    parser = argparse.ArgumentParser(
        description="Uninstall Global Claude Rules System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/uninstall.py           # Interactive uninstall
  python scripts/uninstall.py --dry-run  # Preview without removing
  python scripts/uninstall.py --keep-memory  # Keep memory.md file
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without removing files"
    )
    parser.add_argument(
        "--keep-memory",
        action="store_true",
        help="Keep memory.md file (only remove hook)"
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    # Print header
    print_header("Global Claude Rules Uninstallation")

    # Get paths
    claude_dir = get_claude_dir()
    hooks_dir = get_hooks_dir()

    memory_file = claude_dir / "memory.md"
    hook_file = hooks_dir / "session_start__show_project_info.py"
    guide_file = claude_dir / "GLOBAL_RULES_GUIDE.md"

    # Show what will be removed
    print_warning("The following files will be removed:")
    if memory_file.exists():
        print(f"  - {memory_file}")
    if hook_file.exists():
        print(f"  - {hook_file}")
    if guide_file.exists():
        print(f"  - {guide_file}")
    print()

    # Confirm
    if not args.yes and not args.dry_run:
        if not confirm_action("Continue with uninstallation?", default=False):
            print_info("Uninstallation cancelled.")
            return 0

    # Dry run mode
    if args.dry_run:
        print_warning("DRY RUN MODE - No files will be removed")
        print()

    # Remove files
    success = True

    if not args.keep_memory:
        if memory_file.exists():
            success &= remove_file(memory_file, args.dry_run)
        else:
            print_info(f"Not found: {memory_file}")

    if hook_file.exists():
        success &= remove_file(hook_file, args.dry_run)
    else:
        print_info(f"Not found: {hook_file}")

    if guide_file.exists():
        # Ask about guide file separately
        if not args.yes and not args.dry_run:
            if not confirm_action("Remove GLOBAL_RULES_GUIDE.md?", default=False):
                print_info("Keeping guide file")
            else:
                success &= remove_file(guide_file, args.dry_run)
        else:
            success &= remove_file(guide_file, args.dry_run)
    else:
        print_info(f"Not found: {guide_file}")

    # Clean up empty directories
    if not args.dry_run:
        remove_directory(hooks_dir)
        remove_directory(claude_dir / "hooks")

    # Print summary
    print()
    if success:
        print_success("Uninstallation completed!")
        if args.keep_memory:
            print_info(f"Kept: {memory_file}")
        print_info("To reinstall, run: python scripts/install.py")
    else:
        print_error("Uninstallation encountered errors.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
