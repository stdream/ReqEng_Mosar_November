"""
Phase 4-B: Component-Centric Relationship Extraction

Extracts relationships between Components and other entities:
- CONNECTS_TO: Component ↔ Component (via interfaces)
- PART_OF: Component → Component (hierarchy)
- USES: Component → Interface
- REQUIRES: Component → Subsystem

Uses GPT-4o with multi-chunk context aggregation for comprehensive analysis.
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

MODEL = "gpt-4o"
BATCH_SIZE = 50

def extract_component_relationships(component: Dict, chunks: List[Dict], all_entities: Dict) -> Dict:
    """
    Extract relationships for a single component using all chunks mentioning it.

    Args:
        component: Component entity with name, full_name
        chunks: All chunks mentioning this component (aggregated context)
        all_entities: All available entities by category
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Aggregate context from multiple chunks
    # Group by document for better organization
    chunk_texts = {}
    for chunk in chunks[:20]:  # Limit to top 20 chunks
        doc_id = chunk.get('doc_id', 'UNKNOWN')
        if doc_id not in chunk_texts:
            chunk_texts[doc_id] = []
        chunk_texts[doc_id].append(chunk['text'][:600])

    # Build organized context
    context_parts = []
    for doc_id, texts in chunk_texts.items():
        context_parts.append(f"=== From {doc_id} ===")
        context_parts.extend(texts[:5])  # Max 5 chunks per document

    chunk_context = "\n\n".join(context_parts)

    # Build entity lists (exclude current component)
    components = [e['canonical_name'] for e in all_entities.get('components', [])
                  if e['canonical_name'] != component['canonical_name']][:80]
    interfaces = [e['canonical_name'] for e in all_entities.get('interfaces', [])]
    subsystems = [e['canonical_name'] for e in all_entities.get('subsystems', [])]
    scenarios = [e['canonical_name'] for e in all_entities.get('scenarios', [])]

    prompt = f"""You are a spacecraft system engineer analyzing component relationships.

COMPONENT: {component['canonical_name']}
Full Name: {component.get('full_name', component['canonical_name'])}
Type: Hardware/Software Component

COMPREHENSIVE CONTEXT (all mentions across documents):
{chunk_context}

KNOWN ENTITIES in the system:
- Other Components: {', '.join(components[:50])}...
- Interfaces: {', '.join(interfaces)}
- Subsystems: {', '.join(subsystems)}
- Scenarios: {', '.join(scenarios)}

TASK: Extract ALL relationships for this component.

Relationship types to identify:

1. CONNECTS_TO: Physical/logical connections to other components
   - Look for: "communicates with", "connected to", "interfaces with", "sends data to"
   - Include interface protocol if mentioned (SpaceWire, CAN, etc.)

2. PART_OF: Component hierarchy (this component is part of larger component/system)
   - Look for: "part of", "belongs to", "integrated into", "subsystem of"

3. USES: Interfaces/protocols this component uses
   - Look for: "uses", "via", "through", "SpaceWire interface", "CAN bus"

4. REQUIRES: Dependencies on subsystems
   - Look for: "requires", "depends on", "needs", "powered by"

INSTRUCTIONS:
- Analyze ALL context from multiple documents
- Cross-reference information for consistency
- Only include relationships with confidence >= 0.7
- Use EXACT entity names from KNOWN ENTITIES list
- Provide specific evidence from text
- For CONNECTS_TO, specify the interface/protocol if known

Return JSON:
{{
  "connects_to": [
    {{
      "target": "OBC-S",
      "target_type": "Component",
      "via": "SpaceWire",
      "evidence": "WM communicates with OBC-S via SpaceWire interface for telemetry",
      "confidence": 0.95,
      "bidirectional": true
    }}
  ],
  "part_of": [
    {{
      "target": "SM1-PWS",
      "target_type": "Component",
      "evidence": "cPDU is integrated into SM1-PWS power subsystem",
      "confidence": 0.90
    }}
  ],
  "uses": [
    {{
      "target": "SpaceWire",
      "target_type": "Interface",
      "evidence": "Component uses SpaceWire for high-speed data communication",
      "confidence": 0.95
    }}
  ],
  "requires": [
    {{
      "target": "Power",
      "target_type": "Subsystem",
      "evidence": "Component requires Power subsystem for operation",
      "confidence": 0.85
    }}
  ]
}}

Chain of thought:
1. Scan all context for explicit connection statements
2. Identify communication patterns and interfaces
3. Determine hierarchical relationships
4. Note dependencies on subsystems
5. Cross-validate information across documents
6. Assign confidence based on clarity and consistency
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert spacecraft systems engineer. Extract relationships with high precision using multi-source analysis."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            timeout=60
        )

        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"  ⚠️  Error processing {component['canonical_name']}: {e}", flush=True)
        return {}

def main():
    print("=" * 100, flush=True)
    print("  Phase 4-B: Component-Centric Relationship Extraction", flush=True)
    print("=" * 100, flush=True)
    print(flush=True)

    # Connect to Neo4j
    print("[1] Connecting to Neo4j...", flush=True)
    conn = Neo4jConnection()
    conn.connect()
    print("  ✓ Connected", flush=True)
    print(flush=True)

    # Load all components
    print("[2] Loading components...", flush=True)
    comp_query = """
    MATCH (c:Component)
    RETURN c.canonical_name as name, c.full_name as full_name, c.type as type
    ORDER BY c.canonical_name
    """
    comp_result = conn.execute_query(comp_query, {})
    components = [{"canonical_name": r["name"], "full_name": r["full_name"], "type": r.get("type")}
                  for r in comp_result]
    print(f"  ✓ Loaded {len(components)} components", flush=True)
    print(flush=True)

    # Load all entities for reference
    print("[3] Loading all entities...", flush=True)
    entity_query = """
    MATCH (e:Entity)
    RETURN e.canonical_name as name, e.category as category, e.full_name as full_name
    """
    entity_result = conn.execute_query(entity_query, {})

    all_entities = {}
    for r in entity_result:
        cat = r['category']
        if cat not in all_entities:
            all_entities[cat] = []
        all_entities[cat].append({
            'canonical_name': r['name'],
            'full_name': r['full_name']
        })

    print(f"  ✓ Loaded {sum(len(v) for v in all_entities.values())} entities", flush=True)
    print(flush=True)

    # For each component, find all chunks mentioning it
    print("[4] Finding component-chunk relationships...", flush=True)
    comp_chunks = {}

    for comp in components:
        query = """
        MATCH (c:Chunk)-[:MENTIONS]->(e:Component {canonical_name: $comp_name})
        RETURN c.id as chunk_id, c.text as text, 'UNKNOWN' as doc_id
        ORDER BY c.id
        """
        result = conn.execute_query(query, {"comp_name": comp['canonical_name']})
        comp_chunks[comp['canonical_name']] = [
            {"id": r["chunk_id"], "text": r["text"], "doc_id": r.get("doc_id", "UNKNOWN")}
            for r in result
        ]

    total_chunks = sum(len(chunks) for chunks in comp_chunks.values())
    print(f"  ✓ Found {total_chunks} component-chunk connections", flush=True)
    print(flush=True)

    # Extract relationships
    print(f"[5] Extracting relationships for {len(components)} components...", flush=True)
    print(f"  Using model: {MODEL}", flush=True)
    print(f"  Estimated time: {len(components) * 10 / 60:.1f} minutes", flush=True)
    print(f"  Estimated cost: ${len(components) * 0.03:.2f}", flush=True)
    print(flush=True)

    all_relationships = []
    start_time = time.time()

    for i, comp in enumerate(components, 1):
        comp_name = comp['canonical_name']
        chunks = comp_chunks.get(comp_name, [])

        if not chunks:
            continue

        if i % 20 == 0 or i == 1:
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            eta = (len(components) - i) / rate if rate > 0 else 0
            print(f"  Progress: {i}/{len(components)} - Rate: {rate:.2f} comp/sec - ETA: {eta/60:.1f} min", flush=True)

        result = extract_component_relationships(
            component=comp,
            chunks=chunks,
            all_entities=all_entities
        )

        # Parse results
        for rel_type, rels in result.items():
            if not rels:
                continue

            for rel in rels:
                all_relationships.append({
                    "source": comp_name,
                    "source_type": "Component",
                    "target": rel.get('target'),
                    "target_type": rel.get('target_type'),
                    "relation": rel_type.upper(),
                    "evidence": rel.get('evidence', ''),
                    "confidence": rel.get('confidence', 0.8),
                    "properties": {
                        "via": rel.get('via'),
                        "bidirectional": rel.get('bidirectional', False)
                    }
                })

    total_time = time.time() - start_time
    print(flush=True)
    print(f"  ✓ Extraction complete in {total_time/60:.1f} minutes", flush=True)
    print(f"  ✓ Found {len(all_relationships)} relationships", flush=True)
    print(flush=True)

    # Create relationships in Neo4j
    print("[6] Creating relationships in Neo4j...", flush=True)

    created = {
        "CONNECTS_TO": 0,
        "PART_OF": 0,
        "USES": 0,
        "REQUIRES": 0
    }

    for rel in all_relationships:
        rel_type = rel['relation']

        # Determine target label
        if rel['target_type'] == 'Component':
            target_label = 'Component'
        elif rel['target_type'] == 'Interface':
            target_label = 'Interface'
        elif rel['target_type'] == 'Subsystem':
            target_label = 'Subsystem'
        else:
            target_label = 'Entity'

        # Build query with properties
        if rel_type == 'CONNECTS_TO' and rel['properties'].get('via'):
            query = f"""
            MATCH (c1:Component {{canonical_name: $source}})
            MATCH (c2:{target_label} {{canonical_name: $target}})
            MERGE (c1)-[r:{rel_type}]->(c2)
            ON CREATE SET
                r.via = $via,
                r.evidence = $evidence,
                r.confidence = $confidence,
                r.created_at = datetime()
            RETURN count(r) as count
            """
            params = {
                "source": rel['source'],
                "target": rel['target'],
                "via": rel['properties']['via'],
                "evidence": rel['evidence'],
                "confidence": rel['confidence']
            }
        else:
            query = f"""
            MATCH (c1:Component {{canonical_name: $source}})
            MATCH (e:{target_label} {{canonical_name: $target}})
            MERGE (c1)-[r:{rel_type}]->(e)
            ON CREATE SET
                r.evidence = $evidence,
                r.confidence = $confidence,
                r.created_at = datetime()
            RETURN count(r) as count
            """
            params = {
                "source": rel['source'],
                "target": rel['target'],
                "evidence": rel['evidence'],
                "confidence": rel['confidence']
            }

        try:
            result = conn.execute_query(query, params)
            if result:
                created[rel_type] = created.get(rel_type, 0) + 1

                # Create reverse CONNECTS_TO if bidirectional
                if rel_type == 'CONNECTS_TO' and rel['properties'].get('bidirectional'):
                    reverse_query = query.replace('(c1)-[r:', '(c2)-[r:').replace('(c2)', '(c1_temp)')
                    reverse_query = reverse_query.replace('c1:', 'c2:').replace('c1_temp', 'c1')
                    conn.execute_query(reverse_query, params)

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

    with open("output/phase4b_results.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("=" * 100, flush=True)
    print("  PHASE 4-B COMPLETE", flush=True)
    print("=" * 100, flush=True)
    print(flush=True)
    print(f"Total relationships extracted: {len(all_relationships)}", flush=True)
    print(f"Processing time: {total_time/60:.1f} minutes", flush=True)
    print(f"Results saved to: output/phase4b_results.json", flush=True)
    print(flush=True)

    conn.close()

if __name__ == "__main__":
    main()
