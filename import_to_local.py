#!/usr/bin/env python3
"""
Import to Local Neo4j - Automated
자동으로 로컬 Neo4j에 데이터 import
"""

import json
import sys
from neo4j import GraphDatabase
from tqdm import tqdm

# 로컬 Neo4j 설정
LOCAL_URI = "neo4j://127.0.0.1:7687"
LOCAL_USER = "neo4j"
LOCAL_PASSWORD = "password"
LOCAL_DB = "neo4j"

def clear_database(session):
    """기존 데이터 삭제"""
    print("\n[Step 1] Clearing existing database...")
    session.run("MATCH (n) DETACH DELETE n")
    print("  Database cleared")

def create_constraints(session):
    """제약조건 생성"""
    print("\n[Step 2] Creating constraints...")

    constraints = [
        ("Requirement ID", "CREATE CONSTRAINT req_id IF NOT EXISTS FOR (r:Requirement) REQUIRE r.id IS UNIQUE"),
        ("Document ID", "CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE"),
        ("Entity Name", "CREATE CONSTRAINT entity_name IF NOT EXISTS FOR (e:Entity) REQUIRE e.canonical_name IS UNIQUE"),
    ]

    for name, query in constraints:
        try:
            session.run(query)
            print(f"  Created: {name}")
        except Exception as e:
            if 'already exists' in str(e).lower():
                print(f"  Exists: {name}")
            else:
                print(f"  Warning: {name} - {e}")

def clean_properties(props):
    """속성 정리 (벡터 제외, DateTime 변환)"""
    clean_props = {}

    for key, value in props.items():
        # 벡터 데이터 스킵
        if isinstance(value, str) and value.startswith('<vector:'):
            continue

        # DateTime 문자열 처리
        if isinstance(value, str) and ('T' in value and (':' in value or 'Z' in value)):
            # ISO format datetime - 그냥 문자열로 저장
            clean_props[key] = value
        else:
            clean_props[key] = value

    return clean_props

def import_nodes(session, nodes):
    """노드 import"""
    print(f"\n[Step 3] Importing {len(nodes)} nodes...")

    batch_size = 500
    imported = 0

    # 노드 ID 매핑 저장 (old_id -> new_internal_id)
    node_map = {}

    with tqdm(total=len(nodes), desc="Importing nodes") as pbar:
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i+batch_size]

            for node in batch:
                old_id = node['node_id']
                labels = ":".join(node['labels'])
                props = clean_properties(node['properties'])

                if not props:
                    continue

                # 고유 키로 MERGE
                if 'id' in props:
                    query = f"MERGE (n:{labels} {{id: $id}}) SET n = $props RETURN id(n) as internal_id"
                    params = {'id': props['id'], 'props': props}
                elif 'canonical_name' in props:
                    query = f"MERGE (n:{labels} {{canonical_name: $name}}) SET n = $props RETURN id(n) as internal_id"
                    params = {'name': props['canonical_name'], 'props': props}
                else:
                    query = f"CREATE (n:{labels}) SET n = $props RETURN id(n) as internal_id"
                    params = {'props': props}

                try:
                    result = session.run(query, params)
                    record = result.single()
                    if record:
                        node_map[old_id] = record['internal_id']
                    imported += 1
                except Exception as e:
                    print(f"\n  Error importing node {labels}: {e}")

                pbar.update(1)

    print(f"  Imported: {imported} nodes")
    return node_map

def import_relationships(session, relationships, node_map):
    """관계 import"""
    print(f"\n[Step 4] Importing {len(relationships)} relationships...")

    batch_size = 500
    imported = 0
    skipped = 0

    with tqdm(total=len(relationships), desc="Importing relationships") as pbar:
        for i in range(0, len(relationships), batch_size):
            batch = relationships[i:i+batch_size]

            for rel in batch:
                start_id = rel['start_id']
                end_id = rel['end_id']
                rel_type = rel['type']
                props = clean_properties(rel.get('properties', {}))

                # 매핑된 내부 ID 찾기
                if start_id not in node_map or end_id not in node_map:
                    skipped += 1
                    pbar.update(1)
                    continue

                new_start_id = node_map[start_id]
                new_end_id = node_map[end_id]

                # 관계 생성
                if props:
                    query = f"""
                    MATCH (a), (b)
                    WHERE id(a) = $start_id AND id(b) = $end_id
                    MERGE (a)-[r:{rel_type}]->(b)
                    SET r = $props
                    """
                    params = {'start_id': new_start_id, 'end_id': new_end_id, 'props': props}
                else:
                    query = f"""
                    MATCH (a), (b)
                    WHERE id(a) = $start_id AND id(b) = $end_id
                    MERGE (a)-[:{rel_type}]->(b)
                    """
                    params = {'start_id': new_start_id, 'end_id': new_end_id}

                try:
                    session.run(query, params)
                    imported += 1
                except Exception as e:
                    if 'already exists' not in str(e).lower():
                        print(f"\n  Error importing relationship {rel_type}: {e}")
                    skipped += 1

                pbar.update(1)

    print(f"  Imported: {imported} relationships")
    if skipped > 0:
        print(f"  Skipped: {skipped} relationships")

def verify_import(session):
    """Import 검증"""
    print("\n[Step 5] Verifying import...")

    # Node 수
    node_count = session.run("MATCH (n) RETURN count(n) as count").single()['count']
    print(f"  Total nodes: {node_count}")

    # Relationship 수
    rel_count = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']
    print(f"  Total relationships: {rel_count}")

    # Label별 노드 수
    print("\n  Nodes by label:")
    result = session.run("""
        MATCH (n)
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    for record in result:
        print(f"    {record['label']}: {record['count']}")

    # Relationship 타입별 수
    print("\n  Relationships by type:")
    result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(r) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    for record in result:
        print(f"    {record['type']}: {record['count']}")

def main():
    print("="*60)
    print("Neo4j Database Import to Local")
    print("="*60)
    print(f"Target: {LOCAL_URI}")
    print(f"Database: {LOCAL_DB}")
    print()

    # Load backup
    backup_file = "backup/neo4j_dump.json"
    print(f"Loading backup from {backup_file}...")

    with open(backup_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data['nodes']
    relationships = data['relationships']

    print(f"  Nodes: {len(nodes)}")
    print(f"  Relationships: {len(relationships)}")

    # Connect
    print(f"\nConnecting to {LOCAL_URI}...")
    driver = GraphDatabase.driver(LOCAL_URI, auth=(LOCAL_USER, LOCAL_PASSWORD))

    try:
        with driver.session(database=LOCAL_DB) as session:
            # Test connection
            session.run("RETURN 1").single()
            print("  Connected successfully!")

            # Execute import
            clear_database(session)
            create_constraints(session)
            node_map = import_nodes(session, nodes)
            import_relationships(session, relationships, node_map)
            verify_import(session)

            print("\n" + "="*60)
            print("Import Complete!")
            print("="*60)

            print("\nNext steps:")
            print("1. Update .env file:")
            print("   NEO4J_URI=neo4j://127.0.0.1:7687")
            print("   NEO4J_USERNAME=neo4j")
            print("   NEO4J_PASSWORD=password")
            print()
            print("2. Recreate vector indexes (if needed):")
            print("   See DATABASE_MIGRATION_GUIDE.md")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        driver.close()

if __name__ == "__main__":
    main()
