"""
Add category labels to Entity nodes

Converts entity.category property to node labels for better querying:
- components -> :Component
- scenarios -> :Scenario
- test_cases -> :TestCase
- subsystems -> :Subsystem
- interfaces -> :Interface
"""
import sys
import io

sys.path.append('src')
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from utils.neo4j_connection import Neo4jConnection

# Category to Label mapping
CATEGORY_LABELS = {
    "components": "Component",
    "scenarios": "Scenario",
    "test_cases": "TestCase",
    "subsystems": "Subsystem",
    "interfaces": "Interface"
}

def add_category_labels(conn: Neo4jConnection):
    """Add category-based labels to all Entity nodes."""

    print("=" * 80, flush=True)
    print("  Adding Category Labels to Entity Nodes", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)

    total_updated = 0

    for category, label in CATEGORY_LABELS.items():
        print(f"Processing category: {category} -> :{label}", flush=True)

        # Add label to entities with this category
        query = f"""
        MATCH (e:Entity {{category: $category}})
        SET e:{label}
        RETURN count(e) as count
        """

        result = conn.execute_query(query, {"category": category})
        count = result[0]["count"] if result else 0
        total_updated += count

        print(f"  ✓ Updated {count} entities", flush=True)

    print(flush=True)
    print(f"Total updated: {total_updated} entities", flush=True)
    print(flush=True)

    # Verify results
    print("Verification:", flush=True)
    verify_query = """
    MATCH (e:Entity)
    RETURN e.category as category, labels(e) as labels, count(*) as count
    ORDER BY category
    """

    results = conn.execute_query(verify_query, {})
    for record in results:
        print(f"  {record['category']}: {record['labels']} - {record['count']} nodes", flush=True)

    print(flush=True)
    print("=" * 80, flush=True)
    print("  Complete!", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)

    # Show example queries
    print("Example queries:", flush=True)
    print("  MATCH (c:Component) RETURN c.canonical_name LIMIT 10", flush=True)
    print("  MATCH (s:Scenario) RETURN s.canonical_name", flush=True)
    print("  MATCH (t:TestCase) RETURN t.canonical_name", flush=True)
    print(flush=True)

def main():
    conn = Neo4jConnection()
    conn.connect()

    add_category_labels(conn)

    conn.close()

if __name__ == "__main__":
    main()
