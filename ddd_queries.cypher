// ================================================================================
// DDD (Detailed Design Document) Level 0, 1, 2 구조 조회 Cypher 쿼리 모음
// ================================================================================

// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 1: 레벨별 통계 (Level 0-5까지 전체)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(s:Section)
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
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(s:Section {level: 0})
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
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(s:Section {level: 1})
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
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(s:Section {level: 2})
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(child:Section)
RETURN s.number as number,
       s.title as title,
       count(DISTINCT c) as chunks,
       count(DISTINCT child) as subsections
ORDER BY s.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 5: Level 0, 1, 2 통합 조회 (가장 유용)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(s:Section)
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
// Query 6: 특정 Root Section의 전체 하위 트리 (예: Section 5 - Components Detailed Design)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(root:Section {level: 0, number: '5'})
OPTIONAL MATCH (root)-[:HAS_SUBSECTION*1..4]->(descendant:Section)
OPTIONAL MATCH (descendant)-[:HAS_CHUNK]->(c:Chunk)
RETURN root.number + ': ' + root.title as root_section,
       descendant.level as level,
       descendant.number as section_number,
       descendant.title as title,
       count(c) as chunks
ORDER BY descendant.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 7: 청크가 가장 많은 Section TOP 10 (Level 0-2)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(s:Section)
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
// Query 8: Hardware vs Software Reconfiguration 비교
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Section 3.1 (Hardware) vs 3.2 (Software) 하위 구조 비교
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(parent:Section)
WHERE parent.number IN ['3.1', '3.2']
OPTIONAL MATCH (parent)-[:HAS_SUBSECTION]->(child:Section)
OPTIONAL MATCH (child)-[:HAS_CHUNK]->(c:Chunk)
RETURN parent.number as parent_section,
       parent.title as parent_title,
       child.number as child_number,
       child.title as child_title,
       count(c) as chunks
ORDER BY parent.number, child.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 9: Components Detailed Design (Section 5) 전체 구조
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(section5:Section {number: '5'})
OPTIONAL MATCH (section5)-[:HAS_SUBSECTION]->(level1:Section)
OPTIONAL MATCH (level1)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (level1)-[:HAS_SUBSECTION]->(level2:Section)
WITH level1, count(DISTINCT c) as chunks, count(DISTINCT level2) as subsections
RETURN level1.number as component,
       level1.title as title,
       chunks,
       subsections
ORDER BY level1.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 10: System Operations (Section 4) 상세 구조
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(section4:Section {number: '4'})
OPTIONAL MATCH (section4)-[:HAS_SUBSECTION*1..3]->(descendant:Section)
OPTIONAL MATCH (descendant)-[:HAS_CHUNK]->(c:Chunk)
RETURN descendant.level as level,
       descendant.number as section_number,
       descendant.title as title,
       count(c) as chunks
ORDER BY descendant.number;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 11: 하위 섹션이 가장 많은 Section TOP 5
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(s:Section)
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
// Query 12: 전체 문서 구조 요약
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'DDD'})
OPTIONAL MATCH (d)-[:HAS_SECTION]->(s:Section)
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(sub:Section)
RETURN d.title as document,
       count(DISTINCT s) as total_sections,
       count(DISTINCT c) as total_chunks,
       count(DISTINCT sub) as total_subsection_relationships,
       avg(size((s)-[:HAS_CHUNK]->())) as avg_chunks_per_section;


// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
// Query 13: 빈 섹션 찾기 (청크도 없고 하위 섹션도 없는 경우)
// ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
MATCH (d:Document {id: 'DDD'})-[:HAS_SECTION]->(s:Section)
WHERE s.level IN [0, 1, 2]
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(child:Section)
WITH s, count(c) as chunk_count, count(child) as subsection_count
WHERE chunk_count = 0 AND subsection_count = 0
RETURN s.level as level,
       s.number as number,
       s.title as title
ORDER BY s.number;
