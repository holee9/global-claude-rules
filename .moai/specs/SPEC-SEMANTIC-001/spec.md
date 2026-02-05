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

# SPEC-SEMANTIC-001: 향상된 시맨틱 규칙 매칭 시스템

## 개요 (Overview)

현재 키워드 기반 정규식 매칭을 사용하는 규칙 검색 시스템을 시맨틱 유사도 기반 매칭으로 대체하여 규칙 검색의 정확도를 60-80% 개선합니다.

### 현재 시스템 분석

기존 `pre_tool__enforce_rules.py`와 `project_detector.py`는 다음 방식으로 동작합니다:

1. **키워드 기반 매칭**: TOOL_KEYWORDS 사전에 정의된 키워드로 규칙 검색
2. **정규식 패턴 매칭**: ERROR_PATTERNS에 정의된 정규식으로 에러 패턴 감지
3. **점수 기반 랭킹**: 키워드 일치 횟수로 단순 점수 계산
4. **프로젝트 타입 필터링**: 파일 마커 기반 프로젝트 타입 감지

### 문제점

- **의미적 유사성 무시**: 동의어, 유사 표현을 인식하지 못함
- **키워드 의존성**: 사전에 정의되지 않은 키워드는 검색 불가
- **거짓 양성(FP) 발생**: 키워드 포함 but 문맥 다른 경우 잘못 노출
- **거짓 음성(FN) 발생**: 키워드 없지만 의미적으로 관련 있는 규칙 누락

### 해결 방안

임베딩 기반 시맨틱 매칭 시스템 도입:

1. **sentence-transformers**로 규칙 텍스트 임베딩 생성
2. **FAISS** 또는 **Chroma** 벡터 데이터베이스 구축
3. **코사인 유사도** 기반 실시간 매칭
4. **하이브리드 접근**: 시맨틱 + 키워드 폴백

---

## 환경 (Environment)

### 실행 환경

```yaml
python_version: "3.11+"
platform: ["Windows", "macOS", "Linux"]
execution_context: "PreToolUse Hook"
memory_limit: "2GB recommended"
cache_location: "~/.claude/cache/semantic_vectors/"
```

### 의존성

```python
# Core dependencies
sentence-transformers >= 2.3.0  # 임베딩 생성
numpy >= 1.24.0                  # 벡터 연산
faiss-cpu >= 1.7.4               # 벡터 검색 (또는 chromadb)

# Optional GPU acceleration
sentence-transformers[gpu]       # CUDA 지원 시 가속
faiss-gpu >= 1.7.4               # GPU 벡터 검색
```

### 통신 포인트

```yaml
input:
  - tool_name: str           # 실행 도구 이름
  - tool_input: dict         # 도구 입력 파라미터
  - project_context: dict    # 프로젝트 타입 및 메타데이터

output:
  - relevant_rules: list[dict]  # 매칭된 규칙 목록
  - similarity_scores: list[float]  # 유사도 점수
  - fallback_used: bool        # 폴백 사용 여부
```

---

## 가정 (Assumptions)

### 기술적 가정

| 가정 | 신뢰도 | 근거 | 위험 |
|------|--------|------|------|
| sentence-transformers 모델 로딩 시간 < 3초 | 중 | 모델 캐싱으로 완화 가능 | 모델 크기에 따라 지연 발생 |
| 100개 규칙 기준 검색 시간 < 100ms | 높 | FAISS 인덱스는 밀리초 단위 | 규칙 수 1000개 이상 시 성능 저하 |
| 1GB 이하 임베딩 저장 공간 | 높 | 768차원 × 100규칙 × 4바이트 ≈ 300KB | 규칙 수 증가 시 선형 증가 |

### 비즈니스 가정

| 가정 | 신뢰도 | 근거 | 위험 |
|------|--------|------|------|
| 규칙 관련도 60-80% 개선 가능 | 중 | 임베딩 기반 시맨틱 검색 성능 참조 | 개선 측정 기준 정의 필요 |
| 사용자가 추가 지연을 허용할 것 | 중 | 3초 초기 로딩은 수용 가능한 범위 | 빈번한 모델 리로딩 시 문제 |

---

## 요구사항 (Requirements) - EARS 형식

### 1. 보편적 요구사항 (Ubiquitous)

```yaml
REQ-SEM-001:
  type: Ubiquitous
  statement: "시스템은 항상 모든 ERR 규칙의 임베딩 벡터를 캐시에 저장해야 한다"
  rationale: 중복 계산 방지 및 검색 성능 보장
  verification: 캐시 파일 존재 및 유효성 검증

REQ-SEM-002:
  type: Ubiquitous
  statement: "시스템은 항상 코사인 유사도 점수를 0.0 ~ 1.0 범위로 정규화해야 한다"
  rationale: 일관된 점수 해석 및 임계값 설정
  verification: 유사도 점수 범위 테스트

REQ-SEM-003:
  type: Ubiquitous
  statement: "시스템은 항상 키워드 폴백 메커니즘을 유지해야 한다"
  rationale: 임베딩 생성 실패 시 기존 기능 보장
  verification: 임베딩 실패 시 키워드 매칭 동작 확인
```

### 2. 이벤트 기반 요구사항 (Event-Driven)

```yaml
REQ-SEM-004:
  type: Event-Driven
  statement: "WHEN 도구 실행이 요청되면 THEN 시스템은 도구 컨텍스트와 규칙 간 시맨틱 유사도를 계산해야 한다"
  trigger: PreToolUse 이벤트 수신
  response: 도구 입력 텍스트 임베딩 및 유사도 계산
  verification: 도구 호출 시 임베딩 생성 로그 확인

REQ-SEM-005:
  type: Event-Driven
  statement: "WHEN 새로운 ERR 규칙이 메모리에 추가되면 THEN 시스템은 해당 규칙의 임베딩을 즉시 생성하고 캐시를 업데이트해야 한다"
  trigger: 메모리 파일 변경 감지
  response: 변경된 규칙만 재임베딩 (증분 업데이트)
  verification: 규칙 추가 후 캐시 업데이트 확인

REQ-SEM-006:
  type: Event-Driven
  statement: "WHEN 임베딩 생성이 실패하면 THEN 시스템은 기존 키워드 매칭으로 폴백하고 경고를 로깅해야 한다"
  trigger: 임베딩 생성 예외 발생
  response: 키워드 매칭 실행 + 에러 로그
  verification: 예외 주입 시 폴백 동작 확인
```

### 3. 상태 기반 요구사항 (State-Driven)

```yaml
REQ-SEM-007:
  type: State-Driven
  statement: "IF 캐시가 존재하고 24시간 이내 생성되었으면 THEN 시스템은 캐시된 임베딩을 로드해야 한다"
  condition: 캐시 파일 존재 && 생성 시간 < 24시간
  response: 캐시 로드, 재임베딩 스킵
  verification: 캐시 유효기간 테스트

REQ-SEM-008:
  type: State-Driven
  statement: "IF 유사도 점수가 임계값(0.5) 미만인 결과만 존재하면 THEN 시스템은 키워드 매칭 결과를 병합해야 한다"
  condition: 최대 유사도 < 0.5
  response: 시맨틱 + 키워드 하이브리드 결과
  verification: 낮은 유사도 시 하이브리드 동작 확인

REQ-SEM-009:
  type: State-Driven
  statement: "IF CUDA가 사용 가능하면 THEN 시스템은 GPU 가속을 활성화해야 한다"
  condition: CUDA 사용 가능
  response: GPU 디바이스에 모델 로드
  verification: GPU 환경에서 가속 활성화 확인
```

### 4. 바람직하지 않은 동작 (Unwanted)

```yaml
REQ-SEM-010:
  type: Unwanted
  statement: "시스템은 도구 실행을 5초 이상 지연시키지 않아야 한다"
  consequence: 사용자 경험 저하
  mitigation: 비동기 초기화, 모델 미리로딩

REQ-SEM-011:
  type: Unwanted
  statement: "시스템은 임베딩 생성 실패 시 규칙 검색 기능을 완전히 중단하지 않아야 한다"
  consequence: 규칙 시스템 불가용
  mitigation: 폴백 메커니즘

REQ-SEM-012:
  type: Unwanted
  statement: "시스템은 중복된 규칙을 결과에 포함하지 않아야 한다"
  consequence: 사용자 혼란
  mitigation: 결과 중복 제거 로직
```

### 5. 선택적 요구사항 (Optional)

```yaml
REQ-SEM-013:
  type: Optional
  statement: "가능하다면 다국어 지원을 제공해야 한다"
  description: 한국어, 일본어, 중국어 규칙 지원
  model: paraphrase-multilingual-mpnet-base-v2
  priority: Medium

REQ-SEM-014:
  type: Optional
  statement: "가능하다면 규칙 간 의미적 클러스터링을 제공해야 한다"
  description: 유사한 규칙 그룹화 및 추천
  priority: Low

REQ-SEM-015:
  type: Optional
  statement: "가능하다면 A/B 테스트 프레임워크를 지원해야 한다"
  description: 키워드 vs 시맨틱 성능 비교
  priority: Low
```

---

## 명세 (Specifications)

### 4.1. 시맨틱 임베딩 생성

```python
# 의사 코드
class SemanticRuleEmbedder:
    """규칙 텍스트를 임베딩 벡터로 변환"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.embedding_dim = 384  # MiniLM-L6 기준

    def encode_rule(self, rule: dict) -> np.ndarray:
        """단일 규칙 임베딩 생성

        규칙의 ID, 제목, 문제, 해결책을 결합하여
        문맥이 풍부한 임베딩 생성
        """
        text = self._compose_rule_text(rule)
        return self.model.encode(text)

    def _compose_rule_text(self, rule: dict) -> str:
        """규칙 필드 결합"""
        return f"{rule['id']}: {rule['title']}. {rule['problem']}. {rule['solution']}"
```

### 4.2. 벡터 데이터베이스

```python
class VectorRuleIndex:
    """FAISS 기반 벡터 인덱스"""

    def __init__(self, embedding_dim: int = 384):
        self.index = faiss.IndexFlatIP(embedding_dim)  # Inner Product = Cosine with normalized vectors
        self.rules: list[dict] = []

    def add_rule(self, rule: dict, embedding: np.ndarray):
        """규칙 추가"""
        # L2 정규화하여 내적이 코사인 유사도가 되도록
        normalized = embedding / np.linalg.norm(embedding)
        self.index.add(normalized.reshape(1, -1))
        self.rules.append(rule)

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[tuple[dict, float]]:
        """상위 K개 유사 규칙 검색"""
        normalized = query_embedding / np.linalg.norm(query_embedding)
        scores, indices = self.index.search(normalized.reshape(1, -1), k)
        return [(self.rules[i], scores[0][j]) for j, i in enumerate(indices[0])]
```

### 4.3. 하이브리드 매칭

```python
class HybridRuleMatcher:
    """시맨틱 + 키워드 하이브리드 매칭"""

    def __init__(self):
        self.semantic_matcher = SemanticRuleMatcher()
        self.keyword_matcher = KeywordRuleMatcher()  # 기존

    def find_relevant_rules(self, tool_name: str, tool_input: dict) -> list[dict]:
        # 시맨틱 매칭 시도
        semantic_results = self.semantic_matcher.match(tool_name, tool_input)

        # 유사도가 낮으면 키워드 보강
        if not semantic_results or semantic_results[0]['score'] < 0.5:
            keyword_results = self.keyword_matcher.match(tool_name, tool_input)
            return self._merge_results(semantic_results, keyword_results)

        return semantic_results
```

### 4.4. 캐시 전략

```yaml
cache_structure:
  path: "~/.claude/cache/semantic_vectors/"
  files:
    embeddings: "rule_embeddings.npz"     # NumPy 압축 포맷
    metadata: "rule_metadata.json"        # 규칙 ID-인덱스 매핑
    timestamp: "last_update.txt"          # 마지막 업데이트 시간

invalidation:
  triggers:
    - memory.md 파일 수정 시간 변경
    - 24시간 경과
    - 명시적 무효화 요청

incremental_update:
  strategy: "변경된 규칙만 재임베딩"
  benefit: "전체 재계산 80% 감소"
```

### 4.5. API 인터페이스

```python
# 통합 인터페이스 (기존 find_relevant_rules와 호환)
def find_relevant_rules_semantic(
    rules: list[dict],
    tool_name: str,
    tool_input: dict,
    use_fallback: bool = True,
) -> list[dict]:
    """시맨틱 매칭 기반 규칙 검색

    Args:
        rules: 메모리에서 추출한 전체 규칙
        tool_name: 실행 도구 이름
        tool_input: 도구 입력 파라미터
        use_fallback: 시맨틱 실패 시 키워드 폴백 사용

    Returns:
        relevance_score 필드가 추가된 규칙 리스트
    """
    # 구현...
```

---

## 추적성 (Traceability)

### 요구사항-컴포넌트 매핑

| 요구사항 | 컴포넌트 | 테스트 시나리오 |
|----------|----------|----------------|
| REQ-SEM-001 | VectorCache | TC-001 캐시 저장/로드 |
| REQ-SEM-002 | SemanticMatcher | TC-002 유사도 정규화 |
| REQ-SEM-003 | HybridMatcher | TC-003 폴백 동작 |
| REQ-SEM-004 | SemanticMatcher | TC-004 도구 컨텍스트 매칭 |
| REQ-SEM-005 | VectorCache | TC-005 증분 업데이트 |
| REQ-SEM-006 | HybridMatcher | TC-006 예외 처리 |
| REQ-SEM-007 | VectorCache | TC-007 캐시 유효기간 |
| REQ-SEM-008 | HybridMatcher | TC-008 하이브리드 병합 |
| REQ-SEM-009 | SemanticEmbedder | TC-009 GPU 가속 |

### 태그 정의

```yaml
tags:
  semantic:     # 시맨틱 매칭 관련
  embedding:    # 임베딩 생성 및 저장
  vector-search: # 벡터 검색
  cache:        # 캐싱 전략
  fallback:     # 폴백 메커니즘
  hybrid:       # 하이브리드 매칭
```

---

## 참고 (References)

### 모델 옵션

| 모델 | 차원 | 성능 | 크기 | 추천 용도 |
|------|------|------|------|-----------|
| all-MiniLM-L6-v2 | 384 | 빠름 | 80MB | 기본 추천 |
| all-mpnet-base-v2 | 768 | 정확 | 420MB | 고정확도 필요 시 |
| paraphrase-multilingual-mpnet-base-v2 | 768 | 다국어 | 470MB | 다국어 지원 시 |

### 벡터 DB 옵션

| 라이브러리 | 장점 | 단점 | 추천 |
|-----------|------|------|------|
| faiss-cpu | 가장 빠름, 메타서 | GPU 버전 별도 | 필수 |
| chromadb | 쉬운 API, 퍼시스턴트 | 무거움 | 선택적 |
| annoy | 경량, 서버리스 | 메모리 인덱스만 | 소규모 |

### 관련 자료

- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [FAISS Tutorial](https://github.com/facebookresearch/faiss/wiki)
- [Semantic Search Best Practices](https://www.pinecone.io/learn/semantic-search/)
