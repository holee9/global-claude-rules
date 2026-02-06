# 사용 가이드 (Usage Guide)

**Version**: 1.6.0
**Last Updated**: 2026-02-06

---

## Table of Contents

1. [기본 사용법](#기본-사용법)
2. [규칙 추가하기](#규칙-추가하기)
3. [규칙 검증하기](#규칙-검증하기)
4. [규칙 업데이트하기](#규칙-업데이트하기)
5. [다중 PC 동기화](#다중-pc-동기화)
6. [일일 워크플로우](#일일-워크플로우)

---

## 기본 사용법

### Claude Code에서 규칙 자동 로딩

세션을 시작하면 규칙이 자동으로 로딩됩니다:

```
🚀 MoAI-ADK Session Started
   📦 Version: 1.6.0
   🔄 Changes: 0
   🌿 Branch: main
   📚 Global Memory: 24 error rules (Last: 2026-02-06)
```

### Pre-Tool 규칙 확인

도구 실행 전 관련 규칙이 자동으로 표시됩니다:

```
🔍 Relevant Rules for: Edit
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ERR-003: Edit Tool Hook Failure
→ Use Bash + Python/sed for file editing when Edit fails

ERR-004: File Path Not Found
→ Use Glob tool to verify file paths first
```

### 전역 메모리 직접 확인

```bash
# Linux/macOS
cat ~/.claude/memory.md

# Windows
type %USERPROFILE%\.claude\memory.md
```

---

## 규칙 추가하기

### 방법 1: 대화형 CLI (권장)

```bash
python scripts/add_rule.py
```

**입력 예시:**
```
Add New ERR Rule

Short Title: File Path Not Found

Problem Description:
  What went wrong? (Press Enter twice to finish)
  > Edit tool failed because file didn't exist at assumed path
  >

Root Cause:
  > Assumed path without verification
  >

Solution:
  > Use Glob tool to verify file paths first
  >

Prevention:
  > Always use Glob to confirm file locations in new projects
  >

Category (1-7):
  1. General/System (ERR-001~ERR-099)
  2. Git/Version Control (ERR-100~ERR-199)
  3. Build/Compilation (ERR-200~ERR-299)
  4. FPGA/Hardware (ERR-300~ERR-399)
  5. Backend/API (ERR-400~ERR-499)
  6. Frontend/UI (ERR-500~ERR-599)
  7. MFC/Win32 (ERR-600~ERR-699)
  > 1

✓ ERR-025: File Path Not Found added successfully!

Files updated:
  - templates/memory.md
  - ~/.claude/memory.md

Commit changes? (y/n) > y
✓ Created git commit: Add ERR-025: File Path Not Found
```

### 방법 2: 비대화형 모드

```bash
python scripts/add_rule.py --non-interactive \
  --title "Module Import Error" \
  --problem "Failed to import local module" \
  --cause "Python path not set correctly" \
  --solution "Add PYTHONPATH environment variable" \
  --prevention "Always check sys.path in development" \
  --category 1
```

### 방법 3: 수동 추가 (고급)

`templates/memory.md`을 직접 편집:

```markdown
### ERR-XXX: [Short Title]

**Problem**: [Description]
**Root Cause**: [Why it happened]
**Solution**: [How to fix]
**Prevention**: [How to avoid in future]
**Date**: YYYY-MM-DD
**Project**: [Project name]
**Category**: [Category name] (ERR-XXX~ERR-XXX)
```

---

## 규칙 검증하기

### 기본 검증

```bash
python scripts/validate_rules.py
```

**출력:**
```
============================================================
           Global Claude Rules Validator
============================================================

✓ Found 24 error rules
✓ No duplicates
✓ All required fields present
✓ All dates valid (YYYY-MM-DD)
✓ All categories within valid ranges

Result: VALID (0 errors, 0 warnings)
```

### 상세 검증

```bash
python scripts/validate_rules.py --verbose
```

### 특정 파일 검증

```bash
python scripts/validate_rules.py --file templates/memory.md
```

### 검증 항목

| 항목 | 설명 |
|------|------|
| 중복 ERR ID | 같은 ID가 두 번 이상 사용되지 않음 |
| 필수 필드 | Problem, Root Cause, Solution, Prevention 존재 |
| 날짜 형식 | YYYY-MM-DD 형식 유효성 |
| 카테고리 범위 | ERR ID가 카테고리 범위 내 |
| Quick Reference | 참조 테이블과 실제 규칙 일치 |

---

## 규칙 업데이트하기

### 자동 업데이트

```bash
python scripts/update.py
```

이 명령은 다음을 수행합니다:
1. Git 저장소에서 최신 변경사항 가져오기
2. `templates/memory.md` 업데이트
3. `~/.claude/memory.md` 업데이트
4. Hook 파일 업데이트

### 수동 업데이트

```bash
# 1. 저장소에서 최신 코드 가져오기
git pull

# 2. 설치 스크립트 재실행
python scripts/install.py --force
```

### 업데이트 옵션

```bash
# 드라이런 (변경사항만 확인)
python scripts/update.py --dry-run

# 특정 브랜치에서 업데이트
python scripts/update.py --branch develop

# 도움말
python scripts/update.py --help
```

---

## 다중 PC 동기화

### PC 1: 규칙 추가 및 푸시

```bash
# 1. 규칙 추가
python scripts/add_rule.py

# 2. Git 커밋
cd global-claude-rules
git add templates/memory.md
git commit -m "Add ERR-025: File Path Not Found"

# 3. 푸시
git push
```

### PC 2: 규칙 가져오기

```bash
# 1. 변경사항 가져오기
cd global-claude-rules
git pull

# 2. 로컬 설치 업데이트
python scripts/update.py
```

### Git 원격 저장소 설정

```bash
# 원격 저장소 추가
git remote add origin https://github.com/YOUR-USERNAME/global-claude-rules.git

# 또는 변경
git remote set-url origin https://github.com/YOUR-USERNAME/global-claude-rules.git
```

---

## 일일 워크플로우

### 개발자 일일 루틴

```
┌─────────────────────────────────────────────────────────────┐
│  1. 아침: 최신 규칙 업데이트                                 │
│     $ cd global-claude-rules && git pull                    │
│     $ python scripts/update.py                              │
├─────────────────────────────────────────────────────────────┤
│  2. 작업 중: 에러 발생시 규칙 추가                          │
│     $ python scripts/add_rule.py                            │
├─────────────────────────────────────────────────────────────┤
│  3. 저녁: 변경사항 커밋 및 푸시                             │
│     $ git add templates/memory.md                          │
│     $ git commit -m "Add ERR-XXX: ..."                     │
│     $ git push                                             │
└─────────────────────────────────────────────────────────────┘
```

### 에러 발생시 대응 절차

```
에러 발생
    ↓
문서화 필요성 확인
    ↓
┌─────────────┬─────────────┐
│  새로운 에러 │  반복 에러  │
└─────────────┴─────────────┘
       ↓             ↓
  규칙 추가      기존 규칙 검토
       ↓             ↓
  add_rule.py   Prevention 개선
       ↓             ↓
  커밋/푸시     커밋/푸시
```

---

## CLI 도구 참조

### add_rule.py

```bash
python scripts/add_rule.py [OPTIONS]

Options:
  --non-interactive    비대화형 모드
  --title TEXT         에러 제목
  --problem TEXT       문제 설명
  --cause TEXT         원인
  --solution TEXT      해결책
  --prevention TEXT    예방 방법
  --category INT       카테고리 (1-7)
  --no-commit          git 커밋 생성 안 함
  --help               도움말
```

### validate_rules.py

```bash
python scripts/validate_rules.py [OPTIONS]

Options:
  --file PATH        검증할 파일 경로
  --verbose          상세 출력
  --help             도움말
```

### update.py

```bash
python scripts/update.py [OPTIONS]

Options:
  --dry-run          변경사항만 확인
  --branch TEXT      업데이트할 브랜치
  --help             도움말
```

### uninstall.py

```bash
python scripts/uninstall.py [OPTIONS]

Options:
  --keep-memory      메모리 파일 유지
  --help             도움말
```

---

## 팁 모음

### 규칙 작성 팁

1. **제목은 간결하게**: "File Not Found" > "File was not found at the specified location"
2. **원인은 근본적으로**: 직접 원인이 아니라 근본 원인을 설명
3. **해결책은 실행 가능하게**: "fix it" > "rename function X to Y"
4. **예방은 시스템적으로**: "be careful" > "use checklist before commit"

### 카테고리 선택 팁

| 상황 | 카테고리 |
|------|----------|
| Claude Code 작업 에러 | ERR-001~099 |
| Git 관련 | ERR-100~199 |
| 빌드/컴파일 | ERR-200~299 |
| 하드웨어/FPGA | ERR-300~399 |
| API/백엔드 | ERR-400~499 |
| 프론트엔드 | ERR-500~599 |
| Windows/MFC | ERR-600~699 |

---

**버전**: 1.6.0 | **최종 업데이트**: 2026-02-06
