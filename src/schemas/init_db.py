"""
Initialize Neo4j database schema for MOSAR RM system
"""
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.neo4j_connection import Neo4jConnection, initialize_schema


def main():
    """Initialize Neo4j schema"""
    print("=" * 60)
    print("MOSAR Requirements Management System")
    print("Neo4j Schema Initialization")
    print("=" * 60)
    print()

    # Connect to Neo4j
    conn = Neo4jConnection()
    conn.connect()

    # Get current stats
    print("\n📊 Current Database Statistics:")
    stats = conn.get_database_stats()
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Relationships: {stats['total_relationships']}")

    if stats['total_nodes'] > 0:
        print("\n[WARNING]️  Database is not empty!")
        response = input("Do you want to clear the database first? (yes/no): ")
        if response.lower() in ['yes', 'y']:
            conn.clear_database(confirm=True)
        else:
            print("Proceeding without clearing...")

    # Initialize schema
    schema_file = os.path.join(
        os.path.dirname(__file__),
        "init_schema.cypher"
    )
    initialize_schema(conn, schema_file)

    # Show final stats
    print("\n📊 Final Database Statistics:")
    stats = conn.get_database_stats()
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Relationships: {stats['total_relationships']}")

    # Verify indexes
    print("\n🔍 Verifying Indexes:")
    indexes = conn.execute_query("SHOW INDEXES")
    print(f"  Total Indexes: {len(indexes)}")

    # Group by type
    index_types = {}
    for idx in indexes:
        idx_type = idx.get('type', 'UNKNOWN')
        index_types[idx_type] = index_types.get(idx_type, 0) + 1

    for idx_type, count in index_types.items():
        print(f"    {idx_type}: {count}")

    # Verify constraints
    print("\n🔒 Verifying Constraints:")
    constraints = conn.execute_query("SHOW CONSTRAINTS")
    print(f"  Total Constraints: {len(constraints)}")

    conn.close()
    print("\n✅ Schema initialization complete!")


if __name__ == "__main__":
    main()
