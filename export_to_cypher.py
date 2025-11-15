#!/usr/bin/env python3
"""
Export Neo4j to Cypher Script
브라우저에서 직접 실행 가능한 Cypher 스크립트 생성
"""

import os
import json
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

REMOTE_URI = os.getenv("NEO4J_URI")
REMOTE_USER = os.getenv("NEO4J_USERNAME", "neo4j")
REMOTE_PASSWORD = os.getenv("NEO4J_PASSWORD")

def export_to_cypher():
    """Cypher 스크립트로 export"""

    driver = GraphDatabase.driver(REMOTE_URI, auth=(REMOTE_USER, REMOTE_PASSWORD))

    with open("backup/restore.cypher", 'w', encoding='utf-8') as f:
        f.write("// Neo4j Database Restore Script\n")
        f.write("// Copy and paste into Neo4j Browser\n\n")

        with driver.session() as session:
            # 1. Requirements
            print("Exporting Requirements...")
            f.write("// ========================================\n")
            f.write("// REQUIREMENTS\n")
            f.write("// ========================================\n\n")

            reqs = session.run("MATCH (r:Requirement) RETURN r")
            for record in reqs:
                req = record['r']
                props_dict = dict(req)
                props_str = json.dumps(props_dict, ensure_ascii=False)

                f.write(f"MERGE (:Requirement {{id: {json.dumps(props_dict.get('id'))}}})\n")
                f.write(f"  SET _ = {props_str};\n\n")

            # 2. Documents
            print("Exporting Documents...")
            f.write("// ========================================\n")
            f.write("// DOCUMENTS\n")
            f.write("// ========================================\n\n")

            docs = session.run("MATCH (d:Document) RETURN d")
            for record in docs:
                doc = record['d']
                props_dict = dict(doc)
                props_str = json.dumps(props_dict, ensure_ascii=False)

                f.write(f"MERGE (:Document {{id: {json.dumps(props_dict.get('id'))}}})\n")
                f.write(f"  SET _ = {props_str};\n\n")

            # 3. Entities (간단 버전)
            print("Exporting Entities...")
            f.write("// ========================================\n")
            f.write("// ENTITIES\n")
            f.write("// ========================================\n\n")

            entities = session.run("MATCH (e:Entity) RETURN e LIMIT 100")  # 샘플만
            for record in entities:
                ent = record['e']
                props_dict = dict(ent)
                props_str = json.dumps(props_dict, ensure_ascii=False)

                f.write(f"MERGE (:Entity {{canonical_name: {json.dumps(props_dict.get('canonical_name'))}}})\n")
                f.write(f"  SET _ = {props_str};\n\n")

            f.write("\n// ... (나머지 노드는 JSON import 사용)\n\n")

            # 4. COVERS relationships
            print("Exporting COVERS relationships...")
            f.write("// ========================================\n")
            f.write("// COVERS RELATIONSHIPS\n")
            f.write("// ========================================\n\n")

            covers = session.run("""
                MATCH (a:Requirement)-[r:COVERS]->(b:Requirement)
                RETURN a.id as from_id, b.id as to_id
            """)

            for record in covers:
                f.write(f"MATCH (a:Requirement {{id: {json.dumps(record['from_id'])}}}), ")
                f.write(f"(b:Requirement {{id: {json.dumps(record['to_id'])}}})\n")
                f.write(f"MERGE (a)-[:COVERS]->(b);\n\n")

    driver.close()

    print(f"\n✓ Cypher script saved to: backup/restore.cypher")
    print("\nTo restore:")
    print("1. Open Neo4j Browser")
    print("2. Copy and paste contents of backup/restore.cypher")
    print("3. Execute (may need to run in batches)")

if __name__ == "__main__":
    export_to_cypher()
