# 전역 규칙 동기화 가이드 (Global Rules Synchronization Guide)

**Date**: {{DATE}}
**Version**: {{VERSION}}
**Scope**: 모든 프로젝트에 적용되는 전역 에러 규칙 시스템

---

## 1. 개요 (Overview)

### 1.1 목적

모든 Claude Code 프로젝트에서 발생하는 에러를 중앙에서 관리하고, 동일한 실수가 반복되지 않도록 방지합니다.

### 1.2 구조

```
📁 전역 메모리 시스템
├── 🌍 ~/.claude/memory.md (전역 메모리)
│   ├── ERR-001 ~ ERR-016: Claude Code 작업 에러 (보편적)
│   ├── ERR-017 ~ ERR-021: FPGA/Hardware 에러
│   └── 기술별 규칙 (FPGA, Frontend, Backend, Database)
│
└── 📁 프로젝트별 메모리
    ├── [project]/.claude/memory.md
    └── [project]/doc/LESSONS_LEARNED.md
```

---

## 2. 경로 설정 (Path Configuration)

### 2.1 기본 경로

| 플랫폼 | 전역 메모리 | 전역 가이드 |
|--------|-------------|-------------|
| Windows | `C:\Users\[username]\.claude\memory.md` | `D:\GLOBAL_RULES_GUIDE.md` 또는 `~\.claude\GLOBAL_RULES_GUIDE.md` |
| Linux/macOS | `~/.claude/memory.md` | `~/.claude/GLOBAL_RULES_GUIDE.md` |

### 2.2 환경 변수 (Environment Variables)

| 변수 | 용도 | 예시 |
|------|------|------|
| `GLOBAL_CLAUDE_MEMORY` | 전역 메모리 경로 오버라이드 | `C:\Users\user\.claude\memory.md` |
| `GLOBAL_CLAUDE_GUIDE` | 전역 가이드 경로 오버라이드 | `D:\GLOBAL_RULES_GUIDE.md` |
| `CLAUDE_CONFIG_DIR` | Claude 설정 디렉토리 | `C:\Users\user\.claude` |

---

## 3. 전역 에러 목록 (Global Error List)

### 3.1 Claude Code 작업 에러 (ERR-001 ~ ERR-016)

| ID | 설명 | 빠른 해결 |
|----|------|-----------|
| ERR-001 | TodoWrite 사용 불가 | TaskCreate/TaskUpdate 사용 |
| ERR-002 | Hook 파일 누락 | 무시 후 진행 (non-blocking) |
| ERR-003 | Edit 툴 실패 | Bash + Python/sed 사용 |
| ERR-004 | 파일 경로 틀림 | Glob로 먼저 확인 |
| ERR-005 | 포트 방향 불일치 | 연결 전 input/output 확인 |
| ERR-006 | 리셋 극성 반전 | `_n` 접미사 = active-LOW 확인 |
| ERR-007 | Undriven signal | 드라이버 추가 |
| ERR-008 | 필수 파라미터 누락 | 체크리스트 사용 |
| ERR-009 | Grep 패턴 실패 | Glob + Read 조합 사용 |
| ERR-010 | 비현실적인 모듈 크기 목표 | 구조 고려하여 설정 |
| ERR-011 | 선언되지 않은 신호 사용 | assign 전 선언 확인 |
| ERR-012 | 리셋 신호 이름 틀림 | 모든 참조 확인 |
| ERR-013 | 허위 양성 감지 | 직접 파일 확인 |
| ERR-014 | 주석 구분자 | `//` 접두사 사용 |
| ERR-015 | Python escape | 생성 후 검증 |
| ERR-016 | #을 주석으로 사용 | `//` 사용 |
| ERR-022 | 명령 미준수 | 지시사항 확인 후 실행 |
| ERR-023 | UTF-16 파일 수정 실패 | PowerShell 스크립트 사용 |

### 3.2 MFC/Win32 에러 (ERR-600 ~ ERR-699)

| ID | 설명 | 빠른 해결 |
|----|------|-----------|
| ERR-600 | OnInitDialog control access | Use OnDelayedInit |
| ERR-601 | DLL architecture mismatch | Use x64 DLLs |
| ERR-602 | Uninitialized CFile | Initialize or declare in scope |

---

## 4. 사용 방법 (How to Use)

### 4.1 작업 시작 전 체크리스트

모든 새로운 작업 시작 전:

```
[ ] 1. 전역 메모리 확인: ~/.claude/memory.md
[ ] 2. 프로젝트 메모리 확인: doc/LESSONS_LEARNED.md
[ ] 3. 관련 ERR-XXX 검색
[ ] 4. 문서화된 솔루션 적용
[ ] 5. 작업 시작
```

### 4.2 전역 규칙 확인

```bash
# 전역 메모리 직접 확인
cat ~/.claude/memory.md

# Windows
type %USERPROFILE%\.claude\memory.md
```

---

## 5. 설치 방법 (Installation)

### 5.1 자동 설치 (권장)

```bash
# Git 저장소에서 클론 후 설치 스크립트 실행
git clone https://github.com/user/global-claude-rules.git temp-install
cd temp-install
python scripts/install.py
```

### 5.2 수동 설치

1. `templates/memory.md`를 `~/.claude/memory.md`로 복사
2. `templates/session_start__show_project_info.py`를 `~/.claude/hooks/moai/`로 복사
3. 필요한 경우 환경 변수 설정

---

## 6. 에러 문서화 (Error Documentation)

### 6.1 새 에러 추가

```markdown
### ERR-XXX: [짧은 제목]

**Problem**: [설명]
**Root Cause**: [원인]
**Solution**: [해결책]
**Prevention**: [예방 방법]
**Date**: YYYY-MM-DD
**Project**: [프로젝트명]
```

---

## 7. 자동 로딩 동작 (Auto-Loading Behavior)

### 7.1 SessionStart Hook

전역 메모리는 **SessionStart Hook**을 통해 자동으로 로드됩니다:

- 핵심 규칙 (ERR-001~ERR-016)이 자동으로 systemMessage에 주입
- 프로젝트별 규칙과 자동 병합
- 약 200-300 토큰 소모

### 7.2 로드되는 규칙

| 규칙 집합 | 출처 | 상태 |
|----------|------|------|
| 핵심 규칙 (ERR-001~ERR-016) | ~/.claude/memory.md | ✅ 자동 로드 |
| 프로젝트별 규칙 | .claude/memory.md | ✅ 자동 병합 |
| 프로젝트 레슨 | doc/LESSONS_LEARNED.md | ✅ 자동 병합 |
| 기술별 규칙 | ~/.claude/memory.md | ⚠️ 수동 확인 필요 |

---

## 8. 검증 방법 (Verification)

### 8.1 설치 검증

```bash
# ERR 개수 확인
grep "### ERR-" ~/.claude/memory.md | wc -l
```

### 8.2 자동 로딩 검증

새 세션을 시작할 때 다음 메시지가 표시되는지 확인:

```
📚 Global Memory: [N] error rules (Last: YYYY-MM-DD)
```

---

**END OF GUIDE**
