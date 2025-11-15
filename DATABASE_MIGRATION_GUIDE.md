# Neo4j Database Migration Guide

원격 Neo4j → 로컬 Neo4j 데이터베이스 마이그레이션 가이드

## 📊 현재 상태

**원격 Database**: `bolt://44.195.40.3:7687`
- Total Nodes: 2,853
- Total Relationships: 15,225
- Database Size: ~50MB

**백업 완료**: ✅
- Location: `backup/neo4j_dump.json`
- Statistics: `backup/statistics.json`

---

## 🚀 방법 1: JSON Dump 방식 (권장)

### 장점
- ✅ 가장 안전하고 확실
- ✅ 진행 상황 확인 가능
- ✅ 버전 독립적

### 단계

#### 1. 원격 DB에서 Export (완료)

```bash
python export_db.py
```

**출력**:
- `backup/neo4j_dump.json` - 전체 데이터
- `backup/statistics.json` - 통계 정보

#### 2. 로컬 Neo4j 설치 및 시작

**Windows**:
```bash
# Neo4j Desktop 사용 권장
# 또는 Community Edition 설치

# 새 데이터베이스 생성
# Database Name: mosar-local
# Password: (설정)

# 데이터베이스 시작
```

**Docker 사용 (권장)**:
```bash
docker run -d \
  --name neo4j-local \
  -p 7474:7474 \
  -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/your_password \
  -e NEO4J_PLUGINS='["apoc"]' \
  neo4j:5.14.0
```

#### 3. Import to Local

```bash
# 환경 변수 확인
# LOCAL_NEO4J_URI=bolt://localhost:7687
# LOCAL_NEO4J_USER=neo4j
# LOCAL_NEO4J_PASSWORD=your_password

# Import 실행
python import_db.py
```

**대화형 프롬프트**:
```
Enter local Neo4j URI (default: bolt://localhost:7687): [Enter]
Enter username (default: neo4j): [Enter]
Enter password: your_password
```

**경고 확인**:
```
WARNING: This will DELETE ALL data in the local database!
Type 'YES' to confirm: YES
```

**진행 과정**:
```
Clearing database...
Creating constraints...
Importing 2853 nodes...
  Imported 500/2853 nodes...
  Imported 1000/2853 nodes...
  ...
  ✓ All 2853 nodes imported
Importing 15225 relationships...
  Imported 500/15225 relationships...
  ...
  ✓ Successfully imported 15225 relationships
```

#### 4. Vector Index 재생성

Import 완료 후 Neo4j Browser에서 실행:

```cypher
// Chunk embedding vector index
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:Chunk) ON c.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 3072,
  `vector.similarity_function`: 'euclidean'
}};
```

**Note**: Vector 데이터는 용량 문제로 export되지 않았습니다.
필요시 원본 임베딩을 재생성해야 합니다.

---

## 🔄 방법 2: APOC Export/Import (빠름)

### 전제조건
- 원격 및 로컬 Neo4j 모두 APOC 플러그인 설치 필요

### Export (원격 DB에서)

```cypher
// Neo4j Browser에서 실행
CALL apoc.export.cypher.all("mosar_backup.cypher", {
  format: 'cypher-shell',
  useOptimizations: {type: 'UNWIND_BATCH', unwindBatchSize: 20}
})
```

### Import (로컬 DB에서)

```bash
# 1. 백업 파일 다운로드
# mosar_backup.cypher 파일을 로컬로 복사

# 2. cypher-shell로 실행
cat mosar_backup.cypher | cypher-shell -u neo4j -p your_password
```

---

## 🛠️ 방법 3: Neo4j Admin Dump/Load (프로덕션급)

### 전제조건
- 원격 서버 SSH 접근 권한 필요
- Neo4j 서버 관리자 권한

### Export

```bash
# 원격 서버에서
neo4j-admin database dump neo4j --to-path=/backup
```

### Import

```bash
# 로컬에서
# 1. 덤프 파일 다운로드
scp user@44.195.40.3:/backup/neo4j.dump ./

# 2. 로컬 Neo4j 중지
neo4j stop

# 3. Import
neo4j-admin database load neo4j --from-path=./ --overwrite-destination

# 4. 재시작
neo4j start
```

---

## 📋 데이터 검증

Import 완료 후 검증 쿼리:

### 1. Node 수 확인

```cypher
MATCH (n)
RETURN labels(n) as label, count(n) as count
ORDER BY count DESC
```

**Expected**:
```
Chunk         1,659
Section       527
Entity        443
Requirement   220
Component     298
...
```

### 2. Relationship 수 확인

```cypher
MATCH ()-[r]->()
RETURN type(r) as rel_type, count(r) as count
ORDER BY count DESC
```

**Expected**:
```
MENTIONS             5,610
MENTIONS_REQUIREMENT 4,832
HAS_CHUNK            1,659
...
```

### 3. 데이터 무결성 확인

```cypher
// 고아 노드 확인 (연결이 없는 노드)
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n), count(n)

// 결과: 없어야 정상
```

### 4. 샘플 데이터 확인

```cypher
// FuncR_S112 요구사항 확인
MATCH (r:Requirement {id: 'S112'})
OPTIONAL MATCH (r)-[:ALLOCATED_TO]->(comp)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(test)
RETURN r, comp, test
```

---

## 🔧 문제 해결

### Import 실패 시

**1. 메모리 부족**
```bash
# Neo4j 메모리 설정 증가
# neo4j.conf:
server.memory.heap.initial_size=1G
server.memory.heap.max_size=2G
```

**2. Timeout**
```bash
# Import 스크립트 batch size 조정
# import_db.py:
batch_size = 100  # 기본 500에서 감소
```

**3. Relationship 매칭 실패**
- Node ID가 보존되지 않은 경우
- Properties로 매칭하도록 수정 필요
- 수동으로 MERGE 쿼리 작성

### Vector Index 재생성

Embedding이 없는 경우:

```python
# Phase 3 재실행하여 임베딩 생성
python src/pipeline/phase3_extract_entities.py
```

---

## 📈 성능 최적화

### Import 속도 향상

1. **Batch Size 조정**
```python
batch_size = 1000  # 더 큰 배치
```

2. **Transaction 최적화**
```python
with session.begin_transaction() as tx:
    for node in batch:
        tx.run(query, params)
    tx.commit()
```

3. **Parallel Import**
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    executor.map(import_batch, batches)
```

---

## 📝 .env 설정

로컬 Neo4j 사용 시:

```bash
# .env.local
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_local_password
NEO4J_DATABASE=neo4j

OPENAI_API_KEY=sk-...
```

---

## ✅ 최종 체크리스트

- [ ] 원격 DB 백업 완료 (`export_db.py`)
- [ ] 로컬 Neo4j 설치 및 시작
- [ ] 데이터 Import 완료 (`import_db.py`)
- [ ] Node 수 검증 (2,853개)
- [ ] Relationship 수 검증 (15,225개)
- [ ] Constraints 생성 확인
- [ ] Vector Index 재생성 (필요시)
- [ ] 샘플 쿼리 테스트
- [ ] `.env` 파일 로컬 DB로 업데이트

---

## 🎯 Quick Start (권장 방법)

```bash
# 1. Export (이미 완료됨)
python export_db.py  # ✅ Done

# 2. 로컬 Neo4j 시작 (Docker)
docker run -d \
  --name neo4j-mosar \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/mosar2024 \
  neo4j:5.14.0

# 3. Import
python import_db.py
# URI: bolt://localhost:7687
# User: neo4j
# Password: mosar2024
# Confirm: YES

# 4. 접속 확인
# Browser: http://localhost:7474
# Connect: bolt://localhost:7687

# 5. .env 업데이트
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=mosar2024
```

---

**Last Updated**: 2025-11-15
**Database Version**: Neo4j 5.14.0
**Backup Size**: ~50MB (JSON), ~2,853 nodes, ~15,225 relationships
