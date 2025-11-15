#!/usr/bin/env python3
"""
Neo4j Database Backup Script
원격 Neo4j DB를 Cypher 스크립트로 백업
"""

import os
from neo4j import GraphDatabase
from pathlib import Path
import json
from datetime import datetime

# Remote DB 설정
REMOTE_URI = os.getenv("NEO4J_URI", "bolt://44.195.40.3:7687")
REMOTE_USER = os.getenv("NEO4J_USER", "neo4j")
REMOTE_PASSWORD = os.getenv("NEO4J_PASSWORD")

def export_to_cypher(driver, output_file="backup/neo4j_backup.cypher"):
    """모든 데이터를 Cypher 스크립트로 내보내기"""

    # 출력 디렉토리 생성
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"📦 Backing up Neo4j database to {output_file}")

    with driver.session() as session:
        with open(output_file, 'w', encoding='utf-8') as f:
            # 헤더
            f.write(f"// Neo4j Database Backup\n")
            f.write(f"// Generated: {datetime.now().isoformat()}\n")
            f.write(f"// Source: {REMOTE_URI}\n\n")

            # 1. Constraints 및 Indexes 내보내기
            print("  📋 Exporting constraints and indexes...")
            f.write("// ============================================\n")
            f.write("// CONSTRAINTS AND INDEXES\n")
            f.write("// ============================================\n\n")

            # Constraints
            constraints = session.run("SHOW CONSTRAINTS")
            for record in constraints:
                try:
                    constraint_name = record.get('name', '')
                    constraint_type = record.get('type', '')
                    if 'UNIQUENESS' in constraint_type or 'UNIQUE' in constraint_type:
                        f.write(f"// Constraint: {constraint_name}\n")
                except:
                    pass

            f.write("\n")

            # Indexes
            indexes = session.run("SHOW INDEXES")
            for record in indexes:
                try:
                    index_name = record.get('name', '')
                    index_type = record.get('type', '')
                    if 'VECTOR' in index_type:
                        f.write(f"// Vector Index: {index_name}\n")
                        f.write(f"// (Recreate manually with correct dimensions)\n\n")
                except:
                    pass

            # 2. Nodes 내보내기
            print("  📦 Exporting nodes...")
            f.write("// ============================================\n")
            f.write("// NODES\n")
            f.write("// ============================================\n\n")

            # 모든 label 가져오기
            labels_result = session.run("CALL db.labels()")
            labels = [record["label"] for record in labels_result]

            node_count = 0
            for label in labels:
                print(f"    - Exporting :{label} nodes...")

                # 각 label의 모든 노드 가져오기
                query = f"MATCH (n:{label}) RETURN n"
                result = session.run(query)

                for record in result:
                    node = record["n"]
                    props = dict(node)

                    # embedding 같은 큰 속성은 제외
                    if 'embedding' in props:
                        props['embedding'] = f"<vector of {len(props['embedding'])} dimensions>"

                    # Properties를 Cypher 형식으로 변환
                    props_str = json.dumps(props, ensure_ascii=False)

                    # MERGE 쿼리 생성 (중복 방지)
                    # ID가 있으면 ID로, 없으면 다른 unique 속성 사용
                    if 'id' in props:
                        f.write(f"MERGE (n:{label} {{id: {json.dumps(props['id'])}}})\n")
                        f.write(f"SET n = {props_str};\n\n")
                    elif 'canonical_name' in props:
                        f.write(f"MERGE (n:{label} {{canonical_name: {json.dumps(props['canonical_name'])}}})\n")
                        f.write(f"SET n = {props_str};\n\n")
                    else:
                        # ID가 없는 경우 CREATE 사용 (주의: 중복 가능)
                        f.write(f"CREATE (n:{label})\n")
                        f.write(f"SET n = {props_str};\n\n")

                    node_count += 1

                    if node_count % 100 == 0:
                        print(f"      {node_count} nodes exported...")

            print(f"  ✅ Total {node_count} nodes exported")

            # 3. Relationships 내보내기
            print("  🔗 Exporting relationships...")
            f.write("// ============================================\n")
            f.write("// RELATIONSHIPS\n")
            f.write("// ============================================\n\n")

            # 모든 relationship type 가져오기
            rel_types_result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in rel_types_result]

            rel_count = 0
            for rel_type in rel_types:
                print(f"    - Exporting :{rel_type} relationships...")

                # MATCH 쿼리로 관계 가져오기
                query = f"""
                MATCH (a)-[r:{rel_type}]->(b)
                RETURN
                    labels(a) as start_labels,
                    a.id as start_id,
                    a.canonical_name as start_canonical_name,
                    type(r) as rel_type,
                    properties(r) as rel_props,
                    labels(b) as end_labels,
                    b.id as end_id,
                    b.canonical_name as end_canonical_name
                LIMIT 10000
                """

                result = session.run(query)

                for record in result:
                    start_labels = ":".join(record["start_labels"])
                    end_labels = ":".join(record["end_labels"])

                    # Start node 식별
                    if record["start_id"]:
                        start_match = f"(a:{start_labels} {{id: {json.dumps(record['start_id'])}}})"
                    elif record["start_canonical_name"]:
                        start_match = f"(a:{start_labels} {{canonical_name: {json.dumps(record['start_canonical_name'])}}})"
                    else:
                        continue  # Skip if no identifier

                    # End node 식별
                    if record["end_id"]:
                        end_match = f"(b:{end_labels} {{id: {json.dumps(record['end_id'])}}})"
                    elif record["end_canonical_name"]:
                        end_match = f"(b:{end_labels} {{canonical_name: {json.dumps(record['end_canonical_name'])}}})"
                    else:
                        continue

                    # Relationship properties
                    rel_props = record["rel_props"]
                    if rel_props:
                        props_str = json.dumps(rel_props, ensure_ascii=False)
                        f.write(f"MATCH {start_match}, {end_match}\n")
                        f.write(f"MERGE (a)-[r:{rel_type}]->(b)\n")
                        f.write(f"SET r = {props_str};\n\n")
                    else:
                        f.write(f"MATCH {start_match}, {end_match}\n")
                        f.write(f"MERGE (a)-[:{rel_type}]->(b);\n\n")

                    rel_count += 1

                    if rel_count % 100 == 0:
                        print(f"      {rel_count} relationships exported...")

            print(f"  ✅ Total {rel_count} relationships exported")

    print(f"\n✅ Backup completed: {output_file}")
    print(f"   Nodes: {node_count}")
    print(f"   Relationships: {rel_count}")

    return output_file

def export_statistics(driver, output_file="backup/statistics.json"):
    """데이터베이스 통계 내보내기"""

    print(f"\n📊 Exporting database statistics...")

    stats = {}

    with driver.session() as session:
        # Node counts
        labels_result = session.run("CALL db.labels()")
        labels = [record["label"] for record in labels_result]

        stats['nodes'] = {}
        for label in labels:
            count = session.run(f"MATCH (n:{label}) RETURN count(n) as count").single()["count"]
            stats['nodes'][label] = count

        # Relationship counts
        rel_types_result = session.run("CALL db.relationshipTypes()")
        rel_types = [record["relationshipType"] for record in rel_types_result]

        stats['relationships'] = {}
        for rel_type in rel_types:
            count = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count").single()["count"]
            stats['relationships'][rel_type] = count

        # Total counts
        total_nodes = session.run("MATCH (n) RETURN count(n) as count").single()["count"]
        total_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()["count"]

        stats['totals'] = {
            'nodes': total_nodes,
            'relationships': total_rels
        }

    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    print(f"✅ Statistics saved: {output_file}")
    print(f"\n📊 Database Summary:")
    print(f"   Total Nodes: {stats['totals']['nodes']}")
    print(f"   Total Relationships: {stats['totals']['relationships']}")

    return stats

def main():
    print("="*60)
    print("Neo4j Database Backup Tool")
    print("="*60)
    print(f"Source: {REMOTE_URI}")
    print()

    if not REMOTE_PASSWORD:
        print("❌ Error: NEO4J_PASSWORD environment variable not set")
        return

    # Connect to remote database
    driver = GraphDatabase.driver(REMOTE_URI, auth=(REMOTE_USER, REMOTE_PASSWORD))

    try:
        # Test connection
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            result.single()

        print("✅ Connected to remote database\n")

        # Export statistics
        export_statistics(driver)

        # Export to Cypher
        export_to_cypher(driver)

        print("\n" + "="*60)
        print("✅ Backup Complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Start local Neo4j database")
        print("2. Run: cypher-shell < backup/neo4j_backup.cypher")
        print("   Or use Neo4j Browser and paste the contents")
        print("3. Recreate vector indexes manually (see backup file)")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.close()

if __name__ == "__main__":
    main()
