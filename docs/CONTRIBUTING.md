# 기여 가이드 (Contributing Guide)

**Version**: 1.6.0
**Last Updated**: 2026-02-06

---

## Table of Contents

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

[GitHub Issues](https://github.com/YOUR-USERNAME/global-claude-rules/issues)에서 버그를 신고하세요.

### 4. 문서 개선

- 오타 수정
- 설명 추가
- 번역

---

## 규칙 제출 가이드라인

### 규칙 형식

모든 규칙은 다음 형식을 따라야 합니다:

```markdown
### ERR-XXX: [Short Title]

**Problem**: [What went wrong]
**Root Cause**: [Why it happened]
**Solution**: [How to fix]
**Prevention**: [How to avoid in future]
**Date**: YYYY-MM-DD
**Project**: [Project name]
**Category**: [Category name] (ERR-XXX~ERR-XXX)
```

### 필수 필드

| 필드 | 설명 | 예시 |
|------|------|------|
| **Problem** | 무엇이 잘못되었는지 | "Edit tool failed because file didn't exist" |
| **Root Cause** | 왜 발생했는지 | "Assumed path without verification" |
| **Solution** | 어떻게 수정하는지 | "Use Glob tool to verify file paths" |
| **Prevention** | 어떻게 예방하는지 | "Always use Glob before Read/Edit" |
| **Date** | 발생 날짜 | "2026-02-06" |
| **Project** | 관련 프로젝트 | "global-claude-rules" |
| **Category** | 카테고리 | "General/System (ERR-001~ERR-099)" |

### 카테고리 범위

| 카테고리 | ID 범위 | 예시 |
|----------|---------|------|
| General/System | ERR-001 ~ ERR-099 | ERR-001: TodoWrite Not Available |
| Git/Version Control | ERR-100 ~ ERR-199 | ERR-100: Push Rejected |
| Build/Compilation | ERR-200 ~ ERR-299 | ERR-200: Link Error |
| FPGA/Hardware | ERR-300 ~ ERR-399 | ERR-300: Timing Violation |
| Backend/API | ERR-400 ~ ERR-499 | ERR-400: API Timeout |
| Frontend/UI | ERR-500 ~ ERR-599 | ERR-500: Component Crash |
| MFC/Win32 | ERR-600 ~ ERR-699 | ERR-600: OnInitDialog Error |

### 좋은 규칙의 예시

```markdown
### ERR-004: File Path Not Found

**Problem**: Edit tool failed with "File does not exist" error for assumed file path
**Root Cause**: File path was assumed without verification using Glob tool
**Solution**: Always use Glob tool to verify file paths before Read/Edit operations
**Prevention**: In new projects, start with Glob to confirm file structure; never assume paths
**Date**: 2026-02-05
**Project**: global-claude-rules
**Category**: General/System (ERR-001~ERR-099)
```

### 나쁜 규칙의 예시

```markdown
### ERR-999: Error

**Problem**: Something went wrong
**Root Cause**: Unknown
**Solution**: Fix it
**Prevention**: Be careful
```

**문제점:**
- 제목이 너무 일반적
- 원인이 불명확
- 해결책이 실행 불가능
- 예방 방법이 구체적이지 않음

---

## 개발 워크플로우

### 1. 저장소 포크

```bash
# GitHub에서 저장소 포크
# 그 후 클론
git clone https://github.com/YOUR-USERNAME/global-claude-rules.git
cd global-claude-rules
```

### 2. 브랜치 생성

```bash
git checkout -b add-err-xxx-file-not-found
```

### 3. 규칙 추가

```bash
# CLI 도구 사용
python scripts/add_rule.py

# 또는 수동으로 templates/memory.md 편집
```

### 4. 검증

```bash
# 규칙 검증
python scripts/validate_rules.py

# 테스트 실행
python -m pytest tests/
```

### 5. 커밋

```bash
git add templates/memory.md
git commit -m "Add ERR-XXX: File Path Not Found

- Problem: Edit tool failed for assumed paths
- Solution: Use Glob for verification
- Category: General/System"
```

### 6. 푸시

```bash
git push origin add-err-xxx-file-not-found
```

### 7. Pull Request 생성

GitHub에서 Pull Request를 생성하세요.

---

## 코드 표준

### Python 코드 스타일

- PEP 8 따르기
- 타입 힌트 사용
- 독스트링 작성

```python
def get_next_err_number(memory_content: str) -> int:
    """
    Get the next available ERR number from memory content.

    Args:
        memory_content: The memory file content

    Returns:
        The next available ERR number
    """
    # implementation
```

### Hook 파일 스타일

- UTF-8 인코딩 사용
- 절대 경로 하드코딩 금지
- 환경 변수로 경로 감지

```python
# 좋은 예
def get_claude_dir() -> Path:
    if env_dir := os.getenv("CLAUDE_CONFIG_DIR"):
        return Path(env_dir)
    return Path.home() / ".claude"

# 나쁜 예
CLAUDE_DIR = "C:\\Users\\drake\\.claude"  # 하드코딩된 경로
```

---

## Pull Request 가이드

### PR 제목 형식

```
[Category] Short description

예시:
[ERR-001] Add TodoWrite alternative rule
[Docs] Update installation guide
[Fix] Resolve path detection issue
```

### PR 설명 템플릿

```markdown
## Summary
Added ERR-XXX for [issue description]

## Changes
- Added new error rule to templates/memory.md
- Updated quick reference table

## Validation
- [x] Rules validated with `python scripts/validate_rules.py`
- [x] Tests passing
- [x] No duplicate ERR IDs

## Related Issue
Closes #XXX
```

### PR 검토 체크리스트

제출 전 확인:

- [ ] 규칙 형식이 올바른지
- [ ] 모든 필수 필드가 존재하는지
- [ ] ERR ID가 중복되지 않는지
- [ ] 카테고리가 올바른지
- [ ] `validate_rules.py` 통과
- [ ] 테스트 통과
- [ ] 커밋 메시지가 명확한지

---

## 테스트

### 테스트 실행

```bash
# 전체 테스트
python -m pytest tests/

# 특정 테스트 파일
python -m pytest tests/test_add_rule.py

# 상세 출력
python -m pytest tests/ -v
```

### 테스트 작성

```python
def test_new_err_rule():
    """Test that new ERR rule is added correctly."""
    # Arrange
    title = "Test Error"

    # Act
    result = add_rule(title=title, ...)

    # Assert
    assert result.err_id == "ERR-026"
    assert "Test Error" in result.content
```

---

## 릴리즈 프로세스

### 버전 번호

```
MAJOR.MINOR.PATCH

예: 1.6.0
- MAJOR: 호환되지 않는 변경
- MINOR: 새로운 기능
- PATCH: 버그 수정
```

### 체인지로그

```markdown
## [1.6.0] - 2026-02-06

### Added
- ERR-025: File Path Not Found
- ERR-026: Module Import Error

### Fixed
- Fixed path detection on Windows

### Changed
- Updated documentation
```

---

## 커뮤니케이션

### 이슈 제출

버그 신고나 기능 요청은 [GitHub Issues](https://github.com/YOUR-USERNAME/global-claude-rules/issues)를 이용하세요.

### 토의

질문이 있으면 [Discussions](https://github.com/YOUR-USERNAME/global-claude-rules/discussions)를 이용하세요.

### 코드 리뷰

PR은 최대 7일 내에 리뷰됩니다.

---

## 라이선스

기여하는 모든 코드는 MIT 라이선스 하에 릴리스됩니다. PR을 제출함으로써 귀하의 기여가 MIT 라이선스로 릴리스되는 것에 동의하게 됩니다.

---

**감사합니다!** 🎉

모든 기여는 환영받으며 소중히 여깁니다.

---

**버전**: 1.6.0 | **최종 업데이트**: 2026-02-06
