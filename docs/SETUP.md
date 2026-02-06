# 설치 가이드 (Setup Guide)

**Version**: 1.6.0
**Last Updated**: 2026-02-06

---

## Table of Contents

1. [시스템 요구사항](#시스템-요구사항)
2. [설치 방법](#설치-방법)
3. [검증](#검증)
4. [환경 변수 설정](#환경-변수-설정)
5. [선택적 기능](#선택적-기능)
6. [문제 해결](#문제-해결)

---

## 시스템 요구사항

### 필수 요구사항

| 요구사항 | 최소 사양 | 권장 사양 |
|---------|----------|----------|
| Python | 3.10+ | 3.12+ |
| OS | Windows 10+, Linux, macOS | 최신 LTS |
| Claude Code | 최신 버전 | 최신 버전 |
| Git | 2.0+ | 2.30+ |
| 디스크 공간 | 50MB | 100MB |

### Python 확인

```bash
# Python 버전 확인
python --version
# 또는
python3 --version

# 3.10 이상이어야 합니다
```

---

## 설치 방법

### 방법 1: 저장소 복제 후 설치 (권장)

```bash
# 1. 저장소 복제
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules

# 2. 설치 스크립트 실행
python scripts/install.py
```

### 방법 2: ZIP 다운로드 후 설치

1. GitHub에서 ZIP 다운로드
2. 압축 해제
3. 디렉토리에서 설치 스크립트 실행

```bash
cd global-claude-rules
python scripts/install.py
```

### 설치 옵션

```bash
# 기본 설치 (대화형)
python scripts/install.py

# 강제 설치 (프롬프트 건너뛰기)
python scripts/install.py --force

# 드라이런 (설치하지 않고 확인만)
python scripts/install.py --dry-run

# 도움말
python scripts/install.py --help
```

### 설치 과정

설치 스크립트는 다음을 수행합니다:

1. Claude 설정 디렉토리 확인 (`~/.claude`)
2. Hooks 디렉토리 생성 (`~/.claude/hooks/moai/`)
3. 전역 메모리 파일 설치 (`~/.claude/memory.md`)
4. SessionStart Hook 설치
5. PreTool Hook 설치 (규칙 강제)
6. 템플릿 변수 치환

```
============================================================
              Global Claude Rules Installer
============================================================

✓ Detected Script Directory
✓ Detected Target Directory
✓ Creating hooks directory...
✓ Installing memory.md...
✓ Installing session_start hook...
✓ Installing pre_tool hook...
✓ Installation complete!

Next steps:
1. Start a new Claude Code session
2. Check for "Global Memory: N error rules" message
3. Verify rules are loaded automatically
```

---

## 검증

### 1. 파일 존재 확인

```bash
# Windows
dir %USERPROFILE%\.claude\memory.md
dir %USERPROFILE%\.claude\hooks\moai\

# Linux/macOS
ls -la ~/.claude/memory.md
ls -la ~/.claude/hooks/moai/
```

### 2. Claude Code 세션 시작

새 Claude Code 세션을 시작하면 다음 메시지가 표시되어야 합니다:

```
🚀 MoAI-ADK Session Started
   📦 Version: 1.6.0
   🔄 Changes: 0
   🌿 Branch: main
   📚 Global Memory: 24 error rules (Last: 2026-02-06)
```

### 3. ERR 규칙 개수 확인

```bash
# ERR 규칙 개수 세기
grep -c "### ERR-" ~/.claude/memory.md

# 또는 (Windows)
findstr /C:"### ERR-" %USERPROFILE%\.claude\memory.md
```

### 4. Hook 파일 검증

```bash
# Python 문법 확인
python -m py_compile ~/.claude/hooks/moai/session_start__show_project_info.py
python -m py_compile ~/.claude/hooks/moai/pre_tool__enforce_rules.py

# 오류가 없으면 성공
```

---

## 환경 변수 설정

### 기본 경로

설치 후 파일 위치:

| 플랫폼 | 전역 메모리 | Hook 파일 |
|--------|-------------|-----------|
| Windows | `C:\Users\[user]\.claude\memory.md` | `C:\Users\[user]\.claude\hooks\moai\` |
| Linux/macOS | `~/.claude/memory.md` | `~/.claude/hooks/moai/` |

### 환경 변수 오버라이드

필요한 경우 환경 변수로 경로를 재정의할 수 있습니다.

**Windows (PowerShell):**
```powershell
# 영구 설정
setx CLAUDE_CONFIG_DIR "C:\Users\%USERNAME%\.claude"
setx GLOBAL_CLAUDE_MEMORY "C:\Users\%USERNAME%\.claude\memory.md"
setx GLOBAL_CLAUDE_GUIDE "D:\GLOBAL_RULES_GUIDE.md"

# 현재 세션에만 적용
$env:CLAUDE_CONFIG_DIR = "C:\Users\$env:USERNAME\.claude"
```

**Linux/macOS (bash/zsh):**
```bash
# ~/.bashrc 또는 ~/.zshrc에 추가
export CLAUDE_CONFIG_DIR="$HOME/.claude"
export GLOBAL_CLAUDE_MEMORY="$HOME/.claude/memory.md"
export GLOBAL_CLAUDE_GUIDE="$HOME/.claude/GLOBAL_RULES_GUIDE.md"

# 변경 사항 적용
source ~/.bashrc  # 또는 source ~/.zshrc
```

---

## 선택적 기능

### 시맨틱 매칭 (Semantic Matching)

AI 기반 의미적 규칙 검색을 위해 추가 의존성을 설치하세요.

#### 기본 설치 (CPU)

```bash
pip install sentence-transformers numpy faiss-cpu
```

#### GPU 가속

```bash
pip install sentence-transformers[gpu] faiss-gpu
```

#### 의존성 요구사항

| 패키지 | 최소 버전 | 용도 |
|--------|----------|------|
| sentence-transformers | 2.3.0 | 임베딩 생성 |
| numpy | 1.24.0 | 벡터 연산 |
| faiss-cpu | 1.7.4 | 벡터 검색 (CPU) |
| faiss-gpu | 1.7.4 | 벡터 검색 (GPU) |

#### 시맨틱 매칭 검증

```bash
# Python으로 테스트
python -c "
from sentence_transformers import SentenceTransformer
print('Semantic matching available!')
"
```

의존성이 설치되지 않은 경우 자동으로 기존 키워드 매칭으로 폴백됩니다.

---

## 문제 해결

### 문제: Python 모듈 없음

```
ModuleNotFoundError: No module named 'sentence_transformers'
```

**해결:** 시맨틱 매칭은 선택 사항입니다. 기본 키워드 매칭이 자동으로 사용됩니다.

### 문제: Hook 파일이 로딩되지 않음

**증상:** 세션 시작 시 "Global Memory" 메시지가 표시되지 않음

**해결:**
```bash
# 1. Hook 디렉토리 확인
ls ~/.claude/hooks/moai/

# 2. Hook 파일 존재 확인
ls ~/.claude/hooks/moai/session_start__show_project_info.py

# 3. 재설치
python scripts/install.py --force
```

### 문제: 권한 오류

**증상:** Permission denied when writing to `~/.claude`

**해결:**
```bash
# Linux/macOS
chmod 755 ~/.claude
chmod 755 ~/.claude/hooks
chmod 755 ~/.claude/hooks/moai

# 재설치
python scripts/install.py --force
```

### 문제: Windows에서 ANSI 색상 안 보임

**증상:** 색상 코드가 문자 그대로 표시됨

**해결:** Windows 10+에서 PowerShell을 사용하거나, Windows Terminal을 설치하세요.

### 문제: 경로에 한글이 있어서 오류 발생

**증상:** UnicodeEncodeError 또는 파일 찾기 오류

**해결:** 설치 경로에 ASCII 문자만 사용하거나, 영문 경로로 설치하세요.

---

## 제거

시스템에서 Global Claude Rules를 제거하려면:

```bash
# 완전 제거
python scripts/uninstall.py

# 메모리 파일 유지
python scripts/uninstall.py --keep-memory
```

---

## 다음 단계

설치가 완료되면:

1. [사용 가이드](USAGE.md)를 참조하여 규칙을 추가해 보세요
2. [마이그레이션 가이드](MIGRATION.md)를 확인하여 기존 설치를 업그레이드하세요
3. [기여 가이드](CONTRIBUTING.md)를 참조하여 새 규칙을 제출하세요

---

**버전**: 1.6.0 | **최종 업데이트**: 2026-02-06
