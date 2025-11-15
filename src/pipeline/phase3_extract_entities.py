"""
Stage 3-B: Vocabulary-based Entity & Relationship Extraction

This script:
1. Loads the entity vocabulary from config/entity_vocabulary.json
2. Extracts entities from chunks using LLM with vocabulary context
3. Extracts relationships between entities
4. Creates Entity nodes in Neo4j
5. Creates MENTIONS relationships (Chunk -> Entity)
6. Creates domain relationships (Entity -> Entity)
"""

import sys
import io
import os
import json
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from openai import OpenAI

sys.path.append('src')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from utils.neo4j_connection import Neo4jConnection

load_dotenv()

# Configuration
MODEL = "gpt-4o-mini"
BATCH_SIZE = 100  # Save intermediate results every N chunks
CHECKPOINT_FILE = "output/entity_extraction_checkpoint.json"

# Relationship types according to PRD
RELATIONSHIP_TYPES = [
    "ALLOCATED_TO",   # Requirement -> Component
    "VERIFIED_BY",    # Requirement -> Test Case
    "USED_IN",        # Component -> Scenario
    "CONNECTS_TO",    # Interface relationship
    "PART_OF",        # Component hierarchy
    "REQUIRES",       # Dependency
    "IMPLEMENTS"      # Component implements Requirement
]

def load_vocabulary(vocab_path: str = "config/entity_vocabulary.json") -> Dict:
    """Load entity vocabulary from JSON file."""
    with open(vocab_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_vocabulary_context(vocabulary: Dict) -> str:
    """Build a concise vocabulary context string for LLM prompt."""
    context_parts = []

    for category, entities in vocabulary.items():
        if not entities:
            continue

        # Take top 30 entities per category (most mentioned)
        sorted_entities = sorted(entities, key=lambda x: x.get('total_mentions', 0), reverse=True)[:30]
        entity_names = [e['canonical_name'] for e in sorted_entities]

        context_parts.append(f"{category.upper()}: {', '.join(entity_names)}")

    return "\n".join(context_parts)

def normalize_entity_name(entity_name: str, vocabulary: Dict) -> Optional[Dict]:
    """
    Normalize an entity name using vocabulary.
    Returns: {"canonical_name": str, "full_name": str, "type": str, "category": str} or None
    """
    entity_lower = entity_name.lower().strip()

    for category, entities in vocabulary.items():
        for entity in entities:
            # Check canonical name
            if entity['canonical_name'].lower() == entity_lower:
                return {
                    "canonical_name": entity['canonical_name'],
                    "full_name": entity.get('full_name', entity['canonical_name']),
                    "type": entity.get('type', 'UNKNOWN'),
                    "category": category
                }

            # Check aliases
            for alias in entity.get('aliases', []):
                if alias.lower() == entity_lower:
                    return {
                        "canonical_name": entity['canonical_name'],
                        "full_name": entity.get('full_name', entity['canonical_name']),
                        "type": entity.get('type', 'UNKNOWN'),
                        "category": category
                    }

    return None

def extract_entities_and_relationships(chunk_text: str, chunk_id: str, vocab_context: str, vocabulary: Dict) -> Dict:
    """
    Extract entities and relationships from a chunk using LLM with vocabulary guidance.
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    prompt = f"""Extract technical entities and their relationships from this spacecraft engineering document text.

VOCABULARY (Use these canonical names):
{vocab_context}

IMPORTANT RULES:
1. Only extract entities that appear in the vocabulary above
2. Use the EXACT canonical names from the vocabulary
3. Extract relationships between entities (not chunk-entity relationships)
4. Provide evidence text from the chunk for each relationship

RELATIONSHIP TYPES:
- ALLOCATED_TO: Requirement allocated to Component
- VERIFIED_BY: Requirement verified by Test Case
- USED_IN: Component used in Scenario
- CONNECTS_TO: Interface connection
- PART_OF: Component hierarchy
- REQUIRES: Dependency between entities
- IMPLEMENTS: Component implements Requirement

TEXT:
{chunk_text}

Return JSON in this EXACT format:
{{
  "entities": [
    {{"name": "WM", "category": "components"}},
    {{"name": "S1", "category": "scenarios"}}
  ],
  "relationships": [
    {{
      "source": "S112",
      "relation": "ALLOCATED_TO",
      "target": "HOTDOCK",
      "evidence": "S112 defines electrical power requirements for HOTDOCK module",
      "confidence": 0.95
    }}
  ]
}}

If no entities or relationships found, return empty arrays.
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a technical document analyzer. Extract entities and relationships precisely."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Normalize all entity names using vocabulary
        normalized_entities = []
        for entity in result.get('entities', []):
            normalized = normalize_entity_name(entity['name'], vocabulary)
            if normalized:
                normalized_entities.append({
                    "name": entity['name'],  # Original mention
                    "canonical_name": normalized['canonical_name'],
                    "full_name": normalized['full_name'],
                    "type": normalized['type'],
                    "category": entity.get('category', normalized['category'])
                })

        # Normalize relationship entity names
        normalized_relationships = []
        for rel in result.get('relationships', []):
            source_norm = normalize_entity_name(rel['source'], vocabulary)
            target_norm = normalize_entity_name(rel['target'], vocabulary)

            if source_norm and target_norm:
                normalized_relationships.append({
                    "source": source_norm['canonical_name'],
                    "target": target_norm['canonical_name'],
                    "relation": rel['relation'],
                    "evidence": rel.get('evidence', ''),
                    "confidence": rel.get('confidence', 0.8),
                    "chunk_id": chunk_id
                })

        return {
            "chunk_id": chunk_id,
            "entities": normalized_entities,
            "relationships": normalized_relationships
        }

    except Exception as e:
        print(f"  ⚠️  Error extracting from chunk {chunk_id}: {e}")
        return {"chunk_id": chunk_id, "entities": [], "relationships": []}

def load_checkpoint() -> Dict:
    """Load checkpoint if exists."""
    if os.path.exists(CHECKPOINT_FILE):
        with open(CHECKPOINT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"processed_chunks": [], "entity_stats": {}, "relationship_stats": {}}

def save_checkpoint(checkpoint: Dict):
    """Save checkpoint."""
    with open(CHECKPOINT_FILE, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, indent=2, ensure_ascii=False)

def create_entity_nodes(conn: Neo4jConnection, entities: List[Dict]):
    """Create Entity nodes in Neo4j (idempotent using MERGE)."""
    query = """
    UNWIND $entities AS entity
    MERGE (e:Entity {canonical_name: entity.canonical_name})
    ON CREATE SET
        e.full_name = entity.full_name,
        e.type = entity.type,
        e.category = entity.category,
        e.created_at = datetime()
    ON MATCH SET
        e.full_name = entity.full_name,
        e.type = entity.type,
        e.category = entity.category
    RETURN count(e) as created_count
    """

    result = conn.execute_query(query, {"entities": entities})
    return result[0][0]['created_count'] if result[0] else 0

def create_chunk_entity_relationships(conn: Neo4jConnection, chunk_id: str, entity_names: List[str]):
    """Create MENTIONS relationships from Chunk to Entities."""
    query = """
    MATCH (c:Chunk {id: $chunk_id})
    UNWIND $entity_names AS entity_name
    MATCH (e:Entity {canonical_name: entity_name})
    MERGE (c)-[r:MENTIONS]->(e)
    ON CREATE SET r.created_at = datetime()
    RETURN count(r) as relationship_count
    """

    result = conn.execute_query(query, {"chunk_id": chunk_id, "entity_names": entity_names})
    return result[0]['relationship_count'] if result else 0

def create_entity_relationships(conn: Neo4jConnection, relationships: List[Dict]):
    """Create relationships between entities."""
    for rel in relationships:
        query = f"""
        MATCH (source:Entity {{canonical_name: $source}})
        MATCH (target:Entity {{canonical_name: $target}})
        MERGE (source)-[r:{rel['relation']}]->(target)
        ON CREATE SET
            r.evidence = $evidence,
            r.confidence = $confidence,
            r.chunk_id = $chunk_id,
            r.created_at = datetime()
        RETURN count(r) as created_count
        """

        params = {
            "source": rel['source'],
            "target": rel['target'],
            "evidence": rel.get('evidence', ''),
            "confidence": rel.get('confidence', 0.8),
            "chunk_id": rel.get('chunk_id', '')
        }

        try:
            conn.execute_query(query, params)
        except Exception as e:
            print(f"  ⚠️  Error creating relationship {rel['source']} -> {rel['target']}: {e}")

def main():
    print("=" * 100, flush=True)
    print("  Stage 3-B: Vocabulary-based Entity & Relationship Extraction", flush=True)
    print("=" * 100, flush=True)
    print(flush=True)

    # Load vocabulary
    print("[1] Loading entity vocabulary...", flush=True)
    vocabulary = load_vocabulary()
    vocab_context = build_vocabulary_context(vocabulary)
    total_vocab_size = sum(len(entities) for entities in vocabulary.values())
    print(f"  ✓ Loaded {total_vocab_size} canonical entities", flush=True)
    print(flush=True)

    # Connect to Neo4j
    print("[2] Connecting to Neo4j...")
    conn = Neo4jConnection()
    conn.connect()
    print("  ✓ Connected")
    print()

    # Get all chunks
    print("[3] Loading chunks from Neo4j...")
    chunk_query = """
    MATCH (c:Chunk)
    RETURN c.id as chunk_id, c.text as text
    ORDER BY c.id
    """
    chunks_result = conn.execute_query(chunk_query, {})
    chunks = [{"chunk_id": record['chunk_id'], "text": record['text']} for record in chunks_result]
    print(f"  ✓ Loaded {len(chunks)} chunks")
    print()

    # Load checkpoint
    checkpoint = load_checkpoint()
    processed_set = set(checkpoint.get('processed_chunks', []))
    remaining_chunks = [c for c in chunks if c['chunk_id'] not in processed_set]

    if processed_set:
        print(f"  📌 Resuming from checkpoint: {len(processed_set)} chunks already processed")
        print(f"  📌 Remaining: {len(remaining_chunks)} chunks")
        print()

    # Process chunks
    print(f"[4] Extracting entities and relationships from {len(remaining_chunks)} chunks...")
    print()

    all_entities = {}  # canonical_name -> entity info
    all_relationships = []
    chunk_entity_map = {}  # chunk_id -> [entity_canonical_names]

    start_time = time.time()

    for idx, chunk in enumerate(remaining_chunks, 1):
        chunk_id = chunk['chunk_id']
        chunk_text = chunk['text']

        if idx % 10 == 0 or idx == 1:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (len(remaining_chunks) - idx) / rate if rate > 0 else 0
            print(f"  Processing chunk {idx}/{len(remaining_chunks)} ({chunk_id}) - "
                  f"Rate: {rate:.1f} chunks/sec - ETA: {eta/60:.1f} min")

        result = extract_entities_and_relationships(chunk_text, chunk_id, vocab_context, vocabulary)

        # Collect entities
        chunk_entities = []
        for entity in result['entities']:
            canonical = entity['canonical_name']
            chunk_entities.append(canonical)

            if canonical not in all_entities:
                all_entities[canonical] = {
                    "canonical_name": canonical,
                    "full_name": entity['full_name'],
                    "type": entity['type'],
                    "category": entity['category']
                }

        chunk_entity_map[chunk_id] = chunk_entities

        # Collect relationships
        all_relationships.extend(result['relationships'])

        # Save checkpoint every BATCH_SIZE chunks
        if idx % BATCH_SIZE == 0:
            checkpoint['processed_chunks'].extend([c['chunk_id'] for c in remaining_chunks[idx-BATCH_SIZE:idx]])
            save_checkpoint(checkpoint)
            print(f"  💾 Checkpoint saved at chunk {idx}")

    # Final checkpoint
    checkpoint['processed_chunks'].extend([c['chunk_id'] for c in remaining_chunks])
    save_checkpoint(checkpoint)

    total_time = time.time() - start_time
    print()
    print(f"  ✓ Extraction complete in {total_time/60:.1f} minutes")
    print(f"  ✓ Found {len(all_entities)} unique entities")
    print(f"  ✓ Found {len(all_relationships)} relationships")
    print()

    # Create Entity nodes
    print("[5] Creating Entity nodes in Neo4j...")
    entity_list = list(all_entities.values())
    created_count = create_entity_nodes(conn, entity_list)
    print(f"  ✓ Created/updated {created_count} Entity nodes")
    print()

    # Create Chunk-Entity relationships
    print("[6] Creating MENTIONS relationships (Chunk -> Entity)...")
    total_mentions = 0
    for chunk_id, entity_names in chunk_entity_map.items():
        if entity_names:
            count = create_chunk_entity_relationships(conn, chunk_id, entity_names)
            total_mentions += count
    print(f"  ✓ Created {total_mentions} MENTIONS relationships")
    print()

    # Create Entity-Entity relationships
    print("[7] Creating domain relationships (Entity -> Entity)...")
    create_entity_relationships(conn, all_relationships)
    print(f"  ✓ Created {len(all_relationships)} domain relationships")
    print()

    # Statistics
    print("=" * 100)
    print("  PHASE 3 STATISTICS")
    print("=" * 100)
    print()

    print(f"Entities by category:")
    category_counts = {}
    for entity in all_entities.values():
        cat = entity['category']
        category_counts[cat] = category_counts.get(cat, 0) + 1

    for cat, count in sorted(category_counts.items()):
        print(f"  {cat}: {count}")
    print()

    print(f"Relationships by type:")
    rel_type_counts = {}
    for rel in all_relationships:
        rel_type = rel['relation']
        rel_type_counts[rel_type] = rel_type_counts.get(rel_type, 0) + 1

    for rel_type, count in sorted(rel_type_counts.items(), key=lambda x: -x[1]):
        print(f"  {rel_type}: {count}")
    print()

    # Save detailed results
    output_file = "output/entity_extraction_results.json"
    results = {
        "total_entities": len(all_entities),
        "total_relationships": len(all_relationships),
        "total_mentions": total_mentions,
        "category_counts": category_counts,
        "relationship_type_counts": rel_type_counts,
        "entities": entity_list,
        "relationships": all_relationships
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"  ✓ Detailed results saved to: {output_file}")
    print()

    print("=" * 100)
    print("  Phase 3 Complete!")
    print("=" * 100)
    print()
    print("Next steps:")
    print("1. Verify results in Neo4j:")
    print("   MATCH (e:Entity) RETURN e.category, count(e)")
    print("   MATCH ()-[r]->() WHERE type(r) IN ['ALLOCATED_TO', 'VERIFIED_BY', 'USED_IN'] RETURN type(r), count(r)")
    print("2. Test GraphRAG queries")
    print()

    conn.close()

if __name__ == "__main__":
    main()
