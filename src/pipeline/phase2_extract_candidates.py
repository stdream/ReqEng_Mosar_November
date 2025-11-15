"""
Stage 3-A Phase 1: Entity Candidate Extraction

모든 1,659 chunks에서 entity 후보를 추출합니다.
정확도 우선: 모든 chunk를 빠짐없이 스캔
"""
import sys
import io
import os
import json
from typing import Dict, List, Set
from collections import defaultdict
from openai import OpenAI
from dotenv import load_dotenv
from tqdm import tqdm

sys.path.append('src')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from utils.neo4j_connection import Neo4jConnection

# Load environment
load_dotenv()

# Initialize OpenAI client (GPT-4o-mini for cost efficiency)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
MODEL = "gpt-4o-mini"  # 저렴하고 빠름


def extract_entities_from_chunk(chunk_text: str, chunk_id: str) -> Dict:
    """
    LLM을 사용하여 chunk에서 entity 후보를 추출합니다.

    정규화하지 않고 있는 그대로 추출 (clustering 단계에서 정규화)
    """
    prompt = f"""
Extract all technical entities mentioned in this text from a spacecraft engineering document.

Categories to extract:
1. COMPONENTS: Hardware/software modules (HOTDOCK, R-ICU, WM, cPDU, BAT, etc.)
2. SCENARIOS: Mission scenarios (S1, S2, Scenario 1, assembly scenario, etc.)
3. TEST_CASES: Test identifiers (CT-A-5, IT-1, Component Test, etc.)
4. SUBSYSTEMS: System categories (Power, Data, Thermal, Visual, etc.)
5. INTERFACES: Communication interfaces (SpaceWire, CAN, Ethernet, etc.)

Text:
{chunk_text}

Return JSON (list entities as you see them, NO normalization):
{{
  "components": ["HOTDOCK", "cPDU", "central PDU", ...],
  "scenarios": ["S1", "Scenario 1", "assembly scenario", ...],
  "test_cases": ["CT-A-5", ...],
  "subsystems": ["Power", "power system", ...],
  "interfaces": ["SpaceWire", "SpW", ...]
}}

Important:
- Extract EXACT names as they appear in text
- Include variations (e.g., "HOTDOCK" and "HOT-DOCK" are different at this stage)
- Only extract if clearly mentioned in the text
- Return empty array [] if category not found
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are an expert in extracting technical entities from spacecraft engineering documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,  # Deterministic
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)
        return result

    except Exception as e:
        print(f"Error extracting entities from {chunk_id}: {e}")
        return {
            "components": [],
            "scenarios": [],
            "test_cases": [],
            "subsystems": [],
            "interfaces": []
        }


def load_all_chunks(conn: Neo4jConnection) -> List[Dict]:
    """Neo4j에서 모든 chunk를 로드합니다."""
    query = """
    MATCH (c:Chunk)
    RETURN c.id as id, c.text as text
    ORDER BY c.id
    """
    results = conn.execute_query(query)

    chunks = []
    for r in results:
        chunks.append({
            "id": r["id"],
            "text": r["text"]
        })

    return chunks


def aggregate_entity_candidates(extractions: List[Dict]) -> Dict:
    """
    모든 추출 결과를 집계하여 entity별 통계 생성

    Returns:
        {
            "components": {
                "HOTDOCK": {"count": 45, "chunks": ["chunk_1", "chunk_5", ...]},
                "HOT-DOCK": {"count": 12, "chunks": ["chunk_3", ...]},
                ...
            },
            ...
        }
    """
    aggregated = {
        "components": defaultdict(lambda: {"count": 0, "chunks": []}),
        "scenarios": defaultdict(lambda: {"count": 0, "chunks": []}),
        "test_cases": defaultdict(lambda: {"count": 0, "chunks": []}),
        "subsystems": defaultdict(lambda: {"count": 0, "chunks": []}),
        "interfaces": defaultdict(lambda: {"count": 0, "chunks": []})
    }

    for extraction in extractions:
        chunk_id = extraction["chunk_id"]

        for category in ["components", "scenarios", "test_cases", "subsystems", "interfaces"]:
            entities = extraction.get(category, [])

            for entity in entities:
                aggregated[category][entity]["count"] += 1
                aggregated[category][entity]["chunks"].append(chunk_id)

    # Convert defaultdict to regular dict for JSON serialization
    result = {}
    for category, entities in aggregated.items():
        result[category] = {
            entity_name: {
                "count": data["count"],
                "chunks": data["chunks"]
            }
            for entity_name, data in entities.items()
        }

    return result


def print_statistics(aggregated: Dict):
    """추출 통계 출력"""
    print("\n" + "="*100)
    print("  ENTITY CANDIDATE EXTRACTION STATISTICS")
    print("="*100)

    for category in ["components", "scenarios", "test_cases", "subsystems", "interfaces"]:
        entities = aggregated[category]
        unique_count = len(entities)
        total_mentions = sum(e["count"] for e in entities.values())

        print(f"\n{category.upper()}:")
        print(f"  Unique variants: {unique_count}")
        print(f"  Total mentions: {total_mentions}")

        # Top 10 most mentioned
        if unique_count > 0:
            sorted_entities = sorted(
                entities.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:10]

            print(f"  Top 10 most mentioned:")
            for entity_name, data in sorted_entities:
                print(f"    {entity_name}: {data['count']} mentions")


def main():
    print("="*100)
    print("  Stage 3-A Phase 1: Entity Candidate Extraction")
    print("="*100)
    print("\nStrategy: ACCURACY FIRST - Scanning all 1,659 chunks")
    print("Model: GPT-4o-mini (cost-efficient)")

    # Connect to Neo4j
    print(f"\n[1] Connecting to Neo4j...")
    conn = Neo4jConnection()
    conn.connect()

    # Load all chunks
    print(f"\n[2] Loading all chunks...")
    chunks = load_all_chunks(conn)
    print(f"  Loaded {len(chunks)} chunks")

    conn.close()

    # Create output directory
    os.makedirs("output", exist_ok=True)

    # Extract entities from each chunk
    print(f"\n[3] Extracting entity candidates from {len(chunks)} chunks...")
    print(f"  This will take approximately {len(chunks) * 3 / 60:.1f} minutes")
    print(f"  Estimated cost: ${len(chunks) * 0.0002:.2f} (GPT-4o-mini)")

    extractions = []

    # Use tqdm for progress bar
    for chunk in tqdm(chunks, desc="Extracting entities", unit="chunk"):
        entities = extract_entities_from_chunk(chunk["text"], chunk["id"])
        entities["chunk_id"] = chunk["id"]
        extractions.append(entities)

        # Save intermediate results every 100 chunks
        if len(extractions) % 100 == 0:
            with open("output/entity_extractions_intermediate.json", "w", encoding="utf-8") as f:
                json.dump(extractions, f, indent=2, ensure_ascii=False)

    print(f"\n  ✓ Extracted entities from {len(extractions)} chunks")

    # Save raw extractions
    print(f"\n[4] Saving raw extractions...")
    os.makedirs("output", exist_ok=True)

    with open("output/entity_extractions_raw.json", "w", encoding="utf-8") as f:
        json.dump(extractions, f, indent=2, ensure_ascii=False)

    print(f"  Saved: output/entity_extractions_raw.json")

    # Aggregate by entity name
    print(f"\n[5] Aggregating entity candidates...")
    aggregated = aggregate_entity_candidates(extractions)

    with open("output/entity_candidates_raw.json", "w", encoding="utf-8") as f:
        json.dump(aggregated, f, indent=2, ensure_ascii=False)

    print(f"  Saved: output/entity_candidates_raw.json")

    # Print statistics
    print_statistics(aggregated)

    print("\n" + "="*100)
    print("  Phase 1 Complete!")
    print("="*100)
    print("\nNext step: Run cluster_entity_candidates.py for Phase 2 (Clustering)")


if __name__ == "__main__":
    main()
