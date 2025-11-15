#!/usr/bin/env python3
"""
Create Similarity-Based Connections
임베딩 유사도 기반 Chunk-Chunk, Requirement-Requirement 연결 생성
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
from tqdm import tqdm

load_dotenv()

NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')

# Similarity thresholds
CHUNK_SIMILARITY_THRESHOLD = 0.85  # High similarity for chunks
REQ_SIMILARITY_THRESHOLD = 0.80    # Related requirements

def create_similar_chunk_relationships(session):
    """Create SIMILAR_TO relationships between chunks"""

    print("\n" + "="*60)
    print("Step 1: Create Similar Chunk Relationships")
    print("="*60)
    print(f"  Threshold: {CHUNK_SIMILARITY_THRESHOLD}")
    print()

    # Get total chunks with embeddings
    total = session.run("""
        MATCH (c:Chunk)
        WHERE c.embedding IS NOT NULL
        RETURN count(c) as count
    """).single()['count']

    print(f"  Processing {total} chunks...")

    # Delete existing SIMILAR_TO relationships
    session.run("MATCH ()-[r:SIMILAR_TO]->() DELETE r")

    # Create similarity relationships
    # Note: This is computationally expensive, so we batch it
    query = """
    MATCH (c1:Chunk)
    WHERE c1.embedding IS NOT NULL
    WITH c1 LIMIT 100

    MATCH (c2:Chunk)
    WHERE c2.embedding IS NOT NULL AND id(c1) < id(c2)
    WITH c1, c2, gds.similarity.cosine(c1.embedding, c2.embedding) as similarity
    WHERE similarity >= $threshold

    MERGE (c1)-[r:SIMILAR_TO]->(c2)
    SET r.similarity = similarity

    RETURN count(r) as relationships_created
    """

    result = session.run(query, {'threshold': CHUNK_SIMILARITY_THRESHOLD})
    count = result.single()['relationships_created']

    print(f"  OK Created {count} SIMILAR_TO relationships")

    return count

def create_related_requirement_relationships(session):
    """Create RELATED_TO relationships between requirements"""

    print("\n" + "="*60)
    print("Step 2: Create Related Requirement Relationships")
    print("="*60)
    print(f"  Threshold: {REQ_SIMILARITY_THRESHOLD}")
    print()

    # Delete existing RELATED_TO relationships
    session.run("MATCH ()-[r:RELATED_TO]->() DELETE r")

    # Create similarity relationships for requirements
    query = """
    MATCH (r1:Requirement)
    WHERE r1.embedding IS NOT NULL

    MATCH (r2:Requirement)
    WHERE r2.embedding IS NOT NULL AND id(r1) < id(r2)
    WITH r1, r2, gds.similarity.cosine(r1.embedding, r2.embedding) as similarity
    WHERE similarity >= $threshold

    MERGE (r1)-[rel:RELATED_TO]->(r2)
    SET rel.similarity = similarity

    RETURN count(rel) as relationships_created
    """

    result = session.run(query, {'threshold': REQ_SIMILARITY_THRESHOLD})
    count = result.single()['relationships_created']

    print(f"  OK Created {count} RELATED_TO relationships")

    return count

def analyze_similarity_network(session):
    """Analyze the similarity network"""

    print("\n" + "="*60)
    print("Step 3: Network Analysis")
    print("="*60)

    # Chunk similarity stats
    chunk_stats = session.run("""
        MATCH (c1:Chunk)-[r:SIMILAR_TO]->(c2:Chunk)
        RETURN
            count(r) as total_relationships,
            avg(r.similarity) as avg_similarity,
            max(r.similarity) as max_similarity,
            min(r.similarity) as min_similarity
    """).single()

    print(f"\n  Chunk Similarities:")
    if chunk_stats and chunk_stats['total_relationships']:
        print(f"    Total: {chunk_stats['total_relationships']}")
        print(f"    Avg similarity: {chunk_stats['avg_similarity']:.3f}")
        print(f"    Max similarity: {chunk_stats['max_similarity']:.3f}")
        print(f"    Min similarity: {chunk_stats['min_similarity']:.3f}")
    else:
        print(f"    None found (threshold may be too high)")

    # Requirement similarity stats
    req_stats = session.run("""
        MATCH (r1:Requirement)-[rel:RELATED_TO]->(r2:Requirement)
        RETURN
            count(rel) as total_relationships,
            avg(rel.similarity) as avg_similarity,
            max(rel.similarity) as max_similarity,
            min(rel.similarity) as min_similarity
    """).single()

    print(f"\n  Requirement Relationships:")
    if req_stats and req_stats['total_relationships']:
        print(f"    Total: {req_stats['total_relationships']}")
        print(f"    Avg similarity: {req_stats['avg_similarity']:.3f}")
        print(f"    Max similarity: {req_stats['max_similarity']:.3f}")
        print(f"    Min similarity: {req_stats['min_similarity']:.3f}")
    else:
        print(f"    None found (threshold may be too high)")

    # Sample similar chunks
    print(f"\n  Sample Similar Chunks:")
    samples = session.run("""
        MATCH (c1:Chunk)-[r:SIMILAR_TO]->(c2:Chunk)
        RETURN c1.id as chunk1, c2.id as chunk2, r.similarity as similarity
        ORDER BY r.similarity DESC
        LIMIT 5
    """).data()

    for sample in samples:
        print(f"    {sample['chunk1']} <-> {sample['chunk2']}: {sample['similarity']:.3f}")

    # Sample related requirements
    print(f"\n  Sample Related Requirements:")
    samples = session.run("""
        MATCH (r1:Requirement)-[rel:RELATED_TO]->(r2:Requirement)
        RETURN r1.id as req1, r2.id as req2, rel.similarity as similarity
        ORDER BY rel.similarity DESC
        LIMIT 5
    """).data()

    for sample in samples:
        print(f"    {sample['req1']} <-> {sample['req2']}: {sample['similarity']:.3f}")

def main():
    print("="*60)
    print("MOSAR GraphRAG Similarity Connections")
    print("="*60)
    print(f"Target: {NEO4J_URI}")
    print()

    # Connect
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            # Test connection
            session.run("RETURN 1").single()
            print("  OK Connected\n")

            # Check embeddings exist
            chunk_count = session.run("""
                MATCH (c:Chunk)
                WHERE c.embedding IS NOT NULL
                RETURN count(c) as count
            """).single()['count']

            req_count = session.run("""
                MATCH (r:Requirement)
                WHERE r.embedding IS NOT NULL
                RETURN count(r) as count
            """).single()['count']

            print(f"Embeddings found:")
            print(f"  Chunks: {chunk_count}")
            print(f"  Requirements: {req_count}")

            if chunk_count == 0 and req_count == 0:
                print("\nError: No embeddings found!")
                print("Please run generate_embeddings.py first")
                sys.exit(1)

            # Create similarity relationships
            chunk_rels = create_similar_chunk_relationships(session)
            req_rels = create_related_requirement_relationships(session)

            # Analyze
            analyze_similarity_network(session)

            print("\n" + "="*60)
            print("OK Similarity Connections Complete!")
            print("="*60)
            print(f"\nSummary:")
            print(f"  - Chunk similarities: {chunk_rels}")
            print(f"  - Requirement relationships: {req_rels}")
            print(f"\nNext steps:")
            print(f"  1. Query similar chunks in Neo4j Browser")
            print(f"  2. Explore requirement relationships")
            print(f"  3. Use for GraphRAG retrieval")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        driver.close()

if __name__ == "__main__":
    main()
