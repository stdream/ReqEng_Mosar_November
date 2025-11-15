"""
Stage 1: Build COVERS relationships from requirements CSV

Parses the 'covers' column from mosar_requirements_all.csv and creates
(Requirement)-[:COVERS]->(Requirement) relationships in Neo4j.

This establishes the foundation for requirement traceability.
"""
import sys
import io
import re
import pandas as pd
from typing import List, Set, Tuple

sys.path.append('src')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from utils.neo4j_connection import Neo4jConnection

# Requirement ID pattern: FuncR_S101, PerfR_S201, DesR_A406, etc.
REQ_ID_PATTERN = re.compile(r'\b(FuncR|PerfR|DesR|IntR|SafR)_([A-Z]\d{3})\b')


def extract_requirement_ids(text: str) -> List[str]:
    """
    Extract all requirement IDs from text and return just the ID part (without series prefix).

    Neo4j stores requirements with ID like "S101", not "FuncR_S101".
    The CSV 'covers' column has "FuncR_S112" but we need to extract just "S112".

    Examples:
        "FuncR_S112" -> ["S112"]
        "FuncR_S101, FuncR_S102" -> ["S101", "S102"]
        "Mission analysis RD2 FuncR_S115" -> ["S115"]
    """
    if pd.isna(text) or not text:
        return []

    matches = REQ_ID_PATTERN.findall(text)
    # Return only the ID part (e.g., "S112"), not the full display_id (e.g., "FuncR_S112")
    return [id_num for series, id_num in matches]


def load_covers_data(csv_path: str) -> List[Tuple[str, List[str]]]:
    """
    Load CSV and extract (source_req_id, [covered_req_ids]) pairs.

    Returns:
        List of (source_id, [covered_ids]) where source_id covers covered_ids
    """
    df = pd.read_csv(csv_path, encoding='latin-1')

    covers_data = []

    for _, row in df.iterrows():
        source_id = row['id']
        source_display_id = row['display_id']
        covers_text = row['covers']

        # Extract requirement IDs from covers column
        covered_ids = extract_requirement_ids(covers_text)

        if covered_ids:
            covers_data.append((source_id, covered_ids))

    return covers_data


def create_covers_relationships(conn: Neo4jConnection, covers_data: List[Tuple[str, List[str]]]):
    """
    Create COVERS relationships in Neo4j.

    For each (source, [targets]) pair:
        MATCH (source:Requirement {id: source})
        MATCH (target:Requirement {id: target})
        MERGE (source)-[:COVERS]->(target)
    """
    query = """
    MATCH (source:Requirement {id: $source_id})
    MATCH (target:Requirement {id: $target_id})
    MERGE (source)-[:COVERS]->(target)
    RETURN source.id, target.id
    """

    created = 0
    failed = 0
    failed_pairs = []

    for source_id, covered_ids in covers_data:
        for target_id in covered_ids:
            try:
                params = {"source_id": source_id, "target_id": target_id}
                result = conn.execute_query(query, params)
                if result:
                    created += 1
                    print(f"  ✓ {source_id} -[:COVERS]-> {target_id}")
                else:
                    failed += 1
                    failed_pairs.append((source_id, target_id))
                    print(f"  ✗ {source_id} -[:COVERS]-> {target_id} (not found)")
            except Exception as e:
                failed += 1
                failed_pairs.append((source_id, target_id))
                print(f"  ✗ {source_id} -[:COVERS]-> {target_id} (error: {e})")

    return created, failed, failed_pairs


def verify_covers_relationships(conn: Neo4jConnection):
    """
    Verify created COVERS relationships with statistics.
    """
    print("\n" + "="*100)
    print("  VERIFICATION: COVERS Relationship Statistics")
    print("="*100)

    # Total COVERS relationships
    query1 = """
    MATCH ()-[r:COVERS]->()
    RETURN count(r) as total_covers
    """
    result = conn.execute_query(query1)
    total_covers = result[0]['total_covers']
    print(f"\nTotal COVERS relationships: {total_covers}")

    # Requirements with outgoing COVERS
    query2 = """
    MATCH (r:Requirement)-[:COVERS]->()
    RETURN count(DISTINCT r) as reqs_with_covers
    """
    result = conn.execute_query(query2)
    reqs_with_covers = result[0]['reqs_with_covers']
    print(f"Requirements with outgoing COVERS: {reqs_with_covers}")

    # Requirements with incoming COVERS (covered by others)
    query3 = """
    MATCH ()-[:COVERS]->(r:Requirement)
    RETURN count(DISTINCT r) as reqs_covered
    """
    result = conn.execute_query(query3)
    reqs_covered = result[0]['reqs_covered']
    print(f"Requirements covered by others: {reqs_covered}")

    # Top 5 requirements by outgoing COVERS count
    query4 = """
    MATCH (r:Requirement)-[:COVERS]->(covered:Requirement)
    WITH r, count(covered) as cover_count
    ORDER BY cover_count DESC
    LIMIT 5
    RETURN r.id as req_id, r.title as title, cover_count
    """
    result = conn.execute_query(query4)
    if result:
        print(f"\nTop 5 requirements by outgoing COVERS count:")
        print(f"{'Req ID':<15} {'Covers Count':<15} {'Title':<60}")
        print("-"*95)
        for r in result:
            title = r['title'][:57] + "..." if len(r['title']) > 60 else r['title']
            print(f"{r['req_id']:<15} {r['cover_count']:<15} {title:<60}")

    # Top 5 most-covered requirements
    query5 = """
    MATCH (source:Requirement)-[:COVERS]->(r:Requirement)
    WITH r, count(source) as covered_by_count
    ORDER BY covered_by_count DESC
    LIMIT 5
    RETURN r.id as req_id, r.title as title, covered_by_count
    """
    result = conn.execute_query(query5)
    if result:
        print(f"\nTop 5 most-covered requirements (incoming COVERS):")
        print(f"{'Req ID':<15} {'Covered By':<15} {'Title':<60}")
        print("-"*95)
        for r in result:
            title = r['title'][:57] + "..." if len(r['title']) > 60 else r['title']
            print(f"{r['req_id']:<15} {r['covered_by_count']:<15} {title:<60}")


def main():
    print("="*100)
    print("  Stage 1: Build COVERS Relationships from CSV")
    print("="*100)

    csv_path = "Documents/mosar_requirements_all.csv"

    # Load covers data
    print(f"\n[1] Loading covers data from: {csv_path}")
    covers_data = load_covers_data(csv_path)

    total_sources = len(covers_data)
    total_targets = sum(len(targets) for _, targets in covers_data)

    print(f"  Found {total_sources} requirements with covers data")
    print(f"  Total COVERS relationships to create: {total_targets}")

    # Show examples
    print(f"\n[2] Examples of covers data:")
    for source, targets in covers_data[:5]:
        print(f"  {source} -> {', '.join(targets)}")

    # Connect to Neo4j
    print(f"\n[3] Connecting to Neo4j...")
    conn = Neo4jConnection()
    conn.connect()

    # Create relationships
    print(f"\n[4] Creating COVERS relationships...")
    created, failed, failed_pairs = create_covers_relationships(conn, covers_data)

    print(f"\n  Summary:")
    print(f"    ✓ Successfully created: {created}")
    print(f"    ✗ Failed: {failed}")

    if failed_pairs:
        print(f"\n  Failed pairs (requirement IDs not found in Neo4j):")
        for source, target in failed_pairs[:10]:
            print(f"    {source} -> {target}")
        if len(failed_pairs) > 10:
            print(f"    ... and {len(failed_pairs) - 10} more")

    # Verify
    print(f"\n[5] Verifying created relationships...")
    verify_covers_relationships(conn)

    conn.close()

    print("\n" + "="*100)
    print("  Stage 1 Complete!")
    print("="*100)


if __name__ == "__main__":
    main()
