// SRD 문서의 Section Level 0 (Root)와 Level 1만 추출
// 계층 구조를 보여주는 쿼리

// Option 1: 간단한 버전 - Level 0과 1만 조회
MATCH (d:Document {id: 'SRD'})-[:HAS_SECTION]->(s:Section)
WHERE s.level IN [0, 1]
RETURN s.number as section_number,
       s.title as title,
       s.level as level
ORDER BY s.number;


// Option 2: 계층 구조를 보여주는 버전 - Parent-Child 관계 포함
MATCH (d:Document {id: 'SRD'})-[:HAS_SECTION]->(root:Section)
WHERE root.level = 0
OPTIONAL MATCH (root)-[:HAS_SUBSECTION]->(child:Section)
WHERE child.level = 1
RETURN root.number as root_number,
       root.title as root_title,
       collect({
           number: child.number,
           title: child.title
       }) as subsections
ORDER BY root.number;


// Option 3: 각 섹션의 청크 개수 포함
MATCH (d:Document {id: 'SRD'})-[:HAS_SECTION]->(s:Section)
WHERE s.level IN [0, 1]
OPTIONAL MATCH (s)-[:HAS_CHUNK]->(c:Chunk)
WITH s, count(c) as chunk_count
OPTIONAL MATCH (s)-[:HAS_SUBSECTION]->(child:Section)
RETURN s.number as section_number,
       s.title as title,
       s.level as level,
       chunk_count,
       count(child) as subsection_count
ORDER BY s.number;


// Option 4: 트리 구조로 표시 (Root -> Children)
MATCH (d:Document {id: 'SRD'})-[:HAS_SECTION]->(root:Section {level: 0})
OPTIONAL MATCH (root)-[:HAS_SUBSECTION]->(level1:Section {level: 1})
OPTIONAL MATCH (root)-[:HAS_CHUNK]->(root_chunk:Chunk)
OPTIONAL MATCH (level1)-[:HAS_CHUNK]->(l1_chunk:Chunk)
WITH root,
     count(DISTINCT root_chunk) as root_chunks,
     level1,
     count(DISTINCT l1_chunk) as level1_chunks
ORDER BY root.number, level1.number
RETURN root.number + ': ' + root.title as root_section,
       root_chunks,
       collect({
           section: level1.number + ': ' + level1.title,
           chunks: level1_chunks
       }) as children
ORDER BY root.number;


// Option 5: 가장 간결한 버전 - 번호와 제목만
MATCH (d:Document {id: 'SRD'})-[:HAS_SECTION]->(s:Section)
WHERE s.level = 0 OR s.level = 1
RETURN s.level as level,
       s.number as number,
       s.title as title
ORDER BY s.number;
