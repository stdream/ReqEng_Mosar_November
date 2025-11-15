"""
Neo4j Database Connection and Schema Initialization
"""
import os
from typing import Optional
from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Neo4jConnection:
    """Manages Neo4j database connection"""

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None
    ):
        """
        Initialize Neo4j connection

        Args:
            uri: Neo4j URI (defaults to NEO4J_URI env var)
            username: Neo4j username (defaults to NEO4J_USERNAME env var)
            password: Neo4j password (defaults to NEO4J_PASSWORD env var)
            database: Neo4j database name (defaults to NEO4J_DATABASE env var)
        """
        self.uri = uri or os.getenv("NEO4J_URI")
        self.username = username or os.getenv("NEO4J_USERNAME")
        self.password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database or os.getenv("NEO4J_DATABASE", "neo4j")

        if not all([self.uri, self.username, self.password]):
            raise ValueError(
                "Neo4j connection parameters missing. "
                "Provide via arguments or set NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD env vars"
            )

        self.driver: Optional[Driver] = None

    def connect(self) -> Driver:
        """Establish connection to Neo4j"""
        if self.driver is None:
            self.driver = GraphDatabase.driver(
                self.uri,
                auth=(self.username, self.password)
            )
            # Test connection
            self.driver.verify_connectivity()
            print(f"[OK] Connected to Neo4j at {self.uri}")
        return self.driver

    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
            self.driver = None
            print("[OK] Neo4j connection closed")

    def execute_query(self, query: str, parameters: Optional[dict] = None):
        """
        Execute a Cypher query

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query results
        """
        if not self.driver:
            self.connect()

        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record for record in result]

    def execute_write(self, query: str, parameters: Optional[dict] = None):
        """
        Execute a write transaction

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            Query results
        """
        if not self.driver:
            self.connect()

        def _tx_function(tx):
            result = tx.run(query, parameters or {})
            return [record for record in result]

        with self.driver.session(database=self.database) as session:
            return session.execute_write(_tx_function)

    def clear_database(self, confirm: bool = False):
        """
        Clear all nodes and relationships from database

        Args:
            confirm: Must be True to actually clear the database
        """
        if not confirm:
            raise ValueError("Must set confirm=True to clear database")

        print("[WARNING] Clearing all data from database...")
        self.execute_write("MATCH (n) DETACH DELETE n")
        print("[OK] Database cleared")

    def get_node_count(self) -> int:
        """Get total number of nodes in database"""
        result = self.execute_query("MATCH (n) RETURN count(n) as count")
        return result[0]["count"] if result else 0

    def get_relationship_count(self) -> int:
        """Get total number of relationships in database"""
        result = self.execute_query("MATCH ()-[r]->() RETURN count(r) as count")
        return result[0]["count"] if result else 0

    def get_database_stats(self) -> dict:
        """Get database statistics"""
        node_count = self.get_node_count()
        rel_count = self.get_relationship_count()

        # Get counts by label
        label_counts = {}
        result = self.execute_query(
            "CALL db.labels() YIELD label "
            "CALL apoc.cypher.run('MATCH (n:`' + label + '`) RETURN count(n) as count', {}) "
            "YIELD value RETURN label, value.count as count"
        )
        for record in result:
            label_counts[record["label"]] = record["count"]

        return {
            "total_nodes": node_count,
            "total_relationships": rel_count,
            "nodes_by_label": label_counts
        }


def initialize_schema(connection: Neo4jConnection, schema_file: str):
    """
    Initialize Neo4j schema from Cypher file

    Args:
        connection: Neo4jConnection instance
        schema_file: Path to .cypher file with schema definitions
    """
    print(f"Initializing schema from {schema_file}...")

    with open(schema_file, 'r', encoding='utf-8') as f:
        schema_content = f.read()

    # Split by statement (separated by semicolons)
    statements = [
        stmt.strip()
        for stmt in schema_content.split(';')
        if stmt.strip() and not stmt.strip().startswith('//')
    ]

    success_count = 0
    for stmt in statements:
        # Skip empty statements and comments
        if not stmt or stmt.startswith('//'):
            continue

        try:
            connection.execute_write(stmt)
            success_count += 1
        except Exception as e:
            # Some statements might fail if already exist, that's okay
            if "already exists" in str(e).lower() or "equivalent" in str(e).lower():
                success_count += 1
            else:
                print(f"[WARNING] Warning executing statement: {e}")

    print(f"[OK] Schema initialized ({success_count} statements executed)")


if __name__ == "__main__":
    # Test connection
    conn = Neo4jConnection()
    conn.connect()

    # Print database stats
    stats = conn.get_database_stats()
    print("\nDatabase Statistics:")
    print(f"  Total Nodes: {stats['total_nodes']}")
    print(f"  Total Relationships: {stats['total_relationships']}")
    if stats['nodes_by_label']:
        print("\n  Nodes by Label:")
        for label, count in stats['nodes_by_label'].items():
            print(f"    {label}: {count}")

    conn.close()
