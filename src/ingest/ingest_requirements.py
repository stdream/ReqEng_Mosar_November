"""
Ingest MOSAR Requirements from CSV into Neo4j
"""
import os
import sys
import pandas as pd
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.neo4j_connection import Neo4jConnection


class RequirementsIngester:
    """Ingests requirements from CSV into Neo4j"""

    def __init__(self, connection: Neo4jConnection):
        """
        Initialize ingester

        Args:
            connection: Neo4jConnection instance
        """
        self.conn = connection

    def load_csv(self, csv_path: str) -> pd.DataFrame:
        """
        Load requirements CSV file

        Args:
            csv_path: Path to CSV file

        Returns:
            DataFrame with requirements
        """
        print(f"Loading requirements from {csv_path}...")
        # Try different encodings
        for encoding in ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']:
            try:
                df = pd.read_csv(csv_path, encoding=encoding)
                print(f"[OK] Loaded {len(df)} requirements (encoding: {encoding})")
                return df
            except UnicodeDecodeError:
                continue

        # Last resort: ignore errors
        df = pd.read_csv(csv_path, encoding='utf-8', errors='ignore')
        print(f"[WARNING] Loaded {len(df)} requirements with encoding errors ignored")
        return df

    def parse_requirement(self, row: pd.Series) -> Dict[str, Any]:
        """
        Parse a requirement row into a node dictionary

        Args:
            row: DataFrame row

        Returns:
            Dictionary of requirement properties
        """
        # Extract covers field (comma-separated requirement IDs)
        covers = []
        if pd.notna(row.get('covers')):
            covers = [c.strip() for c in str(row['covers']).split(',') if c.strip()]

        return {
            'id': str(row['id']),
            'display_id': str(row['display_id']),
            'series': str(row['mosar_section']),  # S100, A100, etc.
            'type': str(row['mosar_section']),    # FuncR, PerfR, etc.
            'title': str(row.get('title', '')),
            'level': str(row.get('level', '')),
            'statement': str(row.get('statement', '')),
            'verification': str(row.get('verification', '')),
            'responsible': str(row.get('responsible', '')),
            'comment': str(row.get('comment', '')),
            'pageno': str(row.get('pageno', '')),
            'covers': covers  # List of requirement IDs
        }

    def create_requirement_node(self, req: Dict[str, Any]) -> bool:
        """
        Create or update a Requirement node in Neo4j

        Args:
            req: Requirement dictionary

        Returns:
            True if successful
        """
        query = """
        MERGE (r:Requirement {id: $id})
        SET r.display_id = $display_id,
            r.series = $series,
            r.type = $type,
            r.title = $title,
            r.level = $level,
            r.statement = $statement,
            r.verification = $verification,
            r.responsible = $responsible,
            r.comment = $comment,
            r.pageno = $pageno
        RETURN r.id as id
        """
        try:
            result = self.conn.execute_write(query, req)
            return True
        except Exception as e:
            print(f"[ERROR] Error creating requirement {req['id']}: {e}")
            return False

    def create_covers_relationships(self, req: Dict[str, Any]) -> int:
        """
        Create COVERS relationships for a requirement

        Args:
            req: Requirement dictionary with 'covers' list

        Returns:
            Number of relationships created
        """
        if not req.get('covers'):
            return 0

        count = 0
        for covered_id in req['covers']:
            query = """
            MATCH (r1:Requirement {id: $from_id})
            MATCH (r2:Requirement {id: $to_id})
            MERGE (r1)-[:COVERS]->(r2)
            """
            try:
                self.conn.execute_write(query, {
                    'from_id': req['id'],
                    'to_id': covered_id
                })
                count += 1
            except Exception as e:
                print(f"[WARNING] Warning: Could not create COVERS relationship "
                      f"{req['id']} -> {covered_id}: {e}")

        return count

    def ingest_requirements(self, csv_path: str) -> Dict[str, int]:
        """
        Ingest all requirements from CSV

        Args:
            csv_path: Path to CSV file

        Returns:
            Statistics dictionary
        """
        df = self.load_csv(csv_path)

        stats = {
            'total': len(df),
            'nodes_created': 0,
            'relationships_created': 0,
            'errors': 0
        }

        print(f"\n[*] Creating requirement nodes...")

        # First pass: Create all nodes
        for idx, row in df.iterrows():
            req = self.parse_requirement(row)
            if self.create_requirement_node(req):
                stats['nodes_created'] += 1
                if (idx + 1) % 50 == 0:
                    print(f"  Progress: {idx + 1}/{len(df)}")
            else:
                stats['errors'] += 1

        print(f"[OK] Created {stats['nodes_created']} requirement nodes")

        # Second pass: Create COVERS relationships
        print(f"\n[*] Creating COVERS relationships...")
        for idx, row in df.iterrows():
            req = self.parse_requirement(row)
            count = self.create_covers_relationships(req)
            stats['relationships_created'] += count

        print(f"[OK] Created {stats['relationships_created']} COVERS relationships")

        return stats


def main():
    """Main ingestion process"""
    print("=" * 60)
    print("MOSAR Requirements Ingestion")
    print("=" * 60)
    print()

    # Connect to Neo4j
    conn = Neo4jConnection()
    conn.connect()

    # Find CSV file
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "Documents",
        "mosar_requirements_all.csv"
    )

    if not os.path.exists(csv_path):
        print(f"[ERROR] CSV file not found: {csv_path}")
        return

    # Ingest requirements
    ingester = RequirementsIngester(conn)
    stats = ingester.ingest_requirements(csv_path)

    # Print summary
    print("\n" + "=" * 60)
    print("[*] Ingestion Summary")
    print("=" * 60)
    print(f"  Total requirements processed: {stats['total']}")
    print(f"  Nodes created: {stats['nodes_created']}")
    print(f"  Relationships created: {stats['relationships_created']}")
    print(f"  Errors: {stats['errors']}")

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
    print("\n[*] Requirements ingestion complete!")


if __name__ == "__main__":
    main()
