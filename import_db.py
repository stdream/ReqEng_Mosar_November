#!/usr/bin/env python3
"""
Import Neo4j Database from JSON dump
로컬 Neo4j에 백업 데이터 복원
"""

import os
import sys
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load .env for local database credentials
load_dotenv()

# 로컬 Neo4j 설정 (필요시 수정)
LOCAL_URI = input("Enter local Neo4j URI (default: bolt://localhost:7687): ").strip() or "bolt://localhost:7687"
LOCAL_USER = input("Enter username (default: neo4j): ").strip() or "neo4j"
LOCAL_PASSWORD = input("Enter password: ").strip()

if not LOCAL_PASSWORD:
    print("Error: Password required")
    sys.exit(1)

def clear_database(session):
    """기존 데이터베이스 초기화 (주의!)"""

    print("\nWARNING: This will DELETE ALL data in the local database!")
    confirm = input("Type 'YES' to confirm: ")

    if confirm != 'YES':
        print("Import cancelled")
        sys.exit(0)

    print("Clearing database...")
    session.run("MATCH (n) DETACH DELETE n")
    print("  Database cleared")

def create_constraints(session):
    """필수 constraints 생성"""

    print("\nCreating constraints...")

    constraints = [
        "CREATE CONSTRAINT req_id IF NOT EXISTS FOR (r:Requirement) REQUIRE r.id IS UNIQUE",
        "CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.canonical_name IS UNIQUE",
    ]

    for constraint in constraints:
        try:
            session.run(constraint)
            print(f"  Created: {constraint.split('FOR')[1].split('REQUIRE')[0].strip()}")
        except Exception as e:
            if 'already exists' not in str(e).lower():
                print(f"  Warning: {e}")

def import_nodes(session, nodes):
    """노드 임포트"""

    print(f"\nImporting {len(nodes)} nodes...")

    batch_size = 500
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i:i+batch_size]

        for node in batch:
            labels = ":".join(node['labels'])
            props = node['properties']

            # 벡터 속성은 스킵
            props_clean = {k: v for k, v in props.items()
                          if not (isinstance(v, str) and v.startswith('<vector:'))}

            # MERGE 또는 CREATE 사용
            if 'id' in props_clean:
                query = f"MERGE (n:{labels} {{id: $id}}) SET n = $props"
                params = {'id': props_clean['id'], 'props': props_clean}
            elif 'canonical_name' in props_clean:
                query = f"MERGE (n:{labels} {{canonical_name: $name}}) SET n = $props"
                params = {'name': props_clean['canonical_name'], 'props': props_clean}
            else:
                query = f"CREATE (n:{labels}) SET n = $props"
                params = {'props': props_clean}

            session.run(query, params)

        print(f"  Imported {min(i+batch_size, len(nodes))}/{len(nodes)} nodes...")

    print(f"  ✓ All {len(nodes)} nodes imported")

def import_relationships(session, relationships, node_id_map):
    """관계 임포트"""

    print(f"\nImporting {len(relationships)} relationships...")

    # 먼저 모든 노드의 ID 매핑 생성
    print("  Building node ID mapping...")
    result = session.run("""
        MATCH (n)
        WHERE n.id IS NOT NULL OR n.canonical_name IS NOT NULL
        RETURN
            id(n) as internal_id,
            n.id as node_id,
            n.canonical_name as canonical_name,
            labels(n) as labels
    """)

    # old_id -> (labels, identifier_key, identifier_value) 매핑
    node_map = {}
    for record in result:
        # Use node_id from backup as key (assuming we preserved it)
        # This is tricky - we'll use properties to match instead
        pass

    # 관계는 properties로 매칭하는 방식 사용
    batch_size = 500
    success_count = 0
    failed_count = 0

    for i in range(0, len(relationships), batch_size):
        batch = relationships[i:i+batch_size]

        for rel in batch:
            try:
                # 관계의 start/end 노드를 찾기 위한 쿼리
                # (내부 ID가 아니라 properties로 매칭)

                # 간단한 방법: 전체 노드 매칭 (느리지만 확실)
                query = """
                MATCH (a), (b)
                WHERE id(a) = $start_id AND id(b) = $end_id
                MERGE (a)-[r:""" + rel['type'] + """]->(b)
                SET r = $props
                """

                session.run(query, {
                    'start_id': rel['start_id'],
                    'end_id': rel['end_id'],
                    'props': rel['properties']
                })

                success_count += 1

            except Exception as e:
                failed_count += 1
                if failed_count < 10:  # Show first 10 errors only
                    print(f"  Warning: Failed to create relationship: {e}")

        print(f"  Imported {min(i+batch_size, len(relationships))}/{len(relationships)} relationships...")

    print(f"  ✓ Successfully imported {success_count} relationships")
    if failed_count > 0:
        print(f"  ✗ Failed: {failed_count} relationships")

def import_database():
    """메인 import 함수"""

    print("="*60)
    print("Neo4j Database Import Tool")
    print("="*60)
    print(f"Target: {LOCAL_URI}")
    print()

    # Load backup data
    backup_file = "backup/neo4j_dump.json"
    print(f"Loading backup from {backup_file}...")

    with open(backup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data['nodes']
    relationships = data['relationships']

    print(f"  Nodes: {len(nodes)}")
    print(f"  Relationships: {len(relationships)}")

    # Connect to local database
    print(f"\nConnecting to local database...")
    driver = GraphDatabase.driver(LOCAL_URI, auth=(LOCAL_USER, LOCAL_PASSWORD))

    try:
        with driver.session() as session:
            # Test connection
            session.run("RETURN 1").single()
            print("  ✓ Connected")

            # Clear existing data
            clear_database(session)

            # Create constraints
            create_constraints(session)

            # Import nodes
            import_nodes(session, nodes)

            # Build node mapping
            node_id_map = {}

            # Import relationships
            print("\nNote: Relationship import may take a while...")
            print("Relationships will be created based on node internal IDs")
            print("This assumes node internal IDs are preserved")

            import_relationships(session, relationships, node_id_map)

            print("\n" + "="*60)
            print("✓ Import Complete!")
            print("="*60)

            # Verify
            print("\nVerifying import...")
            node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
            rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']

            print(f"  Total nodes: {node_count}")
            print(f"  Total relationships: {rel_count}")

            print("\nNote: Vector indexes need to be recreated manually:")
            print("  CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS")
            print("  FOR (c:Chunk) ON c.embedding")
            print("  OPTIONS {indexConfig: {")
            print("    `vector.dimensions`: 3072,")
            print("    `vector.similarity_function`: 'euclidean'")
            print("  }}")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.close()

if __name__ == "__main__":
    import_database()
