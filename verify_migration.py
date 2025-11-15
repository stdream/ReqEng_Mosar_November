"""
Database Migration Verification Script
Compares remote backup statistics with local Neo4j database
"""

import json
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

# Local DB
local_driver = GraphDatabase.driver(
    os.getenv('NEO4J_URI'),
    auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
)

# Load backup statistics
with open('backup/statistics.json', 'r', encoding='utf-8') as f:
    remote_stats = json.load(f)

print('='*60)
print('DATABASE COMPARISON: Remote vs Local')
print('='*60)

with local_driver.session() as session:
    # 1. Node counts by label
    print('\n[1] NODE COUNTS BY LABEL')
    print('-'*60)
    result = session.run('''
        MATCH (n)
        RETURN labels(n)[0] as label, count(*) as count
        ORDER BY label
    ''')

    local_nodes = {}
    for record in result:
        label = record['label']
        count = record['count']
        local_nodes[label] = count

    remote_node_counts = remote_stats.get('nodes', {})

    all_labels = sorted(set(list(local_nodes.keys()) + list(remote_node_counts.keys())))

    print(f'{"Label":<20} {"Remote":>10} {"Local":>10} {"Match":>10}')
    print('-'*60)
    total_match = True
    for label in all_labels:
        remote_count = remote_node_counts.get(label, 0)
        local_count = local_nodes.get(label, 0)
        match = 'OK' if remote_count == local_count else 'MISMATCH'
        if match == 'MISMATCH':
            total_match = False
        print(f'{label:<20} {remote_count:>10} {local_count:>10} {match:>10}')

    # 2. Relationship counts by type
    print('\n[2] RELATIONSHIP COUNTS BY TYPE')
    print('-'*60)
    result = session.run('''
        MATCH ()-[r]->()
        RETURN type(r) as rel_type, count(*) as count
        ORDER BY rel_type
    ''')

    local_rels = {}
    for record in result:
        rel_type = record['rel_type']
        count = record['count']
        local_rels[rel_type] = count

    remote_rel_counts = remote_stats.get('relationships', {})

    all_rel_types = sorted(set(list(local_rels.keys()) + list(remote_rel_counts.keys())))

    print(f'{"Relationship Type":<30} {"Remote":>10} {"Local":>10} {"Match":>10}')
    print('-'*60)
    for rel_type in all_rel_types:
        remote_count = remote_rel_counts.get(rel_type, 0)
        local_count = local_rels.get(rel_type, 0)

        # Exclude new relationships created locally
        if rel_type in ['SIMILAR_TO', 'RELATED_TO']:
            match = 'NEW'
            print(f'{rel_type:<30} {remote_count:>10} {local_count:>10} {match:>10}')
        else:
            match = 'OK' if remote_count == local_count else 'MISMATCH'
            if match == 'MISMATCH':
                total_match = False
            print(f'{rel_type:<30} {remote_count:>10} {local_count:>10} {match:>10}')

    # 3. Total counts
    print('\n[3] TOTAL COUNTS')
    print('-'*60)
    total_nodes_result = session.run('MATCH (n) RETURN count(n) as total')
    local_total_nodes = total_nodes_result.single()['total']

    total_rels_result = session.run('MATCH ()-[r]->() RETURN count(r) as total')
    local_total_rels = total_rels_result.single()['total']

    # Subtract new relationships
    new_rels = local_rels.get('SIMILAR_TO', 0) + local_rels.get('RELATED_TO', 0)
    local_original_rels = local_total_rels - new_rels

    remote_total_nodes = remote_stats.get('totals', {}).get('nodes', 0)
    remote_total_rels = remote_stats.get('totals', {}).get('relationships', 0)

    print(f'Total Nodes:')
    print(f'  Remote: {remote_total_nodes}')
    print(f'  Local:  {local_total_nodes}')
    print(f'  Match:  {"OK" if remote_total_nodes == local_total_nodes else "MISMATCH"}')

    print(f'\nTotal Relationships (original):')
    print(f'  Remote: {remote_total_rels}')
    print(f'  Local (original):  {local_original_rels}')
    print(f'  Local (with new):  {local_total_rels} (+{new_rels})')
    print(f'  Match:  {"OK" if remote_total_rels == local_original_rels else "MISMATCH"}')

    # 4. Sample data verification
    print('\n[4] SAMPLE DATA VERIFICATION')
    print('-'*60)

    # Check specific requirements
    test_req_ids = ['S101', 'S110', 'A110', 'FuncR_S101']
    print('\nRequirement Samples:')
    for req_id in test_req_ids:
        result = session.run('''
            MATCH (r:Requirement)
            WHERE r.id = $id OR r.display_id = $id
            RETURN r.id as id, r.display_id as display_id,
                   substring(r.statement, 0, 50) as statement_preview
        ''', id=req_id)

        record = result.single()
        if record:
            print(f'  OK {req_id}: {record["display_id"]} - {record["statement_preview"]}...')
        else:
            print(f'  MISSING: {req_id}')

    # Check documents
    print('\nDocument Samples:')
    doc_ids = ['SRD', 'PDD', 'DDD', 'DEMO']
    for doc_id in doc_ids:
        result = session.run('''
            MATCH (d:Document {id: $id})
            RETURN d.id as id, d.title as title
        ''', id=doc_id)

        record = result.single()
        if record:
            print(f'  OK {doc_id}: {record["title"]}')
        else:
            print(f'  MISSING: {doc_id}')

    # 5. Embedding verification
    print('\n[5] EMBEDDING STATUS')
    print('-'*60)

    chunk_emb_result = session.run('''
        MATCH (c:Chunk)
        RETURN
            count(c) as total,
            count(c.embedding) as with_embedding,
            count(c) - count(c.embedding) as without_embedding
    ''')
    chunk_emb = chunk_emb_result.single()

    req_emb_result = session.run('''
        MATCH (r:Requirement)
        RETURN
            count(r) as total,
            count(r.embedding) as with_embedding,
            count(r) - count(r.embedding) as without_embedding
    ''')
    req_emb = req_emb_result.single()

    print(f'Chunks:')
    print(f'  Total: {chunk_emb["total"]}')
    print(f'  With embeddings: {chunk_emb["with_embedding"]}')
    print(f'  Without embeddings: {chunk_emb["without_embedding"]}')
    if chunk_emb["total"] > 0:
        print(f'  Coverage: {chunk_emb["with_embedding"]/chunk_emb["total"]*100:.1f}%')

    print(f'\nRequirements:')
    print(f'  Total: {req_emb["total"]}')
    print(f'  With embeddings: {req_emb["with_embedding"]}')
    print(f'  Without embeddings: {req_emb["without_embedding"]}')
    if req_emb["total"] > 0:
        print(f'  Coverage: {req_emb["with_embedding"]/req_emb["total"]*100:.1f}%')

    # 6. Similarity relationships (new in local)
    print('\n[6] SIMILARITY RELATIONSHIPS (NEW)')
    print('-'*60)

    similar_to = session.run('MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) as count').single()['count']
    related_to = session.run('MATCH ()-[r:RELATED_TO]->() RETURN count(r) as count').single()['count']

    print(f'SIMILAR_TO (chunks): {similar_to}')
    print(f'RELATED_TO (requirements): {related_to}')
    print(f'Total new relationships: {similar_to + related_to}')

    # 7. Check for missing properties
    print('\n[7] PROPERTY COMPLETENESS CHECK')
    print('-'*60)

    # Requirements with missing key properties
    missing_props = session.run('''
        MATCH (r:Requirement)
        WHERE r.statement IS NULL OR r.type IS NULL
        RETURN count(r) as count
    ''').single()['count']
    print(f'Requirements with missing properties: {missing_props}')

    # Chunks with missing text
    missing_text = session.run('''
        MATCH (c:Chunk)
        WHERE c.text IS NULL OR c.text = ""
        RETURN count(c) as count
    ''').single()['count']
    print(f'Chunks with missing text: {missing_text}')

    # 8. Relationship connectivity check
    print('\n[8] RELATIONSHIP CONNECTIVITY')
    print('-'*60)

    # Orphaned nodes (nodes with no relationships)
    orphans = session.run('''
        MATCH (n)
        WHERE NOT (n)-[]-()
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
    ''')

    print('Orphaned nodes (no relationships):')
    total_orphans = 0
    has_orphans = False
    for record in orphans:
        has_orphans = True
        count = record['count']
        total_orphans += count
        print(f'  {record["label"]}: {count}')

    if not has_orphans:
        print('  None - All nodes are connected OK')

    # 9. Check traceability paths
    print('\n[9] TRACEABILITY PATH VERIFICATION')
    print('-'*60)

    # Sample vertical traceability: Requirement -> Component -> Test
    trace_result = session.run('''
        MATCH path = (r:Requirement)-[:ALLOCATED_TO]->(c:Component)-[:TESTED_IN]->(t:TestCase)
        RETURN count(path) as count
        LIMIT 1
    ''')
    trace_count = trace_result.single()['count']
    print(f'Requirement->Component->Test paths: {"OK" if trace_count > 0 else "No paths found"}')

    # Document -> Section -> Chunk paths
    doc_paths = session.run('''
        MATCH path = (d:Document)-[:HAS_SECTION]->(s:Section)-[:HAS_CHUNK]->(c:Chunk)
        RETURN count(path) as count
        LIMIT 1
    ''')
    doc_path_count = doc_paths.single()['count']
    print(f'Document->Section->Chunk paths: {"OK" if doc_path_count > 0 else "No paths found"}')

    # Chunk -> Requirement mentions
    mention_paths = session.run('''
        MATCH (c:Chunk)-[:MENTIONS_REQUIREMENT]->(r:Requirement)
        RETURN count(*) as count
    ''')
    mention_count = mention_paths.single()['count']
    print(f'Chunk->Requirement mentions: {mention_count} connections')

local_driver.close()

print('\n' + '='*60)
print('VERIFICATION COMPLETE')
print('='*60)

if total_match:
    print('STATUS: OK - All original data migrated successfully')
else:
    print('STATUS: WARNING - Some mismatches detected (review above)')
