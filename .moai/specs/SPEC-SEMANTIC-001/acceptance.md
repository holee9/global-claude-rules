---
spec_id: SPEC-SEMANTIC-001
title: Enhanced Semantic Rule Matching System
status: Planned
priority: High
assigned: workflow-spec
created: 2026-02-06
updated: 2026-02-06
lifecycle: spec-first
tags: [semantic, embedding, vector-search, nlp, rule-matching]
domain: semantic-matching
related_specs: []
dependencies: []
---

# ACCEPTANCE-SEMANTIC-001: 시맨틱 규칙 매칭 시스템 인수 기준

## 1. 정의 완료 (Definition of Done)

**[HARD]** 모든 항목이 충족될 때까지 기능은 완료되지 않음:

1. **EARS 요구사항 준수**: spec.md의 모든 REQ-SEM-XXX 요구사항 충족
2. **테스트 커버리지**: 핵심 모듈 85% 이상 커버리지
3. **성능 기준**: 모든 성능 목표 달성
4. **폴백 메커니즘**: 임베딩 실패 시 기존 기능 보장
5. **문서화**: API 문서 및 사용 가이드 완료
6. **버그 없음**: Critical, Major 레벨 버그 0개

---

## 2. Given-When-Then 시나리오

### 2.1. 시맨틱 매칭 기본 동작

**TC-001: 도구 실행 시 관련 규칙 시맨틱 매칭**

```gherkin
Scenario: 도구 실행 시 시맨틱 매칭으로 관련 규칙 반환
  Given 메모리에 10개의 ERR 규칙이 존재하고
    And 규칙 중 ERR-004는 "file not found" 관련 규칙이며
    And 벡터 인덱스가 초기화되어 있고
    And 캐시가 유효한 상태이다
  When 사용자가 Read 도구로 존재하지 않는 파일을 읽으려 시도하면
  Then 시스템은 ERR-004를 유사도 0.7 이상으로 매칭해야 하고
    And 매칭 결과에 relevance_score 필드가 포함되어야 하며
    And match_type이 "semantic"이어야 한다
```

### 2.2. 동의어 및 의미적 유사성 인식

**TC-002: 동의어를 포함한 쿼리 매칭**

```gherkin
Scenario: 키워드와 다른 표현으로 동일 의미 질문
  Given ERR-013 규칙이 "edit operation failed" 관련이고
    And 벡터 인덱스에 규칙이 임베딩되어 있다
  When 사용자가 "modify failed"로 검색하면
  Then ERR-013 규칙이 검색 결과에 포함되어야 하고
    And 유사도 점수가 0.5 이상이어야 한다
```

**TC-003: 문맥 기반 매칭**

```gherkin
Scenario: 파일 확장자를 포함한 문맥 인식
  Given ERR-023 규칙이 "encoding" 관련이고
    And Python 파일 관련 규칙들이 인덱스되어 있다
  When 사용자가 ".py file encoding error"로 검색하면
  Then encoding 관련 규칙이 우선순위로 매칭되어야 하고
    And Python 관련 규칙들도 상위 결과에 포함되어야 한다
```

### 2.3. 폴백 메커니즘

**TC-004: 임베딩 생성 실패 시 키워드 폴백**

```gherkin
Scenario: sentence-transformers 로딩 실패 시 키워드 매칭 사용
  Given 메모리에 규칙들이 존재하고
    And sentence-transformers 라이브러리가 설치되어 있지 않거나 로딩에 실패한다
  When 사용자가 도구를 실행하면
  Then 시스템은 기존 키워드 매칭을 사용해야 하고
    And 규칙 검색 결과가 정상적으로 반환되어야 하며
    And 로그에 "using keyword fallback" 메시지가 기록되어야 한다
```

**TC-005: 낮은 유사도 시 하이브리드 병합**

```gherkin
Scenario: 모든 시맨틱 결과가 임계값 미만인 경우
  Given 벡터 인덱스가 초기화되어 있고
    And 유사도 임계값이 0.5로 설정되어 있다
  When 사용자가 특정 도구를 실행하고 모든 시맨틱 결과가 0.5 미만이면
  Then 시스템은 키워드 매칭 결과를 병합해야 하고
    And 결과에 시맨틱과 키워드 매칭이 혼합되어야 하며
    And 각 규칙의 match_type 필드가 올바르게 표시되어야 한다
```

### 2.4. 캐시 관리

**TC-006: 유효한 캐시 로드**

```gherkin
Scenario: 24시간 이내 생성된 캐시 사용
  Given ~/.claude/cache/semantic_vectors/ 디렉토리에 캐시 파일이 존재하고
    And 캐시 타임스탬프가 1시간 전이다
  When 시스템이 초기화되면
  Then 캐시된 임베딩을 로드해야 하고
    And 새로운 임베딩을 생성하지 않아야 하며
    And 초기화 시간이 1초 이내여야 한다
```

**TC-007: 만료된 캐시 재생성**

```gherkin
Scenario: 24시간 경과된 캐시 무효화
  Given 캐시 파일이 존재하지만 타임스탬프가 25시간 전이다
  When 시스템이 초기화되면
  Then 기존 캐시를 무시해야 하고
    And 새로운 임베딩을 생성해야 하며
    And 캐시 타임스탬프가 갱신되어야 한다
```

**TC-008: 증분 업데이트**

```gherkin
Scenario: 단일 규칙 추가 시 전체 재임베딩 방지
  Given 50개의 규칙이 이미 인덱싱되어 있고
    And 캐시가 유효한 상태이다
  When 메모리에 1개의 새 규칙이 추가되면
  Then 시스템은 새 규칙만 임베딩해야 하고
    And 기존 50개 규칙의 임베딩을 재사용해야 하며
    And 전체 재계산 시간이 전체 재임베딩의 20% 이하여야 한다
```

### 2.5. 성능 기준

**TC-009: 검색 지연시간**

```gherkin
Scenario: 100개 규칙 기준 검색 성능
  Given 100개의 규칙이 벡터 인덱스에 등록되어 있다
  When 도구 실행으로 규칙 검색을 요청하면
  Then 검색 결과가 100ms 이내에 반환되어야 하고
    And 상위 5개 결과가 정렬되어 있어야 한다
```

**TC-010: 초기 로딩 시간**

```gherkin
Scenario: 첫 번째 실행 시 모델 로딩
  Given 캐시가 존재하지 않는 상태이다
  When 시스템이 처음 초기화되면
  Then sentence-transformers 모델 로딩을 포함하여 3초 이내에 완료되어야 하고
    And 초기화 이후 검색이 가능해야 한다
```

**TC-011: GPU 가속**

```gherkin
Scenario: CUDA 사용 가능 환경에서 GPU 활용
  Given 시스템에 CUDA가 설치되어 있고
    And faiss-gpu가 설치되어 있다
  When 시스템이 초기화되면
  Then GPU 디바이스를 사용해야 하고
    And CPU 대비 배치 처리 속도가 2배 이상 빨라야 한다
```

### 2.6. 결과 품질

**TC-012: 중복 제거**

```gherkin
Scenario: 시맨틱과 키워드 결과 중복 처리
  Given 하이브리드 매칭이 활성화되어 있고
    And ERR-004가 시맨틱과 키워드 모두에서 매칭된다
  When 최종 결과가 생성되면
  Then ERR-004는 결과에 한 번만 나타나야 하고
    And relevance_score는 더 높은 값이 사용되어야 한다
```

**TC-013: 결과 정렬**

```gherkin
Scenario: 유사도 점수 기반 정렬
  Given 여러 규칙이 매칭된다
  When 결과가 반환되면
  Then 결과는 relevance_score 기준 내림차순 정렬되어야 하고
    And 상위 5개 결과만 표시되어야 한다
```

### 2.7. 에러 처리

**TC-014: 라이브러리 설치 누락**

```gherkin
Scenario: 필수 의존성이 설치되어 있지 않음
  Given sentence-transformers 또는 faiss가 설치되어 있지 않다
  When 시스템이 초기화되면
  Then ImportError가 발생하지 않아야 하고
    And 자동으로 키워드 폴백 모드로 전환되어야 하며
    And 경고 로그가 기록되어야 한다
```

**TC-015: 캐시 손상**

```gherkin
Scenario: 캐시 파일이 손상됨
  Given 캐시 파일이 존재하지만 내용이 손상되었다
  When 시스템이 캐시를 로드하려 시도하면
  Then 손상된 캐시를 무시해야 하고
    And 새로운 임베딩을 생성해야 하며
    And 에러 로그가 기록되어야 한다
```

---

## 3. 품질 게이트 (Quality Gates)

### 3.1. 기능 테스트

| 항목 | 기준 | 검증 방법 |
|------|------|-----------|
| 시맨틱 매칭 정확도 | 70%+ | 사용자 피드백, 라벨링된 테스트 케이스 |
| 폴백 동작 | 100% | 모든 실패 시나리오에서 키워드 폴백 작동 |
| 캐시 적중률 | 90%+ | 두 번째 실행부터 캐시 사용 |
| 중복 제거 | 100% | 결과에 중복 ID 없음 |

### 3.2. 성능 테스트

| 항목 | 목표 | 측정 방법 |
|------|------|-----------|
| 검색 지연시간 (100규칙) | < 100ms | 프로파일링 |
| 초기 로딩 (캜 없음) | < 3초 | 모델 로드 시간 측정 |
| 초기 로딩 (캐시 있음) | < 1초 | 캐시 로드 시간 측정 |
| 메모리 사용 | < 500MB | 프로파일링 |

### 3.3. 테스트 커버리지

```bash
# 목표 커버리지
pytest --cov=lib.semantic_matcher --cov=lib.semantic_embedder \
       --cov=lib.vector_index --cov=lib.vector_cache \
       --cov-report=term-missing --cov-fail-under=85
```

### 3.4. 린트 및 포맷팅

```bash
# ruff 린트 (무 경고)
ruff check lib/semantic_*.py lib/vector_*.py lib/hybrid_matcher.py

# black 포맷팅
black --check lib/semantic_*.py lib/vector_*.py lib/hybrid_matcher.py
```

---

## 4. 검증 방법 및 도구 (Verification Methods and Tools)

### 4.1. 단위 테스트

```python
# tests/test_semantic_matcher.py
import pytest
from lib.semantic_matcher import SemanticRuleMatcher
from lib.vector_cache import VectorCache

@pytest.fixture
def sample_rules():
    return [
        {
            'id': 'ERR-004',
            'title': 'File Not Found Error',
            'problem': 'File path does not exist',
            'solution': 'Check file path and try again'
        },
        # ... more rules
    ]

def test_semantic_matching_finds_relevant_rules(sample_rules):
    matcher = SemanticRuleMatcher()
    matcher.initialize(sample_rules)

    results = matcher.match('Read', {'file_path': '/nonexistent/file.txt'})

    assert len(results) > 0
    assert any(r['id'] == 'ERR-004' for r in results)
    assert results[0]['relevance_score'] >= 0.5

def test_fallback_on_embedding_error(sample_rules, monkeypatch):
    # Mock embedding failure
    def mock_encode(*args, **kwargs):
        raise RuntimeError("Embedding failed")

    matcher = SemanticRuleMatcher()
    monkeypatch.setattr(matcher.embedder, 'encode', mock_encode)

    results = matcher.match('Read', {'file_path': '/test/file.txt'})

    # Should fall back to keyword matching
    assert len(results) >= 0
```

### 4.2. 통합 테스트

```python
# tests/test_integration.py
def test_end_to_end_rule_matching():
    """PreToolUse hook에서의 전체 흐름 테스트"""
    from pre_tool_enforce_rules import find_relevant_rules
    from lib.project_detector import detect_project_type

    # 테스트용 메모리 로드
    memory_content = load_test_memory()

    # 규칙 추출
    rules = extract_rules_from_memory(memory_content)

    # 매칭 테스트
    results = find_relevant_rules(
        rules,
        'Write',
        {'file_path': '/test/file.py', 'content': 'print("hello")'}
    )

    # 검증
    assert isinstance(results, list)
    assert all('relevance_score' in r for r in results)
    assert all('match_type' in r for r in results)
```

### 4.3. 성능 벤치마크

```python
# tests/benchmark.py
import time
import pytest

@pytest.mark.benchmark
def test_search_performance_100_rules(benchmark, sample_rules_100):
    matcher = SemanticRuleMatcher()
    matcher.initialize(sample_rules_100)

    def search():
        return matcher.match('Read', {'file_path': '/test/file.txt'})

    result = benchmark(search)
    assert benchmark.stats.stats.mean < 0.1  # 100ms

@pytest.mark.benchmark
def test_initialization_time(benchmark):
    def init():
        matcher = SemanticRuleMatcher()
        matcher.initialize(sample_rules_100)
        return matcher

    result = benchmark(init)
    assert benchmark.stats.stats.mean < 3.0  # 3 seconds
```

### 4.4. A/B 테스트 프레임워크

```python
# lib/ab_test.py
class ABTestRunner:
    """키워드 vs 시맨틱 성능 비교"""

    def run_comparison(self, test_cases: list[dict]):
        """테스트 케이스로 두 방식 비교"""
        keyword_matcher = KeywordRuleMatcher()
        semantic_matcher = SemanticRuleMatcher()

        results = {
            'keyword': [],
            'semantic': [],
            'wins': {'keyword': 0, 'semantic': 0, 'tie': 0}
        }

        for case in test_cases:
            keyword_results = keyword_matcher.match(case['tool'], case['input'])
            semantic_results = semantic_matcher.match(case['tool'], case['input'])

            # 정답 라벨과 비교
            keyword_correct = self._is_correct(keyword_results, case['expected'])
            semantic_correct = self._is_correct(semantic_results, case['expected'])

            if keyword_correct and not semantic_correct:
                results['wins']['keyword'] += 1
            elif semantic_correct and not keyword_correct:
                results['wins']['semantic'] += 1
            elif keyword_correct == semantic_correct:
                results['wins']['tie'] += 1

        return results
```

---

## 5. 성공 지표 (Success Metrics)

### 5.1. 정량적 지표

| 지표 | 기준 | 현재 | 목표 |
|------|------|------|------|
| 검색 정확도 | 정답 라벨 일치율 | ~40% | 70%+ |
| 검색 완료율 | 빈 결과 비율 | < 5% | < 2% |
| 평균 검색 시간 | P95 지연시간 | ~10ms | < 100ms |
| 사용자 만족도 | 규칙 도움됨 응답 | N/A | 80%+ |

### 5.2. 정성적 지표

- 사용자 피드백: "규칙이 더 관련성 있게 나타남"
- 불필요한 규칙 노출 감소
- 실패 패턴에 대한 적절한 규칙 제안 증가

---

## 6. 릴리스 체크리스트

- [ ] 모든 EARS 요구사항 구현 완료
- [ ] 단위 테스트 통과 (85%+ 커버리지)
- [ ] 통합 테스트 통과
- [ ] 성능 벤치마크 목표 달성
- [ ] 린트 및 포맷팅 검사 통과
- [ ] 폴백 메커니즘 검증
- [ ] 캬 무효화/재생성 테스트 통과
- [ ] A/B 테스트로 개선 효과 확인
- [ ] API 문서 작성 완료
- [ ] 사용자 가이드 작성 완료

---

## 7. 다음 단계

1. **테스트 환경 설정**: `pytest` 및 `pytest-cov` 설치
2. **구현 시작**: `/moai:2-run SPEC-SEMANTIC-001`
3. **A/B 테스트**: 라벨링된 테스트 케이스로 성능 검증
4. **사용자 피드백 수집**: 실제 사용 시 개선 효과 확인
