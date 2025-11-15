"""
Ingest MOSAR Documents (Markdown) into Neo4j
Creates Document -> Section -> Chunk hierarchy with embeddings
"""
import os
import sys
from typing import List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.neo4j_connection import Neo4jConnection
from utils.document_parser import (
    MarkdownDocumentParser,
    Section,
    Chunk,
    clean_markdown
)

# Load environment variables
load_dotenv()


class DocumentIngester:
    """Ingests markdown documents into Neo4j with embeddings"""

    def __init__(
        self,
        connection: Neo4jConnection,
        embedding_model: str = "text-embedding-ada-002"
    ):
        """
        Initialize ingester

        Args:
            connection: Neo4jConnection instance
            embedding_model: OpenAI embedding model name
        """
        self.conn = connection
        self.parser = MarkdownDocumentParser(chunk_size=1000, chunk_overlap=200)
        self.embedding_model = embedding_model

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.openai_client = OpenAI(api_key=api_key)

    def get_embedding(self, text: str) -> List[float]:
        """
        Get embedding for text using OpenAI

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"[WARNING] Warning: Could not generate embedding: {e}")
            return []

    def create_document_node(
        self,
        doc_id: str,
        title: str,
        doc_type: str,
        version: str = "",
        date: str = ""
    ) -> bool:
        """
        Create Document node in Neo4j

        Args:
            doc_id: Document identifier
            title: Document title
            doc_type: Document type (SRD, PDD, DDD, DEMO)
            version: Document version
            date: Document date

        Returns:
            True if successful
        """
        query = """
        MERGE (d:Document {id: $id})
        SET d.title = $title,
            d.doc_type = $doc_type,
            d.version = $version,
            d.date = $date
        RETURN d.id as id
        """
        try:
            self.conn.execute_write(query, {
                'id': doc_id,
                'title': title,
                'doc_type': doc_type,
                'version': version,
                'date': date
            })
            return True
        except Exception as e:
            print(f"[ERROR] Error creating document node: {e}")
            return False

    def create_section_node(self, section: Section, doc_id: str) -> bool:
        """
        Create Section node and link to Document

        Args:
            section: Section object
            doc_id: Document identifier

        Returns:
            True if successful
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        MERGE (s:Section {id: $section_id})
        SET s.number = $number,
            s.title = $title,
            s.level = $level
        MERGE (d)-[:HAS_SECTION]->(s)
        """
        try:
            self.conn.execute_write(query, {
                'doc_id': doc_id,
                'section_id': section.id,
                'number': section.number,
                'title': section.title,
                'level': section.level
            })

            # Create parent relationship if exists
            if section.parent_number:
                self._create_subsection_relationship(section, doc_id)

            return True
        except Exception as e:
            print(f"[ERROR] Error creating section node {section.id}: {e}")
            return False

    def _create_subsection_relationship(self, section: Section, doc_id: str):
        """Create HAS_SUBSECTION relationship to parent section"""
        query = """
        MATCH (parent:Section)
        WHERE parent.number = $parent_number
        MATCH (child:Section {id: $child_id})
        MERGE (parent)-[:HAS_SUBSECTION]->(child)
        """
        try:
            self.conn.execute_write(query, {
                'parent_number': section.parent_number,
                'child_id': section.id
            })
        except Exception as e:
            print(f"[WARNING] Warning: Could not create subsection relationship: {e}")

    def create_chunk_node(
        self,
        chunk: Chunk,
        section: Section,
        batch_embeddings: Dict[str, List[float]]
    ) -> bool:
        """
        Create Chunk node with embedding

        Args:
            chunk: Chunk object
            section: Section object (parent)
            batch_embeddings: Pre-computed embeddings dict

        Returns:
            True if successful
        """
        embedding = batch_embeddings.get(chunk.id, [])

        query = """
        MATCH (s:Section {id: $section_id})
        MERGE (c:Chunk {id: $chunk_id})
        SET c.text = $text,
            c.embedding = $embedding,
            c.order_in_section = $order
        MERGE (s)-[:HAS_CHUNK]->(c)
        """
        try:
            self.conn.execute_write(query, {
                'section_id': section.id,
                'chunk_id': chunk.id,
                'text': chunk.text,
                'embedding': embedding,
                'order': chunk.order
            })
            return True
        except Exception as e:
            print(f"[ERROR] Error creating chunk node {chunk.id}: {e}")
            return False

    def create_chunk_sequence(self, chunks: List[Chunk]):
        """
        Create NEXT_CHUNK relationships between consecutive chunks

        Args:
            chunks: List of chunks in order
        """
        for i in range(len(chunks) - 1):
            query = """
            MATCH (c1:Chunk {id: $chunk1_id})
            MATCH (c2:Chunk {id: $chunk2_id})
            MERGE (c1)-[:NEXT_CHUNK]->(c2)
            """
            try:
                self.conn.execute_write(query, {
                    'chunk1_id': chunks[i].id,
                    'chunk2_id': chunks[i + 1].id
                })
            except Exception as e:
                print(f"[WARNING] Warning: Could not create NEXT_CHUNK relationship: {e}")

    def generate_batch_embeddings(
        self,
        chunks: List[Chunk],
        batch_size: int = 100
    ) -> Dict[str, List[float]]:
        """
        Generate embeddings for chunks in batches

        Args:
            chunks: List of chunks
            batch_size: Number of chunks to process at once

        Returns:
            Dictionary mapping chunk_id to embedding vector
        """
        print(f"  Generating embeddings for {len(chunks)} chunks...")
        embeddings = {}

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [chunk.text for chunk in batch]

            try:
                response = self.openai_client.embeddings.create(
                    model=self.embedding_model,
                    input=texts
                )

                for chunk, embedding_obj in zip(batch, response.data):
                    embeddings[chunk.id] = embedding_obj.embedding

                print(f"    Progress: {min(i + batch_size, len(chunks))}/{len(chunks)}")

            except Exception as e:
                print(f"[WARNING] Error generating embeddings for batch: {e}")
                # Fallback: generate individually
                for chunk in batch:
                    embeddings[chunk.id] = self.get_embedding(chunk.text)

        print(f"  [OK] Generated {len(embeddings)} embeddings")
        return embeddings

    def ingest_document(
        self,
        file_path: str,
        doc_id: str,
        doc_title: str,
        doc_type: str,
        version: str = "",
        date: str = ""
    ) -> Dict[str, int]:
        """
        Ingest a single document

        Args:
            file_path: Path to markdown file
            doc_id: Document identifier
            doc_title: Document title
            doc_type: Document type (SRD, PDD, DDD, DEMO)
            version: Document version
            date: Document date

        Returns:
            Statistics dictionary
        """
        print(f"\n[*] Ingesting document: {doc_title}")
        print(f"   File: {file_path}")

        stats = {
            'sections': 0,
            'chunks': 0,
            'embeddings': 0
        }

        # Read document
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Clean content
        content = clean_markdown(content)

        # Create document node
        if not self.create_document_node(doc_id, doc_title, doc_type, version, date):
            return stats

        # Parse document
        sections, chunks = self.parser.parse_document(content, doc_id, doc_title)

        # Generate embeddings in batch
        batch_embeddings = self.generate_batch_embeddings(chunks)
        stats['embeddings'] = len(batch_embeddings)

        # Create section nodes
        print(f"  Creating section nodes...")
        for section in sections:
            if self.create_section_node(section, doc_id):
                stats['sections'] += 1

        # Create chunk nodes
        print(f"  Creating chunk nodes...")
        section_map = {s.id: s for s in sections}
        for chunk in chunks:
            section = section_map.get(chunk.section_id)
            if section and self.create_chunk_node(chunk, section, batch_embeddings):
                stats['chunks'] += 1

        # Create chunk sequences
        print(f"  Creating chunk sequences...")
        self.create_chunk_sequence(chunks)

        print(f"  [OK] Document ingested successfully")
        return stats


def main():
    """Main ingestion process"""
    print("=" * 60)
    print("MOSAR Documents Ingestion")
    print("=" * 60)
    print()

    # Connect to Neo4j
    conn = Neo4jConnection()
    conn.connect()

    # Initialize ingester
    ingester = DocumentIngester(conn)

    # Define documents to ingest
    docs_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "Documents"
    )

    documents = [
        {
            'file': 'System Requirements Document_MOSAR.md',
            'id': 'SRD',
            'title': 'System Requirements Document',
            'type': 'SRD',
            'version': '1.0.0',
            'date': '2019-09-01'
        },
        {
            'file': 'MOSAR-WP2-D2.4-SA_1.1.0-Preliminary-Design-Document.md',
            'id': 'PDD',
            'title': 'Preliminary Design Document',
            'type': 'PDD',
            'version': '1.1.0',
            'date': ''
        },
        {
            'file': 'MOSAR-WP3-D3.6-SA_1.2.0-Detailed-Design-Document.md',
            'id': 'DDD',
            'title': 'Detailed Design Document',
            'type': 'DDD',
            'version': '1.2.0',
            'date': ''
        },
        {
            'file': 'MOSAR-WP3-D3.5-DLR_1.1.0-Demonstration-Procedures.md',
            'id': 'DEMO',
            'title': 'Demonstration Procedures',
            'type': 'DEMO',
            'version': '1.1.0',
            'date': ''
        }
    ]

    total_stats = {'sections': 0, 'chunks': 0, 'embeddings': 0}

    # Ingest each document
    for doc_info in documents:
        file_path = os.path.join(docs_dir, doc_info['file'])

        if not os.path.exists(file_path):
            print(f"[WARNING] Warning: File not found: {file_path}")
            continue

        stats = ingester.ingest_document(
            file_path=file_path,
            doc_id=doc_info['id'],
            doc_title=doc_info['title'],
            doc_type=doc_info['type'],
            version=doc_info['version'],
            date=doc_info['date']
        )

        total_stats['sections'] += stats['sections']
        total_stats['chunks'] += stats['chunks']
        total_stats['embeddings'] += stats['embeddings']

    # Print summary
    print("\n" + "=" * 60)
    print("[*] Ingestion Summary")
    print("=" * 60)
    print(f"  Documents processed: {len(documents)}")
    print(f"  Total sections: {total_stats['sections']}")
    print(f"  Total chunks: {total_stats['chunks']}")
    print(f"  Total embeddings: {total_stats['embeddings']}")

    # Verify database
    print("\n[*] Database Statistics:")
    db_stats = conn.get_database_stats()
    print(f"  Total Nodes: {db_stats['total_nodes']}")
    print(f"  Total Relationships: {db_stats['total_relationships']}")
    if db_stats.get('nodes_by_label'):
        print("\n  Nodes by Label:")
        for label, count in db_stats['nodes_by_label'].items():
            print(f"    {label}: {count}")

    conn.close()
    print("\n[*] Documents ingestion complete!")


if __name__ == "__main__":
    main()
