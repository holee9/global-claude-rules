# Global Claude Rules System

> **반복 에러를 90% 감소시키는 포카요케(Poka-Yoke) 시스템**
>
> 모든 프로젝트, 모든 개발자, 모든 PC에서 동일한 에러 방지 규칙을 자동으로 적용합니다.

---

## 🎯 프로젝트 목표

AI agent 작업 중 발생한 **실수/실패/오류를 규칙으로 강력하게 메모리**하고, 매 세션 시작/작업 지시마다 규칙을 먼저 확인하여 **반복 에러를 줄이는 시스템**입니다.

```
┌─────────────────────────────────────────────────────────────────┐
│  목표: 반복 에러 90% 감소 (Poka-Yoke 원칙 적용)                  │
├─────────────────────────────────────────────────────────────────┤
│  1. 에러 자동 감지 → 규칙화 (ERR-XXX)                           │
│  2. 세션 시작 시 자동 로딩 + 강제 확인                           │
│  3. 다중 PC 간 Git 기반 동기화                                   │
│  4. Claude 실행 시 전역 규칙 자동 업데이트                       │
└─────────────────────────────────────────────────────────────────┘
```

### 핵심 기능

| 기능 | 설명 | 효과 |
|------|------|------|
| **자동 로딩** | 세션 시작 핵심 규칙 자동 표시 | 규칙 잊지 않음 |
| **Pre-Tool 확인** | 도구 실행 전 관련 규칙 표시 | 실행 전 에러 방지 |
| **CLI 도구** | 규칙 추가/검증/업데이트 자동화 | 30초 만에 규칙 추가 |
| **Git 동기화** | 다중 PC 간 규칙 공유 | 모든 PC에서 동일 규칙 |
| **강제 확인** | 모든 작업 전 규칙 표시 | 실수 방지 |

---

## 📦 빠른 시작 (3분 설치)

### 1단계: 저장소 복제

```bash
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules
```

### 2단계: 설치 스크립트 실행

**Windows (PowerShell):**
```powershell
.\scripts\install.ps1
```

**Linux/macOS:**
```bash
python3 scripts/install.py
```

### 3단계: 설치 확인

새 Claude Code 세션을 시작하면 다음과 같이 표시됩니다:

```
🚀 MoAI-ADK Session Started
   📦 Version: 1.5.0
   🔄 Changes: 0
   🌿 Branch: main
   📚 Global Memory: 24 error rules (Last: 2026-02-05)
```

---

## 📖 상세 가이드

| 가이드 | 설명 |
|--------|------|
| [설치 가이드](docs/SETUP.md) | 첫 설치, 환경 설정, 검증 단계 |
| [사용 가이드](docs/USAGE.md) | 규칙 추가, 검증, 업데이트 방법 |
| [기여 가이드](docs/CONTRIBUTING.md) | 규칙 제출, 개발 워크플로우 |

---

## 🚀 주요 사용법

### 새 에러 규칙 추가 (30초)

```bash
# 대화형 모드로 규칙 추가
python scripts/add_rule.py
```

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

✓ ERR-025: File Path Not Found added successfully!
```

### 규칙 검증

```bash
# 규칙 포맷 검증
python scripts/validate_rules.py

# 상세 출력
python scripts/validate_rules.py --verbose
```

### 여러 PC에서 규칙 동기화

**PC 1 (규칙 추가 후):**
```bash
cd global-claude-rules
git add templates/memory.md
git commit -m "Add ERR-025: File Path Not Found"
git push
```

**PC 2 (업데이트):**
```bash
cd global-claude-rules
python scripts/update.py
```

---

## 📂 프로젝트 구조

```
global-claude-rules/
├── templates/                    # 템플릿 파일 (Git 저장소)
│   ├── memory.md                 # 전역 메모리 템플릿
│   ├── GLOBAL_RULES_GUIDE.md     # 사용자 가이드
│   └── session_start__show_project_info.py
│
├── scripts/                      # CLI 도구
│   ├── install.py                # 설치 스크립트
│   ├── add_rule.py               # 규칙 추가 CLI
│   ├── validate_rules.py         # 규칙 검증 도구
│   ├── update.py                 # 자동 업데이트
│   └── uninstall.py              # 제거 스크립트
│
├── tests/                        # 테스트
│   ├── test_install.py
│   ├── test_add_rule.py
│   └── test_validate_rules.py
│
├── docs/                         # 상세 문서
│   ├── SETUP.md                  # 설치 가이드
│   ├── USAGE.md                  # 사용 가이드
│   └── CONTRIBUTING.md           # 기여 가이드
│
└── README.md                     # 이 파일
```

---

## 🔧 설치 위치

| 플랫폼 | 전역 메모리 | Hook 파일 |
|--------|-------------|-----------|
| **Windows** | `C:\Users\[user]\.claude\memory.md` | `C:\Users\[user]\.claude\hooks\moai\` |
| **Linux/macOS** | `~/.claude/memory.md` | `~/.claude/hooks/moai/` |

---

## 📋 에러 카테고리

| ID 범위 | 카테고리 | 설명 |
|---------|----------|------|
| ERR-001 ~ ERR-099 | General/System | Claude Code 작업 에러 |
| ERR-100 ~ ERR-199 | Git/Version Control | 버전 관리 에러 |
| ERR-200 ~ ERR-299 | Build/Compilation | 빌드/컴파일 에러 |
| ERR-300 ~ ERR-399 | FPGA/Hardware | 하드웨어 개발 에러 |
| ERR-400 ~ ERR-499 | Backend/API | 백엔드/API 에러 |
| ERR-500 ~ ERR-599 | Frontend/UI | 프론트엔드/UI 에러 |
| ERR-600 ~ ERR-699 | MFC/Win32 | Windows API 에러 |

---

## 🔄 업데이트 방법

### 자동 업데이트 (권장)

```bash
python scripts/update.py
```

### 수동 업데이트

```bash
git pull
python scripts/install.py --force
```

---

## 🤝 기여 방법

새로운 에러를 발견하면 규칙으로 추가해 주세요:

1. **규칙 추가**: `python scripts/add_rule.py`
2. **검증**: `python scripts/validate_rules.py`
3. **커밋**: `git add/commit/push`
4. **PR 생성**: GitHub에서 Pull Request

자세한 내용은 [CONTRIBUTING.md](docs/CONTRIBUTING.md)를 참조하세요.

---

## 🐛 문제 해결

### 문제: 규칙이 로딩되지 않음

```bash
# 재설치
python scripts/install.py --force
```

### 문제: Hook 오류

```bash
# Hook 디렉토리 확인
ls ~/.claude/hooks/moai/

# 재설치
python scripts/install.py --force
```

### 문제: Git 동기화 실패

```bash
# Git 원격 저장소 확인
git remote -v

# 업데이트 스크립트 사용
python scripts/update.py --dry-run
```

---

## 📊 현재 지원되는 ERR 규칙

현재 **24개 이상의 에러 방지 규칙**이 포함되어 있습니다:

| ERR | 제목 | 카테고리 |
|-----|------|----------|
| ERR-001 | TodoWrite Tool Not Available | System |
| ERR-002 | Hook Files Missing | System |
| ERR-003 | Edit Tool Hook Failure | System |
| ERR-004 | File Path Not Found | System |
| ERR-005 | Port Direction Mismatch | FPGA |
| ERR-006 | Reset Polarity Inversion | FPGA |
| ... | ... | ... |

전체 목록은 `templates/memory.md`를 참조하세요.

---

## 📝 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능합니다.

---

## 🔗 링크

- **GitHub**: https://github.com/YOUR-USERNAME/global-claude-rules
- **Issues**: https://github.com/YOUR-USERNAME/global-claude-rules/issues
- **문서**: [docs/](docs/)

---

## ⭐ 핵심 원칙

1. **모든 프로젝트에 적용** - 프로젝트 종속적이지 않은 범용 규칙
2. **자동 동기화** - Git으로 모든 PC가 항상 최신 상태 유지
3. **강제 확인** - 작업 전 자동으로 관련 규칙 표시
4. **쉬운 기여** - 30초 만에 새 규칙 추가 가능
5. **포카요케** - 실수할 수 없도록 시스템이 방지

---

**버전**: 1.5.0 | **최종 업데이트**: 2026-02-05
