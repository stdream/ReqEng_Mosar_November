# 다음 세션 빠른 시작 가이드

## 🚀 바로 실행하기

### 현재 위치: Manual Vocabulary Review

**옵션 1: Vocabulary 그대로 사용 (빠른 진행)**
```bash
cd /c/Hee/SpaceAI/ReqEng_1114
mkdir -p config
cp output/entity_vocabulary_draft.json config/entity_vocabulary.json
# 다음: extract_entities_with_vocab.py 작성 필요
```

**옵션 2: Manual Review 후 사용 (권장)**
1. `output/entity_vocabulary_draft.json` 파일 열기
2. `human_review_needed: true` 항목 검토
3. Canonical names, aliases 수정
4. `config/entity_vocabulary.json`로 저장

---

## 📊 현재 완료된 작업

✅ Stage 1: COVERS relationships (53개)
✅ Stage 2: MENTIONS_REQUIREMENT (4,832개)
✅ Stage 3-A Phase 1: Entity candidates 추출 (1,659 chunks)
✅ Stage 3-A Phase 2: Clustering & Vocabulary (596 clusters)

---

## 📁 핵심 파일

### 결과 파일 (확인 가능):
- `output/entity_candidates_raw.json` - 추출된 entity 통계
- `output/entity_extractions_raw.json` - 전체 추출 결과
- `output/entity_clusters.json` - Clustering 결과 ✅ 새로 생성
- `output/entity_vocabulary_draft.json` - Vocabulary 초안 ✅ 새로 생성

### 다음 단계 스크립트 (작성 필요):
- `extract_entities_with_vocab.py` - ⏭️ 다음 작성 및 실행

### 문서:
- `SESSION_PROGRESS.md` - 상세 진행 상황
- `prd.md` - 업데이트된 PRD

---

## 🎯 현재 해야 할 일 (Manual Review)

**방법 1: Vocabulary 그대로 사용하고 바로 Phase 3로 진행**
```bash
mkdir -p config
cp output/entity_vocabulary_draft.json config/entity_vocabulary.json
```

**방법 2: Manual Review 수행 (권장)**

1. **Vocabulary 검토**:
   - VSCode에서 `output/entity_vocabulary_draft.json` 열기
   - `human_review_needed: true` 항목 찾기
   - 예시: WM, OBC-S, R-ICU, HOTDOCK, assembly scenario 등

2. **수정 사항**:
   - Canonical names: 가장 표준적인 이름으로 변경
   - full_name: 완전한 이름 추가 (예: "WM" → "Workspace Module")
   - Aliases: 불필요한 변형 제거
   - Type: HW/SW/FW 분류 (components만 해당)

3. **최종 저장**:
   ```bash
   mkdir -p config
   # JSON 파일 수정 후
   cp output/entity_vocabulary_draft.json config/entity_vocabulary.json
   ```

4. **Phase 3 준비**:
   - `extract_entities_with_vocab.py` 작성
   - Vocabulary 기반 entity + relationship 추출

---

## 💡 실제 Clustering 결과 (Phase 2 완료)

- Components: 349 clusters (1,199 variants → 71% reduction)
- Scenarios: 41 clusters (182 variants → 77% reduction)
- Test Cases: 45 clusters (279 variants → 84% reduction)
- Subsystems: 86 clusters (258 variants → 67% reduction)
- Interfaces: 75 clusters (183 variants → 59% reduction)

**총 596 clusters** (2,101 variants에서 clustering)

---

## 📞 문제 발생 시

1. `output` 디렉토리 없음 → `mkdir -p output`
2. Neo4j 연결 안됨 → `.env` 파일 확인
3. OpenAI API 오류 → `.env`의 `OPENAI_API_KEY` 확인

---

**현재 상태**: Phase 2 완료 ✅
**다음 단계**: Manual Vocabulary Review (선택) → Phase 3 Script 작성
