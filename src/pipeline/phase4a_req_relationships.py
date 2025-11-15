"""
Phase 4-A: Requirement-Centric Relationship Extraction

Extracts relationships between Requirements and other entities:
- ALLOCATED_TO: Requirement → Component
- VERIFIED_BY: Requirement → TestCase
- USED_IN: Requirement → Scenario
- REQUIRES: Requirement → Subsystem/Interface

Uses GPT-4o for high-quality extraction with multi-chunk context.
"""
import sys
import io
import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from openai import OpenAI
import time

sys.path.append('src')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from utils.neo4j_connection import Neo4jConnection

load_dotenv()

MODEL = "gpt-4o"  # Use GPT-4o for higher quality
BATCH_SIZE = 50

def extract_requirement_relationships(req_id: str, req_text: str, chunks: List[Dict], entities: Dict) -> Dict:
    """
    Extract relationships for a single requirement using all related chunks.

    Args:
        req_id: Requirement ID (e.g., "S112")
        req_text: Requirement text
        chunks: List of chunks mentioning this requirement
        entities: Available entities by category
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Build context from all chunks
    chunk_context = "\n\n".join([
        f"[Chunk {i+1}] {chunk['text'][:800]}"
        for i, chunk in enumerate(chunks[:10])  # Limit to 10 chunks for context
    ])

    # Build entity lists
    components = [e['canonical_name'] for e in entities.get('components', [])][:100]
    test_cases = [e['canonical_name'] for e in entities.get('test_cases', [])]
    scenarios = [e['canonical_name'] for e in entities.get('scenarios', [])]
    subsystems = [e['canonical_name'] for e in entities.get('subsystems', [])]
    interfaces = [e['canonical_name'] for e in entities.get('interfaces', [])]

    prompt = f"""You are a spacecraft system engineer analyzing requirement relationships.

REQUIREMENT: {req_id}
Description: {req_text}

CONTEXT (chunks mentioning this requirement):
{chunk_context}

KNOWN ENTITIES in the system:
- Components: {', '.join(components[:50])}...
- Test Cases: {', '.join(test_cases)}
- Scenarios: {', '.join(scenarios)}
- Subsystems: {', '.join(subsystems)}
- Interfaces: {', '.join(interfaces)}

TASK: Extract ALL relationships between this requirement and entities.

Relationship types:
1. ALLOCATED_TO: This requirement is allocated to which component(s)?
   - Look for: "allocated to", "implements", "provides", "defines requirements for"

2. VERIFIED_BY: Which test case(s) verify this requirement?
   - Look for: "verified by", "tested by", "test case", "validation"

3. USED_IN: Which scenario(s) use this requirement?
   - Look for: scenario mentions, operational context

4. REQUIRES: Which subsystem(s) or interface(s) does this requirement need?
   - Look for: dependencies, "requires", "needs", "depends on"

INSTRUCTIONS:
- Be thorough but precise
- Only include relationships with confidence >= 0.7
- Provide evidence text from chunks
- Use EXACT entity names from the KNOWN ENTITIES list
- Include chunk numbers as references

Return JSON:
{{
  "allocated_to": [
    {{
      "entity": "HOTDOCK",
      "entity_type": "Component",
      "evidence": "S112 defines electrical power requirements for HOTDOCK module",
      "confidence": 0.95,
      "chunk_refs": [1, 3]
    }}
  ],
  "verified_by": [...],
  "used_in_scenarios": [...],
  "requires": [...]
}}

Chain of thought:
1. Scan all chunks for direct statements
2. Identify entities mentioned together with this requirement
3. Determine relationship type based on context
4. Assign confidence based on clarity of evidence
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert spacecraft systems engineer. Extract relationships with high precision."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            timeout=60
        )

        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"  ⚠️  Error processing {req_id}: {e}", flush=True)
        return {}

def main():
    print("=" * 100, flush=True)
    print("  Phase 4-A: Requirement-Centric Relationship Extraction", flush=True)
    print("=" * 100, flush=True)
    print(flush=True)

    # Connect to Neo4j
    print("[1] Connecting to Neo4j...", flush=True)
    conn = Neo4jConnection()
    conn.connect()
    print("  ✓ Connected", flush=True)
    print(flush=True)

    # Load all requirements
    print("[2] Loading requirements...", flush=True)
    req_query = """
    MATCH (r:Requirement)
    RETURN r.id as id, r.text as text, r.display_id as display_id
    ORDER BY r.id
    """
    req_result = conn.execute_query(req_query, {})
    requirements = [{"id": r["id"], "text": r["text"], "display_id": r["display_id"]} for r in req_result]
    print(f"  ✓ Loaded {len(requirements)} requirements", flush=True)
    print(flush=True)

    # Load all entities
    print("[3] Loading entities...", flush=True)
    entity_query = """
    MATCH (e:Entity)
    RETURN e.canonical_name as name, e.category as category, e.full_name as full_name
    """
    entity_result = conn.execute_query(entity_query, {})

    entities = {}
    for r in entity_result:
        cat = r['category']
        if cat not in entities:
            entities[cat] = []
        entities[cat].append({
            'canonical_name': r['name'],
            'full_name': r['full_name']
        })

    print(f"  ✓ Loaded {sum(len(v) for v in entities.values())} entities", flush=True)
    print(flush=True)

    # For each requirement, find related chunks
    print("[4] Finding requirement-chunk relationships...", flush=True)
    req_chunks = {}

    for req in requirements:
        query = """
        MATCH (r:Requirement {id: $req_id})<-[:MENTIONS_REQUIREMENT]-(c:Chunk)
        RETURN c.id as chunk_id, c.text as text
        """
        result = conn.execute_query(query, {"req_id": req['id']})
        req_chunks[req['id']] = [{"id": r["chunk_id"], "text": r["text"]} for r in result]

    total_chunks = sum(len(chunks) for chunks in req_chunks.values())
    print(f"  ✓ Found {total_chunks} requirement-chunk connections", flush=True)
    print(flush=True)

    # Extract relationships
    print(f"[5] Extracting relationships for {len(requirements)} requirements...", flush=True)
    print(f"  Using model: {MODEL}", flush=True)
    print(f"  Estimated time: {len(requirements) * 5 / 60:.1f} minutes", flush=True)
    print(f"  Estimated cost: ${len(requirements) * 0.02:.2f}", flush=True)
    print(flush=True)

    all_relationships = []
    start_time = time.time()

    for i, req in enumerate(requirements, 1):
        req_id = req['id']
        chunks = req_chunks.get(req_id, [])

        if not chunks:
            continue

        if i % 20 == 0 or i == 1:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(requirements) - i) / rate if rate > 0 else 0
            print(f"  Progress: {i}/{len(requirements)} - Rate: {rate:.2f} req/sec - ETA: {eta/60:.1f} min", flush=True)

        result = extract_requirement_relationships(
            req_id=req_id,
            req_text=req['text'],
            chunks=chunks,
            entities=entities
        )

        # Parse results and create relationship objects
        for rel_type, rels in result.items():
            if not rels:
                continue

            for rel in rels:
                all_relationships.append({
                    "source": req_id,
                    "source_type": "Requirement",
                    "target": rel.get('entity'),
                    "target_type": rel.get('entity_type'),
                    "relation": rel_type.upper(),
                    "evidence": rel.get('evidence', ''),
                    "confidence": rel.get('confidence', 0.8),
                    "chunk_refs": rel.get('chunk_refs', [])
                })

    total_time = time.time() - start_time
    print(flush=True)
    print(f"  ✓ Extraction complete in {total_time/60:.1f} minutes", flush=True)
    print(f"  ✓ Found {len(all_relationships)} relationships", flush=True)
    print(flush=True)

    # Create relationships in Neo4j
    print("[6] Creating relationships in Neo4j...", flush=True)

    created = {
        "ALLOCATED_TO": 0,
        "VERIFIED_BY": 0,
        "USED_IN_SCENARIOS": 0,
        "REQUIRES": 0
    }

    for rel in all_relationships:
        # Map relationship type to Cypher
        rel_type = rel['relation']

        # Find target node
        if rel['target_type'] == 'Component':
            target_label = 'Component'
        elif rel['target_type'] == 'TestCase':
            target_label = 'TestCase'
        elif rel['target_type'] == 'Scenario':
            target_label = 'Scenario'
        elif rel['target_type'] in ['Subsystem', 'Interface']:
            target_label = 'Entity'
        else:
            continue

        query = f"""
        MATCH (r:Requirement {{id: $source}})
        MATCH (e:{target_label} {{canonical_name: $target}})
        MERGE (r)-[rel:{rel_type}]->(e)
        ON CREATE SET
            rel.evidence = $evidence,
            rel.confidence = $confidence,
            rel.created_at = datetime()
        RETURN count(rel) as count
        """

        try:
            result = conn.execute_query(query, {
                "source": rel['source'],
                "target": rel['target'],
                "evidence": rel['evidence'],
                "confidence": rel['confidence']
            })

            if result:
                created[rel_type] = created.get(rel_type, 0) + 1
        except Exception as e:
            print(f"  ⚠️  Error creating {rel['source']} -> {rel['target']}: {e}", flush=True)

    print("  ✓ Relationships created:", flush=True)
    for rel_type, count in created.items():
        print(f"    {rel_type}: {count}", flush=True)
    print(flush=True)

    # Save results
    output = {
        "total_relationships": len(all_relationships),
        "created_in_neo4j": created,
        "processing_time_minutes": total_time / 60,
        "model": MODEL,
        "relationships": all_relationships
    }

    with open("output/phase4a_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("=" * 100, flush=True)
    print("  PHASE 4-A COMPLETE", flush=True)
    print("=" * 100, flush=True)
    print(flush=True)
    print(f"Total relationships extracted: {len(all_relationships)}", flush=True)
    print(f"Processing time: {total_time/60:.1f} minutes", flush=True)
    print(f"Results saved to: output/phase4a_results.json", flush=True)
    print(flush=True)

    conn.close()

if __name__ == "__main__":
    main()
