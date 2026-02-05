# Global Claude Rules System

**Version**: 1.4
**Date**: 2026-02-05
**License**: MIT

Cross-platform global error prevention rules system for Claude Code. Automatically loads common error patterns (ERR-001~ERR-016) at session start to prevent repeated mistakes across all projects.

---

## Features

- ✅ **Cross-platform**: Windows, Linux, macOS support
- ✅ **Environment-aware**: Automatic path detection based on OS
- ✅ **Template-based**: Easy customization with variable substitution
- ✅ **Auto-loading**: Core rules automatically injected via SessionStart hook
- ✅ **Extensible**: Add project-specific rules alongside global rules
- ✅ **Version-controlled**: Git-based distribution and updates

---

## Quick Start

### Windows

```powershell
# Clone and install
git clone https://github.com/user/global-claude-rules.git temp-install
cd temp-install
.\scripts\install.ps1
```

### Linux/macOS

```bash
# Clone and install
git clone https://github.com/user/global-claude-rules.git temp-install
cd temp-install
python3 scripts/install.py
```

---

## Directory Structure

```
global-claude-rules/
├── templates/
│   ├── memory.md                           # Global memory template
│   ├── GLOBAL_RULES_GUIDE.md               # User guide template
│   └── session_start__show_project_info.py # Hook with environment detection
├── scripts/
│   ├── install.py                          # Cross-platform installer
│   ├── install.ps1                         # Windows installer
│   └── uninstall.py                        # Uninstaller (TODO)
├── docs/
│   └── MIGRATION.md                        # Migration guide
├── README.md
└── .gitignore
```

---

## Installation

### Method 1: Automatic Installation (Recommended)

The installer script will:
1. Detect your platform and home directory
2. Create necessary directories (`~/.claude/hooks/moai/`)
3. Install template files with path customization
4. Preserve existing files unless `--force` is used

**Options:**
```bash
# Interactive installation
python scripts/install.py

# Dry-run (preview changes)
python scripts/install.py --dry-run

# Force overwrite
python scripts/install.py --force
```

### Method 2: Manual Installation

1. Copy `templates/memory.md` to `~/.claude/memory.md`
2. Copy `templates/session_start__show_project_info.py` to `~/.claude/hooks/moai/`
3. (Optional) Copy `templates/GLOBAL_RULES_GUIDE.md` to `~/.claude/`

---

## Configuration

### Environment Variables (Optional)

| Variable | Purpose | Default |
|----------|---------|---------|
| `GLOBAL_CLAUDE_MEMORY` | Override memory.md path | `~/.claude/memory.md` |
| `GLOBAL_CLAUDE_GUIDE` | Override guide path | `D:/GLOBAL_RULES_GUIDE.md` (Win) or `~/.claude/GLOBAL_RULES_GUIDE.md` (Unix) |
| `CLAUDE_CONFIG_DIR` | Override .claude directory | `~/.claude` |

**Example (Windows):**
```powershell
setx GLOBAL_CLAUDE_MEMORY "C:\Users\username\.claude\memory.md"
```

**Example (Linux/macOS):**
```bash
export GLOBAL_CLAUDE_MEMORY="$HOME/.claude/memory.md"
```

---

## File Locations

### Default Paths by Platform

| File | Windows | Linux/macOS |
|------|---------|-------------|
| Global Memory | `C:\Users\[user]\.claude\memory.md` | `~/.claude/memory.md` |
| Hook File | `C:\Users\[user]\.claude\hooks\moai\session_start__show_project_info.py` | `~/.claude/hooks/moai/session_start__show_project_info.py` |
| Global Guide | `D:\GLOBAL_RULES_GUIDE.md` or `~/.claude\GLOBAL_RULES_GUIDE.md` | `~/.claude/GLOBAL_RULES_GUIDE.md` |

---

## Error Categories

| ID Range | Category | Description |
|----------|----------|-------------|
| ERR-001 ~ ERR-099 | General/System | Claude Code working errors |
| ERR-100 ~ ERR-199 | Git/Version Control | Version control errors |
| ERR-200 ~ ERR-299 | Build/Compilation | Build and compilation errors |
| ERR-300 ~ ERR-399 | FPGA/Hardware | Hardware development errors |
| ERR-400 ~ ERR-499 | Backend/API | Server-side errors |
| ERR-500 ~ ERR-599 | Frontend/UI | Client-side errors |
| ERR-600 ~ ERR-699 | MFC/Win32 | Windows API errors |

---

## Verification

After installation, verify by starting a new Claude Code session. You should see:

```
🚀 MoAI-ADK Session Started
   📦 Version: X.X.X (latest)
   🔄 Changes: N
   🌿 Branch: main
   ...
   📚 Global Memory: 23 error rules (Last: 2026-02-05)
```

---

## Updating

```bash
# Pull latest changes
cd global-claude-rules
git pull

# Re-run installer
python scripts/install.py --force
```

---

## Migration from Old Setup

If you have an existing installation with hardcoded paths:

1. **Backup** your current `~/.claude/memory.md`
2. **Run** the new installer: `python scripts/install.py`
3. **Verify** paths are correct using environment detection
4. **Remove** old hardcoded path references if needed

See `docs/MIGRATION.md` for detailed migration guide.

---

## Uninstallation

```bash
python scripts/uninstall.py
```

Or manually remove:
- `~/.claude/memory.md`
- `~/.claude/hooks/moai/session_start__show_project_info.py`
- `~/.claude/GLOBAL_RULES_GUIDE.md` (optional)

---

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add new error rules following the template
4. Submit a pull request

**Error Template:**
```markdown
### ERR-XXX: [Short Title]

**Problem**: [Description]
**Root Cause**: [Why it happened]
**Solution**: [How to fix]
**Prevention**: [How to avoid in future]
**Date**: YYYY-MM-DD
**Project**: [Project name]
```

---

## License

MIT License - feel free to use, modify, and distribute.

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/user/global-claude-rules/issues
- Documentation: See `templates/GLOBAL_RULES_GUIDE.md`
