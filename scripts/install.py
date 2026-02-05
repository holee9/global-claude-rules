#!/usr/bin/env python3
"""
Global Claude Rules Installation Script

Cross-platform installer for global Claude Code rules system.
Supports Windows, Linux, and macOS.

Usage:
    python scripts/install.py [--dry-run] [--force]
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path


# ANSI color codes for terminal output
class Colors:
    """ANSI color codes for cross-platform terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    @staticmethod
    def disable():
        """Disable colors (for Windows cmd.exe without ANSI support)."""
        Colors.HEADER = ''
        Colors.OKBLUE = ''
        Colors.OKCYAN = ''
        Colors.OKGREEN = ''
        Colors.WARNING = ''
        Colors.FAIL = ''
        Colors.ENDC = ''
        Colors.BOLD = ''
        Colors.UNDERLINE = ''


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


def get_script_dir() -> Path:
    """Get the directory where this script is located."""
    return Path(__file__).parent.parent.resolve()


def get_home_dir() -> Path:
    """Get the user's home directory."""
    return Path.home()


def get_claude_dir() -> Path:
    """Get the Claude Code configuration directory."""
    # Check environment variable first
    if env_dir := os.getenv("CLAUDE_CONFIG_DIR"):
        return Path(env_dir)
    # Default to home directory
    return get_home_dir() / ".claude"


def get_hooks_dir() -> Path:
    """Get the hooks directory."""
    return get_claude_dir() / "hooks" / "moai"


def setup_colors():
    """Setup colors based on platform and terminal support."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            # Enable ANSI colors on Windows 10+
        except (AttributeError, OSError):
            Colors.disable()


def check_existing_installation(claude_dir: Path, hooks_dir: Path) -> dict:
    """Check for existing installation files."""
    result = {
        "memory_md": (claude_dir / "memory.md").exists(),
        "hook_file": (hooks_dir / "session_start__show_project_info.py").exists(),
        "guide_file": (claude_dir / "GLOBAL_RULES_GUIDE.md").exists(),
    }
    return result


def prompt_overwrite(file_path: Path, force: bool = False) -> bool:
    """Prompt user to overwrite existing file."""
    if force:
        return True
    while True:
        response = input(f"  Overwrite {file_path}? [y/N]: ").strip().lower()
        if not response:
            return False
        if response in ('y', 'yes'):
            return True
        if response in ('n', 'no'):
            return False
        print_warning("Please enter 'y' or 'n'")


def render_template(content: str, variables: dict) -> str:
    """Replace template variables in content."""
    result = content
    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, str(value))
    return result


def install_memory_md(
    source_dir: Path,
    claude_dir: Path,
    variables: dict,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Install memory.md file."""
    source_file = source_dir / "templates" / "memory.md"
    target_file = claude_dir / "memory.md"

    if not source_file.exists():
        print_error(f"Source file not found: {source_file}")
        return False

    # Check if exists
    if target_file.exists():
        print_warning(f"Existing file: {target_file}")
        # Skip prompt in dry-run mode
        if not dry_run and not prompt_overwrite(target_file, force):
            print_info("Skipping memory.md")
            return True

    # Read and render template
    content = source_file.read_text(encoding="utf-8")
    rendered = render_template(content, variables)

    if dry_run:
        print_info(f"[DRY RUN] Would write: {target_file}")
        print_info(f"[DRY RUN] Size: {len(rendered)} bytes")
        return True

    # Write file
    target_file.write_text(rendered, encoding="utf-8")
    print_success(f"Installed: {target_file}")
    return True


def install_hook_file(
    source_dir: Path,
    hooks_dir: Path,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Install session_start hook file."""
    source_file = source_dir / "templates" / "session_start__show_project_info.py"
    target_file = hooks_dir / "session_start__show_project_info.py"

    if not source_file.exists():
        print_error(f"Source file not found: {source_file}")
        return False

    # Create hooks directory
    hooks_dir.mkdir(parents=True, exist_ok=True)

    # Check if exists
    if target_file.exists():
        print_warning(f"Existing file: {target_file}")
        # Skip prompt in dry-run mode
        if not dry_run and not prompt_overwrite(target_file, force):
            print_info("Skipping hook file")
            return True

    if dry_run:
        print_info(f"[DRY RUN] Would copy: {source_file} -> {target_file}")
        return True

    # Copy file (hook file doesn't need template rendering)
    shutil.copy2(source_file, target_file)
    print_success(f"Installed: {target_file}")
    return True


def install_guide_file(
    source_dir: Path,
    claude_dir: Path,
    variables: dict,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Install GLOBAL_RULES_GUIDE.md file."""
    source_file = source_dir / "templates" / "GLOBAL_RULES_GUIDE.md"
    target_file = claude_dir / "GLOBAL_RULES_GUIDE.md"

    if not source_file.exists():
        print_warning(f"Source file not found: {source_file} (optional)")
        return True

    # Check if exists
    if target_file.exists():
        print_warning(f"Existing file: {target_file}")
        # Skip prompt in dry-run mode
        if not dry_run and not prompt_overwrite(target_file, force):
            print_info("Skipping guide file")
            return True

    # Read and render template
    content = source_file.read_text(encoding="utf-8")
    rendered = render_template(content, variables)

    if dry_run:
        print_info(f"[DRY RUN] Would write: {target_file}")
        return True

    # Write file
    target_file.write_text(rendered, encoding="utf-8")
    print_success(f"Installed: {target_file}")
    return True


def install_hooks_directory(
    claude_dir: Path,
    target_hooks_dir: Path,
    dry_run: bool = False,
    force: bool = False,
) -> bool:
    """Install entire hooks directory from global Claude config to project.

    This copies all hooks from C:\Users\USERNAME\.claude\hooks\moai\ to
    the project's .claude/hooks/moai\ directory. This ensures projects
    have access to quality gates, code formatters, and other tooling.

    Args:
        claude_dir: Global Claude config directory (source of hooks)
        target_hooks_dir: Target hooks directory in project
        dry_run: Preview without copying
        force: Skip overwrite prompts

    Returns:
        True if successful, False otherwise
    """
    source_hooks_dir = claude_dir / "hooks" / "moai"

    # Check if source exists
    if not source_hooks_dir.exists():
        print_warning(f"Global hooks not found: {source_hooks_dir}")
        print_info("(This is normal if you haven't installed moai-adk globally)")
        return True  # Not a failure - hooks are optional

    # Check if target already exists
    if target_hooks_dir.exists():
        if not force:
            print_warning(f"Existing hooks directory: {target_hooks_dir}")
            if not prompt_overwrite(target_hooks_dir, False):
                print_info("Skipping hooks directory (use --force to overwrite)")
                return True

    if dry_run:
        print_info(f"[DRY RUN] Would copy hooks: {source_hooks_dir} -> {target_hooks_dir}")
        # Count files that would be copied
        if source_hooks_dir.exists():
            file_count = sum(1 for _ in source_hooks_dir.rglob("*") if _.is_file())
            print_info(f"[DRY RUN] Would copy {file_count} files")
        return True

    # Create target directory
    target_hooks_dir.mkdir(parents=True, exist_ok=True)

    # Copy all hooks
    try:
        # Remove existing hooks if force is enabled
        if force and target_hooks_dir.exists():
            shutil.rmtree(target_hooks_dir)
            target_hooks_dir.mkdir(parents=True, exist_ok=True)

        # Copy directory contents
        for item in source_hooks_dir.iterdir():
            src = item
            dst = target_hooks_dir / item.name
            if item.is_dir():
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        file_count = sum(1 for _ in target_hooks_dir.rglob("*") if _.is_file())
        print_success(f"Installed hooks directory: {file_count} files")
        return True

    except OSError as e:
        print_error(f"Failed to copy hooks: {e}")
        return False


def print_summary(claude_dir: Path, hooks_dir: Path):
    """Print installation summary."""
    print_header("Installation Summary")
    print(f"  Claude Config Dir: {claude_dir}")
    print(f"  Hooks Dir:         {hooks_dir}")
    print(f"  Memory File:       {claude_dir / 'memory.md'}")
    print(f"  Guide File:        {claude_dir / 'GLOBAL_RULES_GUIDE.md'}")
    print(f"  Hook File:         {hooks_dir / 'session_start__show_project_info.py'}")
    print()

    # Verify installation
    memory_exists = (claude_dir / "memory.md").exists()
    hook_exists = (hooks_dir / "session_start__show_project_info.py").exists()

    if memory_exists and hook_exists:
        print_success("Installation completed successfully!")
        print()
        print_info("Environment Variables (optional):")
        print(f"  export GLOBAL_CLAUDE_MEMORY={claude_dir / 'memory.md'}")
        print(f"  export GLOBAL_CLAUDE_GUIDE={claude_dir / 'GLOBAL_RULES_GUIDE.md'}")
        print()
        print_info("To verify installation, start a new Claude Code session.")
    else:
        print_error("Installation incomplete!")
        if not memory_exists:
            print_error("  - memory.md not installed")
        if not hook_exists:
            print_error("  - Hook file not installed")


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(
        description="Install Global Claude Rules System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/install.py           # Interactive installation
  python scripts/install.py --dry-run  # Preview without installing
  python scripts/install.py --force    # Overwrite existing files
        """
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without installing"
    )
    parser.add_argument(
        "--force",
        "-f",
        action="store_true",
        help="Overwrite existing files without prompting"
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Show version information"
    )

    args = parser.parse_args()

    # Show version
    if args.version:
        print("Global Claude Rules Installer v1.0.0")
        return 0

    # Setup colors
    setup_colors()

    # Print header
    print_header("Global Claude Rules Installation")

    # Get paths
    script_dir = get_script_dir()
    claude_dir = get_claude_dir()
    hooks_dir = get_hooks_dir()

    print_info(f"Script Directory: {script_dir}")
    print_info(f"Target Directory: {claude_dir}")
    print()

    # Template variables
    variables = {
        "DATE": datetime.now().strftime("%Y-%m-%d"),
        "VERSION": "1.4",
        "USER_HOME": str(get_home_dir()),
    }

    # Check existing installation
    existing = check_existing_installation(claude_dir, hooks_dir)
    if any(existing.values()):
        print_warning("Existing installation found:")
        if existing["memory_md"]:
            print(f"  - {claude_dir / 'memory.md'}")
        if existing["hook_file"]:
            print(f"  - {hooks_dir / 'session_start__show_project_info.py'}")
        if existing["guide_file"]:
            print(f"  - {claude_dir / 'GLOBAL_RULES_GUIDE.md'}")
        print()

    # Dry run mode
    if args.dry_run:
        print_warning("DRY RUN MODE - No files will be modified")
        print()

    # Install files
    success = True
    success &= install_memory_md(script_dir, claude_dir, variables, args.dry_run, args.force)
    success &= install_hook_file(script_dir, hooks_dir, args.dry_run, args.force)
    success &= install_guide_file(script_dir, claude_dir, variables, args.dry_run, args.force)

    # Install hooks directory (optional - for projects that need full tooling)
    print_info("\nInstalling hooks directory...")
    success &= install_hooks_directory(get_claude_dir(), hooks_dir, args.dry_run, args.force)

    # Print summary
    if not args.dry_run:
        print_summary(claude_dir, hooks_dir)
    else:
        print_header("Dry Run Summary")
        print_info("No files were modified. Run without --dry-run to install.")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
