#!/usr/bin/env python3
"""
Generate Embeddings for MOSAR GraphRAG
Chunk 및 Requirement 임베딩 생성
"""

import os
import sys
from dotenv import load_dotenv
from neo4j import GraphDatabase
from openai import OpenAI
from tqdm import tqdm
import time

load_dotenv()

# Config
NEO4J_URI = os.getenv('NEO4J_URI')
NEO4J_USER = os.getenv('NEO4J_USERNAME')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# OpenAI embedding model
EMBEDDING_MODEL = "text-embedding-3-small"  # 1536 dimensions, cheaper
# EMBEDDING_MODEL = "text-embedding-3-large"  # 3072 dimensions, more accurate

BATCH_SIZE = 100  # OpenAI batch size
DIMENSION = 1536  # for text-embedding-3-small
# DIMENSION = 3072  # for text-embedding-3-large

def get_embedding(text, client):
    """Get embedding from OpenAI"""
    try:
        response = client.embeddings.create(
            input=text,
            model=EMBEDDING_MODEL
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"\n  Error getting embedding: {e}")
        return None

def get_embeddings_batch(texts, client):
    """Get embeddings for multiple texts at once"""
    try:
        response = client.embeddings.create(
            input=texts,
            model=EMBEDDING_MODEL
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        print(f"\n  Error getting batch embeddings: {e}")
        return None

def generate_chunk_embeddings(session, openai_client):
    """Generate embeddings for all chunks"""

    print("\n" + "="*60)
    print("Step 1: Generate Chunk Embeddings")
    print("="*60)

    # Get all chunks without embeddings
    query = """
    MATCH (c:Chunk)
    WHERE c.embedding IS NULL
    RETURN c.id as id, c.text as text
    ORDER BY c.id
    """

    result = session.run(query)
    chunks = [(record['id'], record['text']) for record in result]

    if not chunks:
        print("  All chunks already have embeddings!")
        return

    print(f"  Found {len(chunks)} chunks without embeddings")
    print(f"  Model: {EMBEDDING_MODEL}")
    print(f"  Dimensions: {DIMENSION}")
    print(f"  Estimated cost: ${len(chunks) * 0.00002:.4f}")
    print()

    # Process in batches
    total_processed = 0

    with tqdm(total=len(chunks), desc="Generating embeddings") as pbar:
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i:i+BATCH_SIZE]
            batch_ids = [chunk[0] for chunk in batch]
            batch_texts = [chunk[1][:8000] for chunk in batch]  # Truncate long texts

            # Get embeddings
            embeddings = get_embeddings_batch(batch_texts, openai_client)

            if embeddings:
                # Update database
                for chunk_id, embedding in zip(batch_ids, embeddings):
                    update_query = """
                    MATCH (c:Chunk {id: $id})
                    SET c.embedding = $embedding
                    """
                    session.run(update_query, {'id': chunk_id, 'embedding': embedding})
                    total_processed += 1
                    pbar.update(1)
            else:
                print(f"\n  Batch {i//BATCH_SIZE + 1} failed, skipping...")
                pbar.update(len(batch))

            # Rate limiting
            if i + BATCH_SIZE < len(chunks):
                time.sleep(0.1)

    print(f"\n  OK Generated embeddings for {total_processed} chunks")

def create_vector_index(session):
    """Create vector index for chunks"""

    print("\n" + "="*60)
    print("Step 2: Create Vector Index")
    print("="*60)

    # Drop existing index if any
    try:
        session.run("DROP INDEX chunk_embeddings IF EXISTS")
        print("  Dropped existing index")
    except:
        pass

    # Create new vector index
    query = f"""
    CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
    FOR (c:Chunk) ON c.embedding
    OPTIONS {{
        indexConfig: {{
            `vector.dimensions`: {DIMENSION},
            `vector.similarity_function`: 'cosine'
        }}
    }}
    """

    try:
        session.run(query)
        print(f"  OK Created vector index:")
        print(f"    - Dimensions: {DIMENSION}")
        print(f"    - Similarity: cosine")
    except Exception as e:
        print(f"  Error creating index: {e}")

def generate_requirement_embeddings(session, openai_client):
    """Generate embeddings for requirements"""

    print("\n" + "="*60)
    print("Step 3: Generate Requirement Embeddings")
    print("="*60)

    # Get all requirements
    query = """
    MATCH (r:Requirement)
    RETURN r.id as id, r.statement as statement
    ORDER BY r.id
    """

    result = session.run(query)
    requirements = [(record['id'], record['statement']) for record in result if record['statement']]

    print(f"  Found {len(requirements)} requirements")
    print(f"  Estimated cost: ${len(requirements) * 0.00002:.4f}")
    print()

    # Process in batches
    total_processed = 0

    with tqdm(total=len(requirements), desc="Generating req embeddings") as pbar:
        for i in range(0, len(requirements), BATCH_SIZE):
            batch = requirements[i:i+BATCH_SIZE]
            batch_ids = [req[0] for req in batch]
            batch_texts = [req[1][:8000] for req in batch]

            # Get embeddings
            embeddings = get_embeddings_batch(batch_texts, openai_client)

            if embeddings:
                # Update database
                for req_id, embedding in zip(batch_ids, embeddings):
                    update_query = """
                    MATCH (r:Requirement {id: $id})
                    SET r.embedding = $embedding
                    """
                    session.run(update_query, {'id': req_id, 'embedding': embedding})
                    total_processed += 1
                    pbar.update(1)
            else:
                print(f"\n  Batch {i//BATCH_SIZE + 1} failed, skipping...")
                pbar.update(len(batch))

            # Rate limiting
            if i + BATCH_SIZE < len(requirements):
                time.sleep(0.1)

    print(f"\n  OK Generated embeddings for {total_processed} requirements")

def verify_embeddings(session):
    """Verify embedding generation"""

    print("\n" + "="*60)
    print("Step 4: Verification")
    print("="*60)

    # Check chunks
    total_chunks = session.run("MATCH (c:Chunk) RETURN count(c) as count").single()['count']
    chunks_with_emb = session.run("""
        MATCH (c:Chunk)
        WHERE c.embedding IS NOT NULL
        RETURN count(c) as count
    """).single()['count']

    # Check requirements
    total_reqs = session.run("MATCH (r:Requirement) RETURN count(r) as count").single()['count']
    reqs_with_emb = session.run("""
        MATCH (r:Requirement)
        WHERE r.embedding IS NOT NULL
        RETURN count(r) as count
    """).single()['count']

    print(f"  Chunks: {chunks_with_emb}/{total_chunks} ({chunks_with_emb*100//total_chunks if total_chunks else 0}%)")
    print(f"  Requirements: {reqs_with_emb}/{total_reqs} ({reqs_with_emb*100//total_reqs if total_reqs else 0}%)")

    # Test vector search
    print("\n  Testing vector search...")
    test_query = """
    MATCH (c:Chunk)
    WHERE c.embedding IS NOT NULL
    RETURN c.id as id, c.text as text
    LIMIT 1
    """

    test_chunk = session.run(test_query).single()

    if test_chunk:
        print(f"    Sample chunk: {test_chunk['id']}")

        # Try similarity search
        try:
            search_query = """
            MATCH (c:Chunk)
            WHERE c.embedding IS NOT NULL AND c.id = $target_id
            WITH c
            MATCH (similar:Chunk)
            WHERE similar.embedding IS NOT NULL AND similar.id <> $target_id
            WITH c, similar,
                 gds.similarity.cosine(c.embedding, similar.embedding) as similarity
            WHERE similarity > 0.8
            RETURN similar.id as id, similarity
            ORDER BY similarity DESC
            LIMIT 5
            """

            result = session.run(search_query, {'target_id': test_chunk['id']})
            similar = list(result)

            if similar:
                print(f"    Found {len(similar)} similar chunks")
                for rec in similar[:3]:
                    print(f"      - {rec['id']}: similarity = {rec['similarity']:.3f}")
            else:
                print(f"    No highly similar chunks found (threshold: 0.8)")

        except Exception as e:
            print(f"    Similarity search not available yet: {e}")

    return chunks_with_emb, reqs_with_emb

def main():
    print("="*60)
    print("MOSAR GraphRAG Embedding Generation")
    print("="*60)
    print(f"Target: {NEO4J_URI}")
    print(f"Model: {EMBEDDING_MODEL}")
    print(f"Dimensions: {DIMENSION}")
    print()

    # Check API keys
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not set in .env")
        sys.exit(1)

    # Connect
    print("Connecting to Neo4j...")
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    openai_client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        with driver.session() as session:
            # Test connection
            session.run("RETURN 1").single()
            print("  OK Connected\n")

            # Generate embeddings
            generate_chunk_embeddings(session, openai_client)

            # Create vector index
            create_vector_index(session)

            # Generate requirement embeddings
            generate_requirement_embeddings(session, openai_client)

            # Verify
            chunks_done, reqs_done = verify_embeddings(session)

            print("\n" + "="*60)
            print("OK Embedding Generation Complete!")
            print("="*60)
            print(f"\nSummary:")
            print(f"  - Chunk embeddings: {chunks_done}")
            print(f"  - Requirement embeddings: {reqs_done}")
            print(f"  - Vector index: Created")
            print(f"\nNext steps:")
            print(f"  1. Test vector search in Neo4j Browser")
            print(f"  2. Run similarity-based connection generation")

    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        driver.close()

if __name__ == "__main__":
    main()
