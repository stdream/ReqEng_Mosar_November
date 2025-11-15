// ================================================================================
// PDD 문서 Level 0, 1, 2 구조 조회 Cypher 쿼리 모음
// ================================================================================

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 1: 레벨별 통계 (Level 0-4까지 전체)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(s:Section)
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
WITH s.level as level,
     count(DISTINCT s) as section_count,
     count(DISTINCT c) as chunk_count
ORDER BY level
RETURN level,
       section_count,
       chunk_count,
       CASE WHEN section_count > 0
            THEN toFloat(chunk_count) / section_count
            ELSE 0 END as avg_chunks_per_section;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 2: Level 0 (Root Sections) 상세 정보
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(s:Section {level: 0})
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(child:Section)
RETURN s.number as number,
       s.title as title,
       count(DISTINCT c) as chunks,
       count(DISTINCT child) as subsections
ORDER BY s.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 3: Level 1 Sections 상세 정보
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(s:Section {level: 1})
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(child:Section)
RETURN s.number as number,
       s.title as title,
       count(DISTINCT c) as chunks,
       count(DISTINCT child) as subsections
ORDER BY s.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 4: Level 2 Sections 상세 정보
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(s:Section {level: 2})
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(child:Section)
RETURN s.number as number,
       s.title as title,
       count(DISTINCT c) as chunks,
       count(DISTINCT child) as subsections
ORDER BY s.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 5: Level 0, 1, 2 통합 조회 (들여쓰기 표시용)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(s:Section)
WHERE s.level IN [0, 1, 2]
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
WITH s, count(c) as chunk_count
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(child:Section)
RETURN s.level as level,
       s.number as number,
       s.title as title,
       chunk_count,
       count(child) as subsection_count
ORDER BY s.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 6: 계층 구조 트리 뷰 (Root -> Level 1 -> Level 2)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(root:Section {level: 0})
OPTIONAL MATCH (root)-[:HAS_SUBSECTION]->(level1:Section {level: 1})
OPTIONAL MATCH (level1)-[:HAS_SUBSECTION]->(level2:Section {level: 2})
OPTIONAL MATCH (root)-[:HAS_CHUNK]->(root_chunk:Chunk)
OPTIONAL MATCH (level1)-[:HAS_CHUNK]->(l1_chunk:Chunk)
OPTIONAL MATCH (level2)-[:HAS_CHUNK]->(l2_chunk:Chunk)
WITH root,
     count(DISTINCT root_chunk) as root_chunks,
     level1,
     count(DISTINCT l1_chunk) as level1_chunks,
     collect(DISTINCT {
         number: level2.number,
         title: level2.title,
         chunks: count(DISTINCT l2_chunk)
     }) as level2_children
ORDER BY root.number, level1.number
RETURN root.number as root_number,
       root.title as root_title,
       root_chunks,
       collect({
           number: level1.number,
           title: level1.title,
           chunks: level1_chunks,
           children: level2_children
       }) as level1_sections
ORDER BY root.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 7: 특정 Root Section의 전체 하위 트리 (예: Section 6)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(root:Section {level: 0, number: '6'})
OPTIONAL MATCH (root)-[:HAS_SUBSECTION*1..3]->(descendant:Section)
OPTIONAL MATCH (descendant)-[:HAS_CHUNK]->(c:Chunk)
RETURN root.number + ': ' + root.title as root_section,
       descendant.level as level,
       descendant.number as section_number,
       descendant.title as title,
       count(c) as chunks
ORDER BY descendant.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 8: 청크가 가장 많은 Section TOP 10 (Level 0-2)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(s:Section)
WHERE s.level IN [0, 1, 2]
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
WITH s, count(c) as chunk_count
WHERE chunk_count > 0
RETURN s.level as level,
       s.number as number,
       s.title as title,
       chunk_count
ORDER BY chunk_count DESC
LIMIT 10;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 9: 하위 섹션이 가장 많은 Section TOP 5
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(s:Section)
WHERE s.level IN [0, 1]
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(child:Section)
WITH s, count(child) as subsection_count
WHERE subsection_count > 0
RETURN s.level as level,
       s.number as number,
       s.title as title,
       subsection_count
ORDER BY subsection_count DESC
LIMIT 5;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 10: Section 경로 추적 (예: 6.1.2의 전체 경로)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH path = (d:Document {id: 'PDD'})-[:HAS_SECTION*1..5]->(target:Section {number: '6.1.2'})
WITH nodes(path) as nodes_in_path
UNWIND nodes_in_path as node
WITH node
WHERE 'Section' IN labels(node)
RETURN node.number as section_number,
       node.title as title,
       node.level as level
ORDER BY node.level;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 11: 빈 섹션 찾기 (청크가 없고 하위 섹션도 없는 경우)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})-[:HAS_SECTION]->(s:Section)
WHERE s.level IN [0, 1, 2]
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(child:Section)
WITH s, count(c) as chunk_count, count(child) as subsection_count
WHERE chunk_count = 0 AND subsection_count = 0
RETURN s.level as level,
       s.number as number,
       s.title as title
ORDER BY s.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 12: 전체 문서 구조 요약
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'PDD'})
OPTIONAL MATCH (d)-[:HAS_SECTION]->(s:Section)
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(sub:Section)
RETURN d.title as document,
       count(DISTINCT s) as total_sections,
       count(DISTINCT c) as total_chunks,
       count(DISTINCT sub) as total_subsection_relationships,
       avg(size((s)-[:HAS_CHUNK]->())) as avg_chunks_per_section;
