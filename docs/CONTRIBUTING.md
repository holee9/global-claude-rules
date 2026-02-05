# 기여 가이드 (Contributing Guide)

Global Claude Rules System에 기여해 주셔서 감사합니다. 새로운 에러 규칙을 추가하고, 프로젝트를 개선하는 방법을 안내합니다.

---

## 📋 목차

1. [기여할 수 있는 방법](#기여할-수-있는-방법)
2. [규칙 제출 가이드라인](#규칙-제출-가이드라인)
3. [개발 워크플로우](#개발-워크플로우)
4. [코드 표준](#코드-표준)
5. [Pull Request 가이드](#pull-request-가이드)

---

## 기여할 수 있는 방법

### 1. 새 에러 규칙 추가

가장 중요한 기여 방법입니다. 새로운 에러를 발견하면 규칙으로 등록하세요.

### 2. 기존 규칙 개선

- 설명을 더 명확하게
- 예방 방법 추가
- 카테고리 재분류

### 3. 버그 신고

[GitHub Issues](https://github.com/YOUR-USERNAME/global-claude-rules/issues)에 버그를 신고해 주세요.

### 4. 문서 개선

- 오타 교정
- 설명 명확화
- 번역 추가

---

## 규칙 제출 가이드라인

### 좋은 규칙의 특징

| 특징 | 좋은 예 | 나쁜 예 |
|------|---------|---------|
| **구체적** | Edit tool fails on .rc files (UTF-16) | File edit error |
| **재현 가능** | Use Glob before Read to verify path exists | Check paths first |
| **범용성** | Applies to all projects using Edit tool | Only for my specific project |
| **예방 중심** | Prevention: Always verify encoding first | Just fix it manually |

### 규칙 템플릿

```markdown
### ERR-XXX: [Short Title]

**Problem**: [Clear description of what went wrong]
**Root Cause**: [Why it happened - technical explanation]
**Solution**: [How to fix the specific issue]
**Prevention**: [How to avoid this in future - actionable steps]
**Date**: YYYY-MM-DD
**Project**: [Project name where discovered]
**Category**: [Category (ERR-XXX~ERR-XXX)]
```

### 규칙 추가 단계

#### 1단계: 검색

먼저 비슷한 규칙이 이미 있는지 확인하세요:

```bash
# 기존 규칙 검색
grep -i "keyword" templates/memory.md
```

#### 2단계: 추가

```bash
# CLI 도구로 규칙 추가
python scripts/add_rule.py
```

#### 3단계: 검증

```bash
# 포맷 검증
python scripts/validate_rules.py
```

#### 4단계: 테스트

```bash
# 테스트 실행
pytest tests/

# 또는 특정 테스트
pytest tests/test_add_rule.py
```

#### 5단계: 커밋

```bash
git add templates/memory.md
git commit -m "Add ERR-XXX: [Title]"
```

---

## 개발 워크플로우

### 포크 및 클론

```bash
# 1. 포크 (GitHub 웹에서)

# 2. 클론
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules

# 3. 업스트림 추가
git remote add upstream https://github.com/ORIGINAL-OWNER/global-claude-rules.git
```

### 브랜치 전략

```bash
# 메인 브랜치 업데이트
git checkout main
git pull upstream main

# 기능 브랜치 생성
git checkout -b add-err-xxx-new-rule
```

### 커밋 컨벤션

```
<type>(<scope>): <subject>

<body>

<footer>
```

**타입 (type):**
- `add`: 새 규칙 추가
- `fix`: 버그 수정
- `docs`: 문서 변경
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 기타 유지보수

**예시:**

```
add(rules): ERR-025 UTF-16 file encoding error

Add new rule for handling UTF-16 encoded files on Windows.
Edit tool fails with "String to replace not found" when
editing .rc files that use UTF-16 LE encoding.

Closes #42
```

---

## 코드 표준

### Python 코드 스타일

```python
# 함수는 snake_case
def add_new_rule(title: str, problem: str) -> dict:
    """Add a new ERR rule to memory.

    Args:
        title: Short title for the error
        problem: Problem description

    Returns:
        Dictionary with rule data
    """
    # ...

# 클래스는 PascalCase
class RuleValidator:
    """Validates ERR rule format."""

    def __init__(self):
        self.errors = []

    def validate(self, rule: dict) -> bool:
        """Validate rule format.

        Returns:
            True if rule is valid
        """
        # ...
```

### 문서화 문자열

```python
def short_function(docstring_example):
    """One line summary.

    Longer description if needed.
    """
    pass
```

### 타입 힌트

```python
from typing import List, Dict, Optional

def get_rules(category: str) -> List[Dict[str, str]]:
    """Get all rules for a category."""
    return []

def find_rule(err_id: str) -> Optional[Dict]:
    """Find rule by ID."""
    return None
```

---

## Pull Request 가이드

### PR 제목 형식

```
Add ERR-XXX: [Short error title]
```

### PR 설명 템플릿

```markdown
## What this PR does

Adds a new ERR rule for [error description].

## Changes

- [ ] Added ERR-XXX to templates/memory.md
- [ ] Updated quick reference table
- [ ] Validated with `python scripts/validate_rules.py`
- [ ] Tested locally

## Related issue

Closes #[issue_number]

## Screenshots (if applicable)

Before:
[creenshot]

After:
[screenshot]
```

### PR 검증 목록

제출 전 확인해 주세요:

- [ ] `python scripts/validate_rules.py` 통과
- [ ] `pytest tests/` 통과
- [ ] 새 규칙이 기존 규칙과 중복되지 않음
- [ ] 규칙 번호가 올바른 카테고리 범위内
- [ ] 설명이 명확하고 재현 가능함
- [ ] 예방 방법이 포함됨

### 코드 리뷰

PR이 제출되면 자동으로 검증이 실행됩니다:

```yaml
# .github/workflows/validate.yml (예정)
name: Validate Rules
on: [pull_request]
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate
        run: |
          python scripts/validate_rules.py
          pytest tests/
```

---

## 규칙 카테고리 가이드

### 카테고리 선택 기준

| 카테고리 | ID 범위 | 포함되는 에러 |
|----------|---------|---------------|
| **General/System** | 001-099 | Claude Code 도구, 파일 시스템, 인코딩 |
| **Git/Version** | 100-199 | merge, conflict, branch, push/pull |
| **Build/Compile** | 200-299 | 컴파일 에러, 링커,依赖问题 |
| **FPGA/Hardware** | 300-399 | timing, synthesis, place & route |
| **Backend/API** | 400-499 | 서버 에러, API, 데이터베이스 |
| **Frontend/UI** | 500-599 | React, Vue, CSS, 렌더링 |
| **MFC/Win32** | 600-699 | Win32 API, MFC, COM |

### 범용성 원칙

**포함 (범용):**
- 모든 프로젝트에서 발생 가능
- 특정 언어/프레임워크에 국한되지 않음
- 기술적 원인이 명확함

**제외 (프로젝트 특정):**
- 특정 프로젝트에만 해당
- 일시적인 문제
- 환경 의존적 (네트워크, 서버 상태 등)

프로젝트 특정 규칙은 프로젝트의 `.claude/memory.md`에 추가하세요.

---

## 테스트 가이드

### 테스트 작성

새 기능을 추가할 때 테스트도 함께 작성해 주세요:

```python
# tests/test_add_rule.py

def test_add_rule_with_all_fields():
    """Test adding a rule with all fields."""
    rule = format_rule_entry(
        999,
        "Test Title",
        "Test problem",
        "Test cause",
        "Test solution",
        "Test prevention",
        project="TestProject",
        category="Test Category"
    )

    assert "ERR-999" in rule
    assert "Test Title" in rule
    assert "TestProject" in rule
```

### 테스트 실행

```bash
# 전체 테스트
pytest tests/

# 특정 파일
pytest tests/test_add_rule.py

# 상세 출력
pytest tests/ -v

# 커버리지
pytest tests/ --cov
```

---

## 릴리스 프로세스

### 버전 번호

```
MAJOR.MINOR.PATCH

MAJOR: 호환되지 않는 변경
MINOR: 새로운 기능 (규칙 추가)
PATCH: 버그 수정
```

### 릴리스 체크리스트

- [ ] CHANGELOG.md 업데이트
- [ ] 버전 번호 업데이트
- [ ] 모든 테스트 통과
- [ ] 문서 업데이트
- [ ] Git 태그 생성

---

## 질문?

- **GitHub Issues**: https://github.com/YOUR-USERNAME/global-claude-rules/issues
- **Discussions**: https://github.com/YOUR-USERNAME/global-claude-rules/discussions

---

감사합니다! 🎉

**마지막 업데이트**: 2026-02-05
