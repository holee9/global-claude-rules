# Changelog

All notable changes to the Global Claude Rules System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `add_rule.py` - Interactive CLI tool for adding new ERR rules
- `validate_rules.py` - Rule validation tool with duplicate detection
- `update.py` - Auto-update script for multi-PC synchronization
- `pre_tool__enforce_rules.py` - Hook for showing relevant rules before tool execution
- Test infrastructure with `tests/` directory
- `CHANGELOG.md` for version history tracking

### Changed
- README.md updated with new CLI tools documentation
- Improved error rule format with Category field

### Fixed
- ERR-024: Hook Directory Not Found - added to template

## [1.4] - 2026-02-05

### Added
- ERR-022: Instruction Not Followed - Command Verification Required
- ERR-023: UTF-16 File Edit Failure
- ERR-024: Hook Directory Not Found
- Cross-platform installation support

### Changed
- Updated install.py for better cross-platform compatibility
- Improved SessionStart hook output format

## [1.3] - 2025-XX-XX

### Added
- ERR-600 through ERR-602 for MFC/Win32 errors
- MFC error category (ERR-600~ERR-699)

## [1.2] - 2025-XX-XX

### Added
- ERR-016: Hash Used as Comment Character
- ERR-015: Python Escape Sequence in SV Code
- ERR-014: Bare Comment Separator
- ERR-013: False Positive Syntax Detection
- ERR-012: Wrong Reset Signal Name
- ERR-011: Undeclared Signal Usage

### Fixed
- Improved rule formatting consistency

## [1.1] - 2025-XX-XX

### Added
- ERR-010: Unrealistic Module Size Goals
- ERR-009: Grep Pattern Not Matching
- ERR-008: TaskCreate Missing Parameter
- ERR-007: Undriven Signal
- ERR-006: Reset Polarity Inversion Bug
- ERR-005: Port Direction Mismatch
- ERR-004: File Path Not Found
- ERR-003: Edit Tool Hook Failure
- ERR-002: Hook Files Missing
- ERR-001: TodoWrite Tool Not Available

### Changed
- Initial rule set with ERR-001 through ERR-016

## [1.0] - 2025-XX-XX

### Added
- Initial release of Global Claude Rules System
- Cross-platform installer (install.py, install.ps1)
- SessionStart hook for auto-loading rules
- Global memory template
- Error Prevention System (EPS) with ERR-XXX format
- Quick reference table for common errors

---

## Version Summary

| Version | Date | ERR Rules | Key Features |
|---------|------|-----------|--------------|
| 1.5 | 2026-02-05 | 24+ | CLI tools, auto-update, pre-tool enforcement |
| 1.4 | 2026-02-05 | 24 | Cross-platform improvements |
| 1.3 | TBD | 21 | MFC/Win32 error support |
| 1.2 | TBD | 18 | SystemVerilog error support |
| 1.1 | TBD | 16 | FPGA/Hardware error support |
| 1.0 | TBD | 0 | Initial release |
