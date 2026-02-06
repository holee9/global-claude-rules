# API 문서 (API Documentation)

**Version**: 1.6.0
**Last Updated**: 2026-02-06

---

## Table of Contents

1. [시맨틱 매칭 API](#시맨틱-매칭-api)
2. [CLI 도구 API](#cli-도구-api)
3. [Hook API](#hook-api)
4. [Python 라이브러리](#python-라이브러리)

---

## 시맨틱 매칭 API

### SemanticMatcher

의미적 유사도 기반 규칙 검색 메인 클래스.

```python
from semantic_matcher import SemanticMatcher

matcher = SemanticMatcher()
results = matcher.find_relevant_rules(
    query="edit file not found",
    tool_name="Edit"
)
```

#### 메서드

| 메서드 | 설명 | 반환값 |
|--------|------|--------|
| `find_relevant_rules(query, tool_name)` | 관련 규칙 검색 | `List[RuleMatch]` |
| `is_semantic_available()` | 시맨틱 매칭 가능 여부 | `bool` |
| `get_rule_embedding(rule_text)` | 규칙 임베딩 생성 | `np.ndarray` |

### RuleMatch

검색 결과 클래스.

```python
@dataclass
class RuleMatch:
    err_id: str           # ERR-XXX
    title: str            # 규칙 제목
    similarity: float     # 유사도 (0-1)
    rule_type: str        # "semantic" 또는 "keyword"
```

---

## CLI 도구 API

### add_rule.py

```python
from add_rule import add_rule, validate_rule_fields

# 대화형으로 규칙 추가
add_rule()

# 필드 검증
errors = validate_rule_fields({
    "title": "Test Error",
    "problem": "...",
    "root_cause": "...",
    "solution": "...",
    "prevention": "..."
})
```

#### 함수

| 함수 | 설명 | 반환값 |
|------|------|--------|
| `add_rule()` | 대화형 규칙 추가 | `None` |
| `validate_rule_fields(fields)` | 필드 검증 | `List[str]` (에러 목록) |
| `get_next_err_number(content, category)` | 다음 ERR 번호 | `int` |
| `get_category_for_number(number)` | 카테고리 반환 | `str` |

### validate_rules.py

```python
from validate_rules import (
    validate_memory_file,
    ValidationResult,
    ValidationError
)

# 메모리 파일 검증
result = validate_memory_file("templates/memory.md")

if result.is_valid:
    print("Valid!")
else:
    for error in result.errors:
        print(f"{error.err_id}: {error.message}")
```

#### 클래스

```python
class ValidationResult:
    is_valid: bool
    total_rules: int
    errors: List[ValidationError]
    warnings: List[ValidationError]

class ValidationError:
    err_id: str
    field: str
    message: str
    line: int
```

---

## Hook API

### SessionStart Hook

세션 시작 시 호출되는 Hook.

```python
# .claude/hooks/moai/session_start__show_project_info.py

def main():
    """Session start hook main function."""
    # 프로젝트 정보 표시
    # 전역 메모리 로드
    # 규칙 요약 출력
    pass

if __name__ == "__main__":
    main()
```

### PreTool Hook

도구 실행 전 호출되는 Hook.

```python
# .claude/hooks/moai/pre_tool__enforce_rules.py

def main():
    """Pre-tool hook main function."""
    # 도구 이름 확인
    # 관련 규칙 검색
    # 규칙 표시
    pass

if __name__ == "__main__":
    main()
```

#### 환경 변수

Hook은 다음 환경 변수를 사용합니다:

| 변수 | 설명 |
|------|------|
| `CLAUDE_CONFIG_DIR` | Claude 설정 디렉토리 |
| `GLOBAL_CLAUDE_MEMORY` | 전역 메모리 파일 경로 |
| `GLOBAL_CLAUDE_GUIDE` | 전역 가이드 파일 경로 |

---

## Python 라이브러리

### shared/errors.py

에러 정의 모듈.

```python
class RuleError(Exception):
    """Base exception for rule errors."""
    pass

class ValidationError(RuleError):
    """Raised when validation fails."""
    pass

class DuplicateErrorError(RuleError):
    """Raised when duplicate ERR ID is found."""
    pass
```

### 사용 예시

```python
from shared.errors import ValidationError, DuplicateErrorError

try:
    validate_rule_fields(fields)
except ValidationError as e:
    print(f"Validation failed: {e}")
except DuplicateErrorError as e:
    print(f"Duplicate ERR ID: {e}")
```

---

## 통합 예시

### 규칙 검색 통합

```python
from semantic_matcher import SemanticMatcher
from pathlib import Path

# 시맨틱 매처 초기화
matcher = SemanticMatcher()

# 규칙 검색
results = matcher.find_relevant_rules(
    query="file path not found",
    tool_name="Edit"
)

# 결과 출력
for match in results:
    print(f"{match.err_id}: {match.title} ({match.similarity:.2f})")
```

### 규칙 추가 통합

```python
from add_rule import add_rule, validate_rule_fields
from validate_rules import validate_memory_file

# 1. 규칙 추가
add_rule()

# 2. 검증
result = validate_memory_file("templates/memory.md")

if result.is_valid:
    print("All rules valid!")
else:
    for error in result.errors:
        print(f"Error: {error.message}")
```

---

## 의존성

### 필수 의존성

```python
# requirements.txt
python>=3.10
```

### 선택적 의존성 (시맨틱 매칭)

```python
# requirements-semantic.txt
sentence-transformers>=2.3.0
numpy>=1.24.0
faiss-cpu>=1.7.4  # 또는 faiss-gpu
```

---

## 버전 호환성

| Python 버전 | 1.5.x | 1.6.x |
|-------------|-------|-------|
| 3.10 | ✅ | ✅ |
| 3.11 | ✅ | ✅ |
| 3.12 | ✅ | ✅ |
| 3.13 | ⚠️ | ✅ |

---

## 타입 정의

### Rule

```python
@dataclass
class Rule:
    err_id: str
    title: str
    problem: str
    root_cause: str
    solution: str
    prevention: str
    date: str
    project: str
    category: str
```

### Category

```python
class Category(Enum):
    GENERAL = (1, 99, "General/System")
    GIT = (100, 199, "Git/Version Control")
    BUILD = (200, 299, "Build/Compilation")
    FPGA = (300, 399, "FPGA/Hardware")
    BACKEND = (400, 499, "Backend/API")
    FRONTEND = (500, 599, "Frontend/UI")
    MFC = (600, 699, "MFC/Win32")
```

---

**버전**: 1.6.0 | **최종 업데이트**: 2026-02-06
