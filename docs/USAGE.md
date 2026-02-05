# 사용 가이드 (Usage Guide)

Global Claude Rules System의日常 사용법을 설명합니다.

---

## 📋 목차

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
   📦 Version: 1.5.0
   🔄 Changes: 0
   🌿 Branch: main
   📚 Global Memory: 24 error rules (Last: 2026-02-05)

## 🌍 GLOBAL RULES (Auto-loaded from ~/.claude/memory.md)

## Common Errors Across All Projects (Claude Code Working)

### ERR-001: TodoWrite Tool Not Available
**Problem**: `TodoWrite tool not available` error
**Solution**: Use `TaskCreate`, `TaskUpdate`, `TaskList` instead
...
```

### 도구 실행 전 규칙 확인

PreToolUse Hook이 도구 실행 전에 관련 규칙을 표시합니다:

```
사용자: "파일 수정해줘"

🔒 Relevant ERR Rules for Write:
  • ERR-004: File Path Not Found
  • ERR-022: Instruction Not Followed

(Showing 2 of 5 relevant rules)
```

---

## 규칙 추가하기

새로운 에러를 발견하면 규칙으로 추가하세요.

### 방법 1: 대화형 모드 (권장)

```bash
cd global-claude-rules
python scripts/add_rule.py
```

**대화형 입력 예시:**

```
============================================================
                  Add New ERR Rule
============================================================

ℹ Please provide the following information for the new error rule.

Short Title: File Encoding Error

Problem Description:
  What went wrong? (Press Enter twice to finish)
  > Edit tool fails when editing UTF-16 files like .rc on Windows
  >

Root Cause:
  > Edit tool expects UTF-8 encoding, but Windows resource files use UTF-16 LE
  >

Solution:
  > Detect file encoding first, for UTF-16 use PowerShell with Get-Content -Encoding Unicode
  >

Prevention:
  > Always check file encoding before using Edit tool. For .rc, .res, .config files assume UTF-16 on Windows
  >

Project Name (optional): WindowsApp

Quick Solution (default: Detect file encoding first...):
Check encoding, use PowerShell for UTF-16 files

============================================================
                  New Rule Summary
============================================================
  ℹ Error ID: ERR-025
  ℹ Category: System/File Operations (ERR-001~ERR-099)
  ℹ Title: File Encoding Error

✓ Updated: templates/memory.md
✓ Updated: C:\Users\[user]\.claude\memory.md
✓ Git commit created: docs: Add ERR-025 File Encoding Error

============================================================
        Rule Added Successfully
============================================================
✓ ERR-025: File Encoding Error

ℹ To apply changes globally, run:
  python scripts/install.py --force
```

### 방법 2: 비대화형 모드

스크립트에서 사용하거나 CI/CD에 통합할 때 유용합니다:

```bash
python scripts/add_rule.py \
    --title "Import Path Error" \
    --problem "Relative import fails when script run from different directory" \
    --root-cause "Python relative imports depend on current working directory" \
    --solution "Use absolute imports or add module path to sys.path" \
    --prevention "Always use absolute imports for project modules" \
    --project "MyProject" \
    --quick-solution "Use absolute imports"
```

### 방법 3: Dry-Run (미리보기)

실제로 추가하지 않고 미리보기:

```bash
python scripts/add_rule.py --dry-run
```

---

## 규칙 검증하기

### 기본 검증

```bash
python scripts/validate_rules.py
```

### 특정 파일 검증

```bash
# 템플릿 파일 검증
python scripts/validate_rules.py --file templates/memory.md

# 전역 메모리 검증
python scripts/validate_rules.py --file ~/.claude/memory.md
```

### 상세 출력

```bash
python scripts/validate_rules.py --verbose
```

**출력 예시:**

```
============================================================
                  Validation Results
============================================================

⚠ Found 2 warning(s):

  ⚠ ERR-025: table (line 250)
    Rule not found in quick reference table

  ⚠ ERR-026: date (line 270)
    Date field is missing

============================================================
                       Summary
============================================================
  Total rules: 25
  Errors: 0
  Warnings: 2
```

### Quiet 모드 (에러만 표시)

```bash
python scripts/validate_rules.py --quiet
```

---

## 규칙 업데이트하기

### 자동 업데이트 (권장)

```bash
python scripts/update.py
```

**실행 과정:**

1. Git 원격 저장소에서 최신 변경사항 가져오기
2. 변경사항 요약 표시
3. 확인 후 변경사항 적용 (git pull)
4. 자동 재설치 (install.py --force)

```
============================================================
          Global Claude Rules Update
============================================================
ℹ Current version: 1.5.0
ℹ Remote: https://github.com/YOUR-USERNAME/global-claude-rules.git
ℹ Branch: main

ℹ Fetching latest changes from remote...
✓ Fetched latest changes

============================================================
              New Changes Available
============================================================
  • abc1234 Add ERR-025: File Encoding Error
  • def5678 Add ERR-026: Import Path Error
  • ghi9012 Fix validation script

Apply 3 update(s)? [Y/n]: Y

ℹ Pulling latest changes...
✓ Pulled latest changes

ℹ Running install script...
✓ Installed: C:\Users\[user]\.claude\memory.md
✓ Installation completed

============================================================
            Update Complete
============================================================
✓ Global Claude Rules system updated

ℹ Start a new Claude Code session to use the updated rules
```

### 업데이트 확인만 하기

실제 업데이트 없이 확인만:

```bash
python scripts/update.py --check
```

### Dry-Run

변경사항 미리보기:

```bash
python scripts/update.py --dry-run
```

### Pull만 하기 (재설치 없음)

```bash
python scripts/update.py --no-install
```

---

## 다중 PC 동기화

### 워크플로우

```
┌─────────────┐                    ┌─────────────┐
│    PC 1     │                    │    PC 2     │
│  (Office)   │                    │   (Home)    │
└──────┬──────┘                    └──────┬──────┘
       │                                  │
       │ 1. Add new rule                  │
       │ 2. Commit & Push                 │
       │                                  │
       │────────── Git Push ──────────────>│
       │                                  │
       │                          3. Pull
       │                          4. Update
       │                                  │
       │<───────── Rule Synced ───────────│
       │                                  │
       │      Both PCs have same rules    │
```

### PC 1: 규칙 추가 후 공유

```bash
# 1. 규칙 추가
python scripts/add_rule.py

# 2. 변경사항 확인
git status

# 3. 커밋
git add templates/memory.md
git commit -m "Add ERR-027: New error rule"

# 4. 푸시
git push origin main
```

### PC 2: 업데이트 받기

```bash
# 1. 업데이트 스크립트 실행
python scripts/update.py

# 또는 수동으로:
# git pull
# python scripts/install.py --force
```

### 충돌 해결

양쪽 PC에서 동시에 규칙을 추가한 경우:

```bash
# 1. 원격 변경사항 가져오기
git fetch origin

# 2. 리베이스 (선택사항)
git rebase origin/main

# 3. 충돌 해결 후
git add templates/memory.md
git rebase --continue

# 4. 푸시
git push origin main
```

---

## 일일 워크플로우

### 새 프로젝트 시작할 때

```
1. Claude Code 세션 시작
   ↓
2. 자동으로 전역 규칙 로딩됨
   ↓
3. 프로젝트 특정 규칙 확인 (.claude/memory.md)
   ↓
4. 작업 시작
```

### 에러 발생했을 때

```
1. 에러 문서화 (규칙 추가)
   ↓
2. python scripts/add_rule.py
   ↓
3. 검증: python scripts/validate_rules.py
   ↓
4. 커밋: git add/commit/push
   ↓
5. 다른 PC에서 업데이트: python scripts/update.py
```

### 정기 유지보수

```
주간:
- python scripts/update.py (업데이트 확인)
- python scripts/validate_rules.py (규칙 검증)

월간:
- 새 규칙 검토
- 더 이상 유효하지 않은 규칙 제료/업데이트
```

---

## CLI 도구 레퍼런스

### add_rule.py

| 옵션 | 설명 |
|------|------|
| `--non-interactive` | 비대화형 모드 |
| `--title` | 에러 제목 |
| `--problem` | 문제 설명 |
| `--root-cause` | 근본 원인 |
| `--solution` | 해결 방법 |
| `--prevention` | 예방 방법 |
| `--project` | 프로젝트 이름 |
| `--quick-solution` | 빠른 해결 방법 요약 |
| `--no-commit` | Git 커밋 건너뛰기 |
| `--dry-run` | 미리보기 |

### validate_rules.py

| 옵션 | 설명 |
|------|------|
| `--file`, `-f` | 검증할 파일 경로 |
| `--verbose`, `-v` | 상세 출력 |
| `--quiet`, `-q` | 에러만 표시 |

### update.py

| 옵션 | 설명 |
|------|------|
| `--dry-run` | 변경사항 미리보기 |
| `--no-install` | 설치 건너뛰기 (pull만) |
| `--check` | 업데이트 필요 여부만 확인 |
| `--force`, `-f` | 강제 재설치 |
| `--days` | 업데이트 권장 일수 (기본: 7) |

---

## 팁과 모범 사례

### 규칙 추가 팁

1. **구체적으로 작성**
   - ❌ "파일 에러"
   - ✅ "Edit tool fails when file path uses forward slashes on Windows"

2. **재현 가능하게**
   - 문제 상황을 명확히 설명
   - 실제 코드/명령어 예시 포함

3. **예방 중심**
   - "해결방법"뿐만 아니라 "예방방법"도 필수
   - 다음번 같은 에러를 방지하는 방법

### 규칙 번호 할당

자동으로 할당되지만, 카테고리를 참고하세요:

| 범위 | 카테고리 | 예시 |
|------|----------|------|
| 001-099 | General/System | ERR-001: TodoWrite unavailable |
| 100-199 | Git/Version | ERR-100: Git merge conflict |
| 200-299 | Build/Compile | ERR-200: Linker error |
| 300-399 | FPGA/Hardware | ERR-300: Timing violation |
| 400-499 | Backend/API | ERR-400: API rate limit |
| 500-599 | Frontend/UI | ERR-500: React render error |
| 600-699 | MFC/Win32 | ERR-600: MFC assertion |

---

## 다음 단계

- **[기여 가이드](CONTRIBUTING.md)** - 규칙 제출 방법
- **[설치 가이드](SETUP.md)** - 설치 문제 해결

---

**마지막 업데이트**: 2026-02-05
