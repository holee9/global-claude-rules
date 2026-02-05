# 설치 가이드 (Setup Guide)

Global Claude Rules System을 처음 설치하는 경우 이 가이드를 따르세요.

---

## 📋 목차

1. [사전 요구사항](#사전-요구사항)
2. [설치 방법](#설치-방법)
3. [환경별 설치](#환경별-설치)
4. [설치 검증](#설치-검증)
5. [환경 변수 설정](#환경-변수-설정)
6. [문제 해결](#문제-해결)

---

## 사전 요구사항

### 필수 요구사항

| 요구사항 | Windows | Linux/macOS |
|----------|---------|-------------|
| Python | 3.7+ | 3.7+ |
| Git | 최신 버전 | 최신 버전 |
| Claude Code | 설치됨 | 설치됨 |

### 설치 확인

```bash
# Python 버전 확인
python --version
# 또는
python3 --version

# Git 버전 확인
git --version
```

---

## 설치 방법

### 방법 1: 자동 설치 (권장)

#### 1단계: 저장소 복제

```bash
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules
```

#### 2단계: 설치 스크립트 실행

**Windows (PowerShell):**
```powershell
# 실행 정책 확인
Get-ExecutionPolicy

# 실행 정책이 Restricted인 경우
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 설치 스크립트 실행
.\scripts\install.ps1
```

**Linux/macOS:**
```bash
# 설치 스크립트 실행
python3 scripts/install.py

# 또는 python 명령어가 다른 경우
python scripts/install.py
```

#### 3단계: 설치 완료 확인

```
✓ Installed: C:\Users\[user]\.claude\memory.md
✓ Installed: C:\Users\[user]\.claude\hooks\moai\session_start__show_project_info.py
✓ Installed: C:\Users\[user]\.claude\GLOBAL_RULES_GUIDE.md

Installation completed successfully!
```

---

### 방법 2: 수동 설치

자동 설치가 실패하는 경우 수동으로 설치하세요.

#### 1단계: 디렉토리 생성

**Windows:**
```powershell
# PowerShell에서 실행
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\hooks\moai"
```

**Linux/macOS:**
```bash
# Bash에서 실행
mkdir -p ~/.claude/hooks/moai
```

#### 2단계: 파일 복사

**templates/memory.md → ~/.claude/memory.md**

**Windows:**
```powershell
Copy-Item templates\memory.md $env:USERPROFILE\.claude\memory.md
```

**Linux/macOS:**
```bash
cp templates/memory.md ~/.claude/memory.md
```

**templates/session_start__show_project_info.py → ~/.claude/hooks/moai/**

**Windows:**
```powershell
Copy-Item templates\session_start__show_project_info.py $env:USERPROFILE\.claude\hooks\moai\
```

**Linux/macOS:**
```bash
cp templates/session_start__show_project_info.py ~/.claude/hooks/moai/
```

---

## 환경별 설치

### Windows

#### PowerShell 사용

```powershell
# 1. 저장소 복제
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules

# 2. 설치
.\scripts\install.ps1

# 3. 확인
Get-ChildItem $env:USERPROFILE\.claude
```

#### CMD 사용

```cmd
REM 1. 저장소 복제
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules

REM 2. 설치 (Python 필요)
python scripts\install.py
```

#### WSL (Windows Subsystem for Linux)

```bash
# WSL에서 Linux용 설치 방법 따르기
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules
python3 scripts/install.py
```

### Linux

#### Ubuntu/Debian

```bash
# 1. 의존성 설치
sudo apt update
sudo apt install python3 python3-pip git

# 2. 저장소 복제
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules

# 3. 설치
python3 scripts/install.py
```

#### Fedora/RHEL

```bash
# 1. 의존성 설치
sudo dnf install python3 python3-pip git

# 2. 저장소 복제
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules

# 3. 설치
python3 scripts/install.py
```

### macOS

```bash
# 1. Homebrew로 의존성 설치 (선택사항)
brew install python3 git

# 2. 저장소 복제
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules

# 3. 설치
python3 scripts/install.py
```

---

## 설치 검증

### 1단계: 파일 존재 확인

**Windows:**
```powershell
Test-Path $env:USERPROFILE\.claude\memory.md
# Should return: True

Test-Path $env:USERPROFILE\.claude\hooks\moai\session_start__show_project_info.py
# Should return: True
```

**Linux/macOS:**
```bash
ls -la ~/.claude/memory.md
# Should show the file

ls -la ~/.claude/hooks/moai/session_start__show_project_info.py
# Should show the file
```

### 2단계: 내용 확인

```bash
# 메모리 파일 내용 확인 (처음 20줄)
head -n 20 ~/.claude/memory.md

# Windows PowerShell:
Get-Content $env:USERPROFILE\.claude\memory.md -Head 20
```

다음과 유사한 내용이 보여야 합니다:

```
# Global Development Memory - MANDATORY RULES

**Last Updated**: 2026-02-05
**Scope**: All Projects (Global)
**Version**: 1.5
```

### 3단계: Claude Code 세션 시작 검증

새 Claude Code 세션을 시작하면 다음과 같이 표시됩니다:

```
🚀 MoAI-ADK Session Started
   📦 Version: 1.5.0
   🔄 Changes: 0
   🌿 Branch: main
   📚 Global Memory: 24 error rules (Last: 2026-02-05)
```

---

## 환경 변수 설정

### 선택적 환경 변수

| 변수 | 설명 | 기본값 |
|------|------|--------|
| `CLAUDE_CONFIG_DIR` | Claude 설정 디렉토리 | `~/.claude` |
| `GLOBAL_CLAUDE_MEMORY` | 전역 메모리 파일 경로 | `~/.claude/memory.md` |
| `GLOBAL_CLAUDE_GUIDE` | 전역 가이드 파일 경로 | `~/.claude/GLOBAL_RULES_GUIDE.md` |

### Windows 환경 변수 설정

**현재 세션만 설정 (PowerShell):**
```powershell
$env:CLAUDE_CONFIG_DIR = "C:\Users\[user]\.claude"
$env:GLOBAL_CLAUDE_MEMORY = "C:\Users\[user]\.claude\memory.md"
```

**영구 설정 (PowerShell):**
```powershell
# 시스템 환경 변수에 추가
[System.Environment]::SetEnvironmentVariable('CLAUDE_CONFIG_DIR', 'C:\Users\[user]\.claude', 'User')
[System.Environment]::SetEnvironmentVariable('GLOBAL_CLAUDE_MEMORY', 'C:\Users\[user]\.claude\memory.md', 'User')
```

### Linux/macOS 환경 변수 설정

**현재 세션만 설정:**
```bash
export CLAUDE_CONFIG_DIR="$HOME/.claude"
export GLOBAL_CLAUDE_MEMORY="$HOME/.claude/memory.md"
```

**영구 설정 (~/.bashrc 또는 ~/.zshrc):**
```bash
echo 'export CLAUDE_CONFIG_DIR="$HOME/.claude"' >> ~/.bashrc
echo 'export GLOBAL_CLAUDE_MEMORY="$HOME/.claude/memory.md"' >> ~/.bashrc
source ~/.bashrc
```

---

## 설치 옵션

### Dry-Run (변경 사항 미리보기)

실제로 파일을 수정하지 않고 변경 사항을 확인합니다:

```bash
python scripts/install.py --dry-run
```

### 강제 재설치

기존 파일을 덮어씁니다:

```bash
python scripts/install.py --force
```

### 버전 확인

```bash
python scripts/install.py --version
```

---

## 문제 해결

### 문제: "python 명령을 찾을 수 없습니다"

**해결 방법:**

**Windows:**
```powershell
# Python이 설치된 위치 확인
where python

# 또는 python3 사용
python3 scripts/install.py
```

**Linux/macOS:**
```bash
# python3 사용
python3 scripts/install.py

# 또는 python 명령어 생성
sudo ln -sf /usr/bin/python3 /usr/bin/python
```

### 문제: "권한 거부" 오류

**해결 방법:**

**Linux/macOS:**
```bash
# 스크립트에 실행 권한 부여
chmod +x scripts/install.py

# 또는 python으로 직접 실행
python3 scripts/install.py
```

**Windows:**
```powershell
# PowerShell 실행 정책 변경
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 문제: Hook 파일이 실행되지 않음

**해결 방법:**

```bash
# Hook 디렉토리 확인
ls -la ~/.claude/hooks/moai/

# 디렉토리가 없는 경우 재설치
python scripts/install.py --force

# 파일이 있는 경우 실행 권한 확인
chmod +x ~/.claude/hooks/moai/*.py
```

### 문제: Git 인증 오류

**해결 방법:**

```bash
# Git 자격 증명 설정
git config --global credential.helper store

# 또는 SSH 키 사용
ssh-keygen -t ed25519 -C "your_email@example.com"
# SSH 퍼블릭 키를 GitHub 계정에 추가
```

### 문제: UTF-8 인코딩 오류 (Windows)

**해결 방법:**

```powershell
# PowerShell UTF-8 설정
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

# 또는 시스템 UTF-8 설정 (Windows 10 1903+)
# 설정 > 시간 및 언어 > 언어 > 관리용 언어 설정 >
# 시스템 로캘 변경 > 베타: Unicode UTF-8 전역 언어 지원 사용
```

---

## 다음 단계

설치가 완료되면:

1. **[사용 가이드](USAGE.md)** - 규칙 추가, 검증, 업데이트 방법 학습
2. **[기여 가이드](CONTRIBUTING.md)** - 새 규칙 제출 방법 학습

---

## 추가 도움말

- **GitHub Issues**: https://github.com/YOUR-USERNAME/global-claude-rules/issues
- **문서**: [README.md](../README.md)

---

**마지막 업데이트**: 2026-02-05
