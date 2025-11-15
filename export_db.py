#!/usr/bin/env python3
"""
Simple Neo4j Database Export
원격 DB를 JSON 덤프로 백업
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
import json
from pathlib import Path

# Load .env
load_dotenv()

REMOTE_URI = os.getenv("NEO4J_URI")
REMOTE_USER = os.getenv("NEO4J_USERNAME", "neo4j")
REMOTE_PASSWORD = os.getenv("NEO4J_PASSWORD")

def export_database():
    """Export all nodes and relationships to JSON"""

    if not REMOTE_PASSWORD:
        print("Error: NEO4J_PASSWORD not set in .env")
        return

    print(f"Connecting to {REMOTE_URI}...")

    driver = GraphDatabase.driver(REMOTE_URI, auth=(REMOTE_USER, REMOTE_PASSWORD))

    try:
        # Create backup directory
        Path("backup").mkdir(exist_ok=True)

        with driver.session() as session:
            # Test connection
            session.run("RETURN 1").single()
            print("Connected successfully!\n")

            # Export nodes
            print("Exporting nodes...")
            nodes_query = """
            MATCH (n)
            RETURN
                id(n) as node_id,
                labels(n) as labels,
                properties(n) as properties
            """

            nodes = []
            result = session.run(nodes_query)
            for record in result:
                props = dict(record['properties'])

                # Convert special types to JSON-serializable
                for key, value in props.items():
                    if hasattr(value, 'iso_format'):  # DateTime
                        props[key] = value.iso_format()
                    elif isinstance(value, list) and len(value) > 100:  # Large vectors
                        props[key] = f"<vector:{len(value)} dims>"

                node_data = {
                    'node_id': record['node_id'],
                    'labels': record['labels'],
                    'properties': props
                }

                nodes.append(node_data)

            print(f"  Exported {len(nodes)} nodes")

            # Export relationships
            print("Exporting relationships...")
            rels_query = """
            MATCH (a)-[r]->(b)
            RETURN
                id(a) as start_id,
                id(b) as end_id,
                type(r) as rel_type,
                properties(r) as properties
            """

            relationships = []
            result = session.run(rels_query)
            for record in result:
                props = dict(record['properties'])

                # Convert special types
                for key, value in props.items():
                    if hasattr(value, 'iso_format'):
                        props[key] = value.iso_format()

                rel_data = {
                    'start_id': record['start_id'],
                    'end_id': record['end_id'],
                    'type': record['rel_type'],
                    'properties': props
                }
                relationships.append(rel_data)

            print(f"  Exported {len(relationships)} relationships")

            # Save to JSON
            backup_data = {
                'nodes': nodes,
                'relationships': relationships,
                'stats': {
                    'total_nodes': len(nodes),
                    'total_relationships': len(relationships)
                }
            }

            output_file = "backup/neo4j_dump.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            print(f"\nBackup saved to: {output_file}")
            print(f"  Nodes: {len(nodes)}")
            print(f"  Relationships: {len(relationships)}")

            # Also create statistics
            stats_file = "backup/statistics.json"
            stats = get_statistics(session)
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, indent=2, ensure_ascii=False)

            print(f"\nStatistics saved to: {stats_file}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.close()

def get_statistics(session):
    """Get database statistics"""

    stats = {'nodes': {}, 'relationships': {}}

    # Node counts by label
    labels = session.run("CALL db.labels()").data()
    for record in labels:
        label = record['label']
        count = session.run(f"MATCH (n:{label}) RETURN count(n) as count").single()['count']
        stats['nodes'][label] = count

    # Relationship counts by type
    rel_types = session.run("CALL db.relationshipTypes()").data()
    for record in rel_types:
        rel_type = record['relationshipType']
        count = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count").single()['count']
        stats['relationships'][rel_type] = count

    # Totals
    total_nodes = session.run("MATCH (n) RETURN count(n) as count").single()['count']
    total_rels = session.run("MATCH ()-[r]->() RETURN count(r) as count").single()['count']

    stats['totals'] = {
        'nodes': total_nodes,
        'relationships': total_rels
    }

    return stats

if __name__ == "__main__":
    export_database()
