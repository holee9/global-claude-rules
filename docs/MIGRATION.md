# Migration Guide

**Version**: 1.0
**Date**: 2026-02-05

---

## Overview

This guide helps you migrate from a hardcoded-path installation to the new environment-aware installation.

---

## Before Migration

### Identify Your Current Setup

1. **Check your current hook file** for hardcoded paths:
   ```bash
   # Windows
   type %USERPROFILE%\.claude\hooks\moai\session_start__show_project_info.py | findstr "C:\\ D:\\"

   # Linux/macOS
   grep -n "C:/Users\|D:/" ~/.claude/hooks/moai/session_start__show_project_info.py
   ```

2. **Check your current memory.md location**:
   ```bash
   # Windows
   dir %USERPROFILE%\.claude\memory.md

   # Linux/macOS
   ls -la ~/.claude/memory.md
   ```

---

## Migration Steps

### Step 1: Backup Current Files

```bash
# Create backup directory
mkdir claude-backup

# Windows
copy %USERPROFILE%\.claude\memory.md claude-backup\
copy %USERPROFILE%\.claude\hooks\moai\session_start__show_project_info.py claude-backup\

# Linux/macOS
cp ~/.claude/memory.md claude-backup/
cp ~/.claude/hooks/moai/session_start__show_project_info.py claude-backup/
```

### Step 2: Extract Custom Rules

If you've added project-specific rules to your global memory:

1. Open your backup `memory.md`
2. Copy entries marked with your project name
3. Paste them into your project's `.claude/memory.md` or `doc/LESSONS_LEARNED.md`

### Step 3: Run New Installer

```bash
# Clone new repository
git clone https://github.com/user/global-claude-rules.git temp-install
cd temp-install

# Run installer
python scripts/install.py
```

### Step 4: Verify Installation

```bash
# Check files exist
ls ~/.claude/memory.md
ls ~/.claude/hooks/moai/session_start__show_project_info.py

# Verify no hardcoded paths in hook
grep -n "drake\\.lee\|C:\\/Users\\/drake" ~/.claude/hooks/moai/session_start__show_project_info.py
# Should return nothing (no hardcoded paths)
```

### Step 5: Test New Session

Start a new Claude Code session and verify:
- Session starts without errors
- Global memory summary appears: `📚 Global Memory: N error rules`
- Auto-loaded rules appear in system message

---

## Platform-Specific Notes

### Windows

**Default paths after migration:**
- Global Memory: `C:\Users\[username]\.claude\memory.md`
- Hook: `C:\Users\[username]\.claude\hooks\moai\session_start__show_project_info.py`
- Global Guide: `D:\GLOBAL_RULES_GUIDE.md` (if exists) or `C:\Users\[username]\.claude\GLOBAL_RULES_GUIDE.md`

**Environment variables (optional):**
```powershell
setx GLOBAL_CLAUDE_MEMORY "C:\Users\%USERNAME%\.claude\memory.md"
setx GLOBAL_CLAUDE_GUIDE "D:\GLOBAL_RULES_GUIDE.md"
```

### Linux/macOS

**Default paths after migration:**
- Global Memory: `~/.claude/memory.md`
- Hook: `~/.claude/hooks/moai/session_start__show_project_info.py`
- Global Guide: `~/.claude/GLOBAL_RULES_GUIDE.md`

**Environment variables (optional):**
```bash
# Add to ~/.bashrc or ~/.zshrc
export GLOBAL_CLAUDE_MEMORY="$HOME/.claude/memory.md"
export GLOBAL_CLAUDE_GUIDE="$HOME/.claude/GLOBAL_RULES_GUIDE.md"
```

---

## Rollback

If you need to rollback to your old setup:

```bash
# Restore from backup
cp claude-backup/memory.md ~/.claude/memory.md
cp claude-backup/session_start__show_project_info.py ~/.claude/hooks/moai/
```

---

## Troubleshooting

### Issue: Hook not loading

**Symptoms**: No global memory summary in session start

**Solution**:
1. Verify hook file exists at correct path
2. Check Python syntax: `python -m py_compile ~/.claude/hooks/moai/session_start__show_project_info.py`
3. Check Claude Code logs for errors

### Issue: Wrong user path detected

**Symptoms**: File not found errors for `[other_user]`

**Solution**:
```bash
# Set environment variable
export CLAUDE_CONFIG_DIR="$HOME/.claude"  # Linux/macOS
setx CLAUDE_CONFIG_DIR "C:\Users\YOUR_USERNAME\.claude"  # Windows
```

### Issue: Old guide path (D:/) not found

**Symptoms**: Warning about GLOBAL_RULES_GUIDE.md

**Solution**: The new system uses `~/.claude/GLOBAL_RULES_GUIDE.md` by default. Copy your guide there or set the environment variable.

---

## Success Checklist

After migration, verify:
- [ ] New hook file exists without hardcoded usernames
- [ ] Global memory.md exists in home directory
- [ ] New Claude Code session shows global memory summary
- [ ] No path-related errors in logs
- [ ] Custom rules preserved in project directories

---

## Next Steps

After successful migration:
1. Delete backup directory (after verification)
2. Set up environment variables if using custom paths
3. Add repository to git for easy updates
4. Document any project-specific rules separately
