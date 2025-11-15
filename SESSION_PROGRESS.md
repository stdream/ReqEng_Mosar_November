# GraphRAG Domain Graph 구축 - 세션 진행 상황

**마지막 업데이트**: 2025-11-15
**현재 단계**: Phase 3-B 완료 - Entity Nodes & MENTIONS Relationships 생성 완료 ✅

---

## ✅ 완료된 작업

### Stage 1: COVERS Relationships (완료)
- **파일**: `build_covers_relationships.py`
- **결과**: 53개 COVERS relationships 생성
- **통계**:
  - 42개 requirements가 다른 requirement를 covers
  - 34개 requirements가 다른 requirement에 의해 covered
  - Top: C801 (3), A110 (3), A101 (2)

### Stage 2: MENTIONS_REQUIREMENT (완료)
- **파일**: `extract_requirement_mentions_fast.py`
- **방법**: Embedding similarity (threshold=0.75)
- **결과**: 4,832개 MENTIONS_REQUIREMENT relationships 생성
- **통계**:
  - 98.3% chunk coverage (1,631/1,659)
  - 99.5% requirement coverage (219/220)
  - Top 언급: G101 (324), A102 (223), C801 (176)

### Stage 3-A Phase 1: Entity Candidate Extraction (완료) ✅
- **파일**: `extract_entity_candidates.py`
- **전략**: 정확도 우선 - 전체 1,659 chunks 스캔
- **모델**: GPT-4o-mini (비용 효율)
- **소요 시간**: 약 50분
- **비용**: $0.33

#### 추출 결과:

**COMPONENTS**: 1,199개 unique variants, 3,728번 언급
- WM: 276회
- R-ICU: 228회
- HOTDOCK: 206회
- cPDU: 157회
- OBC-S: 106회

**SCENARIOS**: 182개 unique variants, 375번 언급
- S1: 31회
- assembly scenario: 25회
- Scenario 1: 24회

**TEST_CASES**: 279개 unique variants, 437번 언급
- CT-A-5: 23회
- IT-1: 9회

**SUBSYSTEMS**: 258개 unique variants, 807번 언급
- Power: 186회
- Thermal: 54회

**INTERFACES**: 183개 unique variants, 736번 언급
- SpW: 127회
- SpaceWire: 105회
- CAN: 79회

#### 생성된 파일:
- ✅ `output/entity_extractions_raw.json` - 전체 추출 결과 (1,659 chunks)
- ✅ `output/entity_candidates_raw.json` - 집계된 entity 통계
- ✅ `output/entity_extractions_intermediate.json` - 중간 저장 (100 chunks마다)

### Stage 3-A Phase 2: Clustering & Vocabulary Construction (완료) ✅
- **파일**: `cluster_entity_candidates.py`
- **전략**: Hierarchical clustering (threshold=0.85)
- **모델**: OpenAI text-embedding-ada-002
- **소요 시간**: ~1분
- **비용**: ~$0.40 (embedding 생성)

#### Clustering 결과:

**COMPONENTS**: 1,199 variants → 349 clusters
- Human review 필요: 83 clusters (23.8%)
- Top clusters: WM (341 mentions, 15 variants), OBC-S (282 mentions, 24 variants), R-ICU (270 mentions, 14 variants)

**SCENARIOS**: 182 variants → 41 clusters
- Human review 필요: 11 clusters (26.8%)
- Top clusters: assembly scenario (122 mentions, 41 variants), S1 (58 mentions, 11 variants)

**TEST_CASES**: 279 variants → 45 clusters
- Human review 필요: 16 clusters (35.6%)
- Top clusters: FuncR_S105 (73 mentions, 33 variants), CT-A-5 (67 mentions, 38 variants)

**SUBSYSTEMS**: 258 variants → 86 clusters
- Human review 필요: 26 clusters (30.2%)
- Top clusters: Power (248 mentions, 14 variants), Thermal (115 mentions, 26 variants)

**INTERFACES**: 183 variants → 75 clusters
- Human review 필요: 16 clusters (21.3%)
- Top clusters: SpW (141 mentions, 10 variants), SpaceWire (106 mentions, 2 variants)

#### 생성된 파일:
- ✅ `output/entity_clusters.json` - 전체 clustering 결과
- ✅ `output/entity_vocabulary_draft.json` - Vocabulary 초안
- ✅ `config/entity_vocabulary.json` - Manual review 완료된 최종 vocabulary

### Phase 3-B: Entity Extraction & Neo4j 생성 (완료) ✅
- **파일**: `run_phase3_full.py`
- **전략**: Vocabulary 기반 entity 추출 (simplified approach)
- **모델**: GPT-4o-mini
- **소요 시간**: 61.1분
- **비용**: ~$0.50

#### 추출 결과:

**429개 Unique Entities**:
- **Components**: 298개 (WM, OBC-S, R-ICU, HOTDOCK, cPDU 등)
- **Subsystems**: 51개 (Power, Thermal, Data 등)
- **Interfaces**: 37개 (SpaceWire, CAN, RMAP 등)
- **Scenarios**: 23개 (S1, S2, assembly scenario 등)
- **Test Cases**: 21개 (CT-A-5, IT-1 등)

**6,284개 MENTIONS Relationships**: Chunk → Entity

#### Neo4j 데이터:
- ✅ 429 Entity nodes (각 category별 label 추가됨)
  - `:Entity:Component` (298)
  - `:Entity:Subsystem` (51)
  - `:Entity:Interface` (37)
  - `:Entity:Scenario` (23)
  - `:Entity:TestCase` (21)
- ✅ 6,284 MENTIONS relationships (Chunk → Entity)

#### 생성된 파일:
- ✅ `output/phase3_results.json` - 전체 Phase 3 결과

---

## 📋 다음 단계

### Phase 4: Entity-Entity Relationships (다음 작업)

**목표**: Entity 간 domain relationships 추출

**필요한 Relationships** (PRD 기준):
1. `ALLOCATED_TO`: Requirement → Component
2. `VERIFIED_BY`: Requirement → Test Case
3. `USED_IN`: Component → Scenario
4. `CONNECTS_TO`: Interface relationships
5. `PART_OF`: Component hierarchy
6. `REQUIRES`: Dependencies
2. LLM에 vocabulary 제공하여 정확한 추출
3. Entity nodes 생성 (MERGE로 중복 방지)
4. Chunk-Entity relationships 생성
5. **Entity-Entity relationships 생성** (핵심!)

**예상 결과**:
- ~25-30개 Component nodes
- ~5개 Scenario nodes
- ~40-60개 TestCase nodes
- ~10개 Subsystem nodes
- ~5,000-8,000개 Chunk-Entity relationships
- ~500-1,000개 Entity-Entity relationships

---

## 📊 Neo4j 현재 상태

### Nodes (예상):
- Chunks: 1,659
- Requirements: 220
- Documents: 4
- Sections: 527
- **Total**: ~2,410 nodes

### Relationships (현재):
- HAS_SECTION: 527
- HAS_SUBSECTION: 301
- HAS_CHUNK: 1,659
- NEXT_CHUNK: 1,208
- **COVERS**: 53 ✅ (Stage 1)
- **MENTIONS_REQUIREMENT**: 4,832 ✅ (Stage 2)
- **Total**: ~8,580 relationships

### Relationships (Stage 3 완료 후 예상):
- 기존: ~8,580
- 추가 (Chunk-Entity): ~5,000
- 추가 (Entity-Entity): ~500
- **예상 Total**: ~14,000 relationships

---

## 🔧 준비된 스크립트

### Phase 1 (완료):
- ✅ `extract_entity_candidates.py` - Entity 후보 추출

### Phase 2 (준비 완료):
- ✅ `cluster_entity_candidates.py` - Clustering & Vocabulary

### Phase 3 (준비 완료, 실행 대기):
- ✅ `extract_entities_with_vocab.py` - Vocabulary 기반 추출 (작성 필요)

---

## 💡 중요 결정사항 (PRD 반영됨)

### 1. Entity Resolution 전략
- **선택**: Controlled Vocabulary 방식 ✅
- **이유**: 중복 없음, 일관성, Graph 연결성
- **방법**: 2-Pass (Clustering → Manual Review → Vocabulary 기반 추출)

### 2. Entity 간 관계 추출
- **필수**: Entity만 추출하면 Graph Traversal 불가능
- **해결**: LLM으로 Entity + Relationships 동시 추출
- **관계 타입**:
  - ALLOCATED_TO: Requirement → Component
  - VERIFIED_BY: Requirement → TestCase
  - USED_IN: Component → Scenario
  - CONNECTS_TO: Component → Component
  - PART_OF: Component → Subsystem

### 3. 정확도 우선
- ✅ 전체 1,659 chunks 스캔 (샘플링 없음)
- ✅ Embedding similarity + LLM 기반 추출
- ✅ Manual review 포함

---

## 📝 PRD 업데이트 내역

1. **Section 5.4**: Entity-Chunk 연결 전략 (3가지 방법 비교)
2. **Section 5.4**: Entity 간 관계 추출 필수성
3. **Section 5.4**: Entity Resolution & Normalization (Controlled Vocabulary)
4. **Section 5.5**: GraphRAG 동작 메커니즘 (5-step flow)
5. **Section 5.5**: 일반 RAG vs GraphRAG 비교

---

## 🚀 다음 세션 시작 시 실행 명령어

```bash
# 1. Phase 2 실행 (Clustering)
cd /c/Hee/SpaceAI/ReqEng_1114
python cluster_entity_candidates.py

# 2. 출력 확인
cat output/entity_vocabulary_draft.json

# 3. 수동 검토 후 최종본 저장
# (JSON 파일 편집 후)
cp output/entity_vocabulary_draft.json config/entity_vocabulary.json

# 4. Phase 3 실행 (Vocabulary 기반 추출)
# (작성 필요: extract_entities_with_vocab.py)
python extract_entities_with_vocab.py
```

---

## 📂 주요 파일 위치

### 스크립트:
- `extract_entity_candidates.py` - Phase 1
- `cluster_entity_candidates.py` - Phase 2
- `build_covers_relationships.py` - Stage 1
- `extract_requirement_mentions_fast.py` - Stage 2

### 데이터:
- `output/entity_candidates_raw.json` - Phase 1 결과
- `output/entity_extractions_raw.json` - Phase 1 전체 추출
- `Documents/mosar_requirements_all.csv` - Requirements

### 설정:
- `prd.md` - 업데이트된 PRD
- `.env` - Neo4j & OpenAI credentials

---

## 🎯 최종 목표

**완성된 GraphRAG 시스템**:
1. ✅ Lexical Layer (Documents → Sections → Chunks)
2. ✅ Requirements + COVERS relationships
3. ✅ Chunk → Requirement links (MENTIONS_REQUIREMENT)
4. 🔄 Domain Layer (Components, Scenarios, Tests, Subsystems)
5. 🔄 Link Layer (Chunk → Entity)
6. 🔄 Entity-Entity relationships (ALLOCATED_TO, VERIFIED_BY, etc.)

**완료 시 가능한 쿼리**:
- "Requirement S112를 변경하면 어떤 영향이 있나?"
- "HOTDOCK과 관련된 모든 requirements, tests, scenarios는?"
- "S1 scenario에 사용되는 모든 components는?"
- "Power subsystem의 모든 requirements는?"

---

## 💰 비용 정리

- Stage 1 (COVERS): 무료 (CSV 파싱)
- Stage 2 (MENTIONS_REQUIREMENT): ~$0.50 (embedding similarity)
- **Stage 3-A Phase 1**: $0.33 (GPT-4o-mini, 1,659 chunks)
- Stage 3-A Phase 2 예상: ~$0.50 (embeddings)
- Stage 3-B 예상: ~$5-10 (GPT-4o-mini, entity + relationship extraction)

**Total 예상**: ~$6-11

---

**상태**: Phase 1 완료, Phase 2 실행 준비 완료
**다음 작업**: `python cluster_entity_candidates.py` 실행
