### ERR-024: Hook Directory Not Found - PreToolUse/PostToolUse Failure
**Problem**: Hook execution fails with error: `PreToolUse:Write hook error: [uv run ...]: error: Failed to spawn: ... 지정된 경로를 찾을 수 없습니다 (os error 3)`
**Root Cause**: `.claude/hooks/moai/` directory does not exist in project. This happens when:
  - Project is cloned/created without running install script
  - Template project (like global-claude-rules) that distributes hooks but doesn't use them locally
  - Global settings.json expects hooks at `{{PROJECT_DIR}}.claude/hooks/moai/` but actual hooks are at global location
**Solution**:
  1. **Immediate fix**: Run install script to copy hooks to project
     ```bash
     python scripts/install.py --force
     ```
  2. **Alternative**: Manually copy hooks from global location
     ```bash
     cp -r C:/Users/USERNAME/.claude/hooks/moai .claude/hooks/
     ```
  3. **For template projects**: Add hooks to `.gitignore` and document in README that hooks are optional
**Prevention**:
  - Always run `install.py` after cloning any moai-adk based project
  - Verify hooks exist before starting work: `ls .claude/hooks/moai/`
  - For template/distribution projects: Document that hooks are distributed but not required
  - Global settings should use fallback: check if project hooks exist, if not use global hooks
**Date**: 2026-02-05
**Project**: global-claude-rules
**Category**: System/Configuration (ERR-001~099)
