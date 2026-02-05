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

# PLAN-SEMANTIC-001: 시맨틱 규칙 매칭 시스템 구현 계획

## 1. 마일스톤 (Milestones)

### 1.1. 1차 마일스톤: 핵심 시맨틱 매칭 엔진 (Priority High)

**목표**: 기본적인 임베딩 생성 및 유사도 검색 기능 구현

- **M1-1**: sentence-transformers 기반 임베딩 모듈 구현
- **M1-2**: FAISS 인덱스 생성 및 검색 기능 구현
- **M1-3**: 캐시 저장/로드 기능 구현
- **M1-4**: 기존 pre_tool__enforce_rules.py와 통합

**완료 기준**:
- 도구 실행 시 시맨틱 매칭이 동작
- 최소 1개 이상의 규칙이 올바르게 매칭됨

### 1.2. 2차 마일스톤: 하이브리드 매칭 및 폴백 (Priority High)

**목표**: 안정성 확보를 위한 하이브리드 매칭 및 폴백 메커니즘

- **M2-1**: 키워드 매칭과의 하이브리드 병합 로직 구현
- **M2-2**: 임베딩 실패 시 폴백 메커니즘 구현
- **M2-3**: 유사도 임계값 기반 결과 필터링 구현
- **M2-4**: 예외 처리 및 로깅 강화

**완료 기준**:
- 임베딩 실패 시에도 규칙 검색이 동작
- 낮은 유사도 시 키워드 결과가 병합됨

### 1.3. 3차 마일스톤: 성능 최적화 (Priority Medium)

**목표**: 검색 속도 및 메모리 사용량 최적화

- **M3-1**: 증분 업데이트 기능 구현 (변경된 규칙만 재임베딩)
- **M3-2**: GPU 가加速 옵션 구현
- **M3-3**: 캐시 유효기간 관리 구현
- **M3-4**: 병렬 처리 최적화

**완료 기준**:
- 100개 규칙 기준 검색 < 100ms
- 초기 로딩 < 3초

### 1.4. 4차 마일스톤: 고급 기능 (Priority Low)

**목표**: 다국어 지원 및 A/B 테스트

- **M4-1**: 다국어 모델 옵션 추가
- **M4-2**: A/B 테스트 프레임워크 구현
- **M4-3**: 규칙 클러스터링 및 추천 기능
- **M4-4**: 성능 분석 대시보드

**완료 기준**:
- 선택 사항으로, 기간에 따라 추후 구현 가능

---

## 2. 기술 접근 방식 (Technical Approach)

### 2.1. 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    PreToolUse Hook                          │
│                  (pre_tool__enforce_rules.py)               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  SemanticRuleMatcher                        │
│  ┌───────────────┐  ┌──────────────┐  ┌─────────────────┐  │
│  │  Embedder     │  │ VectorIndex  │  │ HybridMatcher   │  │
│  │  (sBERT)      │  │  (FAISS)     │  │  (+Keyword)     │  │
│  └───────────────┘  └──────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴────────┐
                    ▼                ▼
            ┌─────────────┐  ┌──────────────────┐
            │ VectorCache │  │ KeywordFallback  │
            │  (~/.claude)│  │  (기존 로직)     │
            └─────────────┘  └──────────────────┘
```

### 2.2. 핵심 컴포넌트

**SemanticEmbedder**:

```python
class SemanticEmbedder:
    """sentence-transformers 래퍼"""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.device = self._detect_device()

    def encode(self, texts: list[str]) -> np.ndarray:
        """배치 임베딩 생성"""
        return self.model.encode(
            texts,
            batch_size=32,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    def encode_rule(self, rule: dict) -> np.ndarray:
        """단일 규칙 임베딩"""
        text = self._compose_rule_text(rule)
        return self.encode([text])[0]

    def _compose_rule_text(self, rule: dict) -> str:
        return f"{rule['id']}: {rule['title']}. {rule['problem']}. {rule['solution']}"

    def _detect_device(self) -> str:
        """CUDA 사용 가능 여부 감지"""
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
```

**VectorRuleIndex**:

```python
class VectorRuleIndex:
    """FAISS 기반 벡터 인덱스"""

    def __init__(self, embedding_dim: int = 384):
        self.embedding_dim = embedding_dim
        self.index = faiss.IndexFlatIP(embedding_dim)
        self.rules: list[dict] = []
        self.rule_id_to_idx: dict[str, int] = {}

    def add_rules(self, rules: list[dict], embeddings: np.ndarray):
        """배치 규칙 추가"""
        for i, rule in enumerate(rules):
            self.rule_id_to_idx[rule['id']] = i

        # L2 정규화
        normalized = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.index.add(normalized)
        self.rules.extend(rules)

    def search(self, query_embedding: np.ndarray, k: int = 5) -> list[tuple[dict, float]]:
        """상위 K개 검색"""
        normalized = query_embedding / np.linalg.norm(query_embedding)
        scores, indices = self.index.search(normalized.reshape(1, -1), k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.rules):
                results.append((self.rules[idx], float(score)))
        return results

    def save(self, path: Path):
        """인덱스 저장"""
        faiss.write_index(self.index, str(path / "index.faiss"))

    def load(self, path: Path):
        """인덱스 로드"""
        self.index = faiss.read_index(str(path / "index.faiss"))
```

**VectorCache**:

```python
class VectorCache:
    """임베딩 캐시 관리"""

    CACHE_DIR = Path.home() / ".claude" / "cache" / "semantic_vectors"
    CACHE_VALIDITY = timedelta(hours=24)

    def __init__(self):
        self.cache_dir = self.CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def is_valid(self) -> bool:
        """캐시 유효성 검사"""
        timestamp_file = self.cache_dir / "timestamp.txt"
        if not timestamp_file.exists():
            return False

        timestamp = datetime.fromisoformat(timestamp_file.read_text())
        return datetime.now() - timestamp < self.CACHE_VALIDITY

    def save(self, embeddings: np.ndarray, metadata: dict):
        """캐시 저장"""
        np.savez_compressed(
            self.cache_dir / "embeddings.npz",
            embeddings=embeddings
        )
        (self.cache_dir / "metadata.json").write_text(
            json.dumps(metadata, ensure_ascii=False)
        )
        (self.cache_dir / "timestamp.txt").write_text(
            datetime.now().isoformat()
        )

    def load(self) -> tuple[np.ndarray, dict] | None:
        """캐시 로드"""
        try:
            data = np.load(self.cache_dir / "embeddings.npz")
            embeddings = data["embeddings"]
            metadata = json.loads(
                (self.cache_dir / "metadata.json").read_text()
            )
            return embeddings, metadata
        except (FileNotFoundError, ValueError):
            return None

    def invalidate(self):
        """캐시 무효화"""
        for file in self.cache_dir.glob("*"):
            file.unlink()
```

**HybridRuleMatcher**:

```python
class HybridRuleMatcher:
    """시맨틱 + 키워드 하이브리드 매칭"""

    SIMILARITY_THRESHOLD = 0.5
    MIN_RESULTS = 3

    def __init__(self, use_gpu: bool = True):
        self.embedder = SemanticEmbedder()
        self.index = VectorRuleIndex()
        self.cache = VectorCache()
        self.keyword_matcher = KeywordRuleMatcher()  # 기존

    def initialize(self, rules: list[dict]):
        """초기화 및 규칙 인덱싱"""
        # 캐시 확인
        if self.cache.is_valid():
            cached = self.cache.load()
            if cached:
                embeddings, metadata = cached
                self._load_from_cached(rules, embeddings, metadata)
                return

        # 캐시 없으면 새로 생성
        embeddings = self._generate_embeddings(rules)
        self.index.add_rules(rules, embeddings)
        self.cache.save(embeddings, {"rule_ids": [r['id'] for r in rules]})

    def match(self, tool_name: str, tool_input: dict) -> list[dict]:
        """규칙 매칭"""
        # 쿼리 임베딩 생성
        query_text = self._compose_query(tool_name, tool_input)
        query_embedding = self.embedder.encode([query_text])[0]

        # 시맨틱 검색
        semantic_results = self.index.search(query_embedding, k=10)

        # 유사도 점수 추가
        results = []
        for rule, score in semantic_results:
            rule['relevance_score'] = score
            rule['match_type'] = 'semantic'
            results.append(rule)

        # 하이브리드 결정
        max_score = semantic_results[0][1] if semantic_results else 0
        if max_score < self.SIMILARITY_THRESHOLD or len(results) < self.MIN_RESULTS:
            keyword_results = self.keyword_matcher.match(tool_name, tool_input)
            results = self._merge_results(results, keyword_results)

        return results

    def _compose_query(self, tool_name: str, tool_input: dict) -> str:
        """쿼리 텍스트 구성"""
        parts = [f"Tool: {tool_name}"]
        if 'file_path' in tool_input:
            parts.append(f"File: {tool_input['file_path']}")
        if 'command' in tool_input:
            parts.append(f"Command: {tool_input['command']}")
        return ". ".join(parts)

    def _merge_results(self, semantic: list, keyword: list) -> list:
        """결과 병합 및 중복 제거"""
        seen = {r['id'] for r in semantic}
        for rule in keyword:
            if rule['id'] not in seen:
                rule['match_type'] = 'keyword'
                semantic.append(rule)
                seen.add(rule['id'])
        return semantic
```

### 2.3. 기존 코드와의 통합

```python
# pre_tool__enforce_rules.py 수정

def find_relevant_rules(
    rules: list[dict],
    tool_name: str,
    tool_input: dict,
) -> list[dict]:
    """시맨틱 매칭 기반 규칙 검색 (업그레이드)"""
    try:
        # 하이브리드 매처 사용
        if not hasattr(find_relevant_rules, 'matcher'):
            from semantic_matcher import HybridRuleMatcher
            find_relevant_rules.matcher = HybridRuleMatcher()
            find_relevant_rules.matcher.initialize(rules)

        return find_relevant_rules.matcher.match(tool_name, tool_input)

    except Exception as e:
        # 시맨틱 실패 시 기존 키워드 폴백
        logging.warning(f"Semantic matching failed: {e}, using keyword fallback")
        return find_relevant_rules_keyword(rules, tool_name, tool_input)  # 기존 함수
```

---

## 3. 의존성 설치

### 3.1. requirements.txt

```txt
# Semantic Rule Matching Dependencies
sentence-transformers>=2.3.0
faiss-cpu>=1.7.4
numpy>=1.24.0

# Optional GPU acceleration
# sentence-transformers[gpu]  # Uncomment for CUDA support
# faiss-gpu>=1.7.4             # Uncomment for CUDA support
```

### 3.2. 설치 명령어

```bash
# CPU 버전 (기본)
pip install sentence-transformers faiss-cpu

# GPU 버전 (CUDA 사용 가능 환경)
pip install sentence-transformers faiss-gpu
```

---

## 4. 파일 구조

```
.claude/hooks/moai/
├── pre_tool__enforce_rules.py           # 수정: 하이브리드 매칭 통합
├── lib/
│   ├── semantic_matcher.py              # 신규: 메인 매처
│   ├── semantic_embedder.py             # 신규: 임베딩 생성
│   ├── vector_index.py                  # 신규: FAISS 래퍼
│   ├── vector_cache.py                  # 신규: 캐시 관리
│   └── hybrid_matcher.py                # 신규: 하이브리드 로직
└── tests/                               # 신규: 테스트 디렉토리
    ├── test_semantic_matcher.py
    ├── test_vector_cache.py
    └── test_hybrid_matcher.py
```

---

## 5. 위험 및 대응 계획 (Risks and Mitigations)

| 위험 | 영향 | 확률 | 대응 계획 |
|------|------|------|-----------|
| 모델 로딩 지연 > 5초 | 높 | 중 | 비동기 초기화, 모델 미리로딩 |
| 임베딩 메모리 초과 | 중 | 낮 | 배치 처리, 모델 경량화 |
| GPU 메모리 부족 | 중 | 중 | CPU 폴백 자동 전환 |
| 규칙 수 증가로 검색 지연 | 중 | 중 | FAISS IVF 인덱스로 업그레이드 |
| sentence-transformes 설치 실패 | 높 | 낮 | 키워드 폴백 명시적 처리 |

---

## 6. 성능 목표

| 메트릭 | 현재 | 목표 | 측정 방법 |
|--------|------|------|-----------|
| 검색 정확도 | ~40% | 70-80% | 사용자 피드백, A/B 테스트 |
| 검색 지연시간 | ~10ms | <100ms | 프로파일링 |
| 초기 로딩 | N/A | <3초 | 모델 로드 시간 측정 |
| 메모리 사용 | ~10MB | <500MB | 프로파일링 |
| 캐시 적중률 | N/A | >90% | 캐시 통계 |

---

## 7. 다음 단계 (Next Steps)

1. **구현 시작**: `/moai:2-run SPEC-SEMANTIC-001`
2. **의존성 설치**: `pip install sentence-transformers faiss-cpu`
3. **테스트 작성**: acceptance.md의 Given-When-Then 시나리오 구현
4. **성능 벤치마크**: 키워드 vs 시맨틱 비교 측정

---

## 8. 참조

- spec.md: 전체 요구사항 및 EARS 명세
- acceptance.md: 상세 인수 기준 및 테스트 시나리오
