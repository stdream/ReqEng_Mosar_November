"""
Neo4j Service Layer
Handles all database operations
"""

from neo4j import GraphDatabase, Driver, Session
from typing import List, Dict, Any, Optional
from config.settings import settings
import logging

logger = logging.getLogger(__name__)


class Neo4jService:
    """Neo4j database service"""

    def __init__(self):
        self.driver: Optional[Driver] = None
        self._connect()

    def _connect(self):
        """Connect to Neo4j database"""
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info(f"Connected to Neo4j at {settings.NEO4J_URI}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self):
        """Close database connection"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")

    def execute_query(self, query: str, parameters: Optional[Dict[str, Any]] = None) -> List[Dict]:
        """Execute a Cypher query and return results"""
        if not self.driver:
            raise RuntimeError("Neo4j driver not initialized")

        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    # ========================================================================
    # Requirement Queries
    # ========================================================================

    def get_requirement_by_id(self, req_id: str) -> Optional[Dict[str, Any]]:
        """Get requirement by ID"""
        query = """
        MATCH (r:Requirement)
        WHERE r.id = $req_id OR r.display_id = $req_id
        RETURN r {
            .*,
            covers: [(r)-[:COVERS]->(covered) | covered.id]
        } as requirement
        """

        results = self.execute_query(query, {"req_id": req_id})
        return results[0]["requirement"] if results else None

    def get_requirement_graph(self, req_id: str, depth: int = 2) -> Dict[str, List]:
        """
        Get graph data for a requirement
        Returns nodes and relationships for @neo4j-nvl/react
        """
        query = f"""
        MATCH (r:Requirement)
        WHERE r.id = $req_id OR r.display_id = $req_id

        CALL {{
            WITH r
            MATCH path = (r)-[*1..{depth}]-(n)
            RETURN collect(DISTINCT n) as related_nodes,
                   reduce(rels = [], p in collect(path) |
                          rels + relationships(p)) as all_rels
        }}

        WITH r, related_nodes, all_rels
        UNWIND related_nodes as node
        WITH r, collect(DISTINCT node) + [r] as all_nodes,
             reduce(unique_rels = [], rel in all_rels |
                    CASE WHEN NOT rel IN unique_rels THEN unique_rels + rel
                    ELSE unique_rels END) as relationships

        RETURN
            [n IN all_nodes | {{
                id: toString(id(n)),
                labels: labels(n),
                properties: properties(n)
            }}] as nodes,
            [rel IN relationships | {{
                id: toString(id(rel)),
                type: type(rel),
                startNode: toString(id(startNode(rel))),
                endNode: toString(id(endNode(rel))),
                properties: properties(rel)
            }}] as relationships
        """

        results = self.execute_query(query, {"req_id": req_id, "depth": depth})

        if not results:
            return {"nodes": [], "relationships": []}

        # Filter out relationships with None startNode or endNode
        relationships = [
            rel for rel in results[0].get("relationships", [])
            if rel.get("startNode") is not None and rel.get("endNode") is not None
        ]

        return {
            "nodes": results[0].get("nodes", []),
            "relationships": relationships
        }

    def get_all_requirements(self, type: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get all requirements with optional type filter"""
        where_clause = "WHERE r.type = $type" if type else ""

        query = f"""
        MATCH (r:Requirement)
        {where_clause}
        RETURN r {{
            .*,
            covers: [(r)-[:COVERS]->(covered) | covered.id]
        }} as requirement
        ORDER BY r.id
        LIMIT $limit
        """

        results = self.execute_query(query, {"type": type, "limit": limit})
        return [r["requirement"] for r in results]

    # ========================================================================
    # Search Queries
    # ========================================================================

    def search_requirements(self, query_text: str, limit: int = 20) -> List[Dict]:
        """Full-text search for requirements"""
        query = """
        CALL db.index.fulltext.queryNodes('requirement_fulltext', $query_text)
        YIELD node, score
        RETURN node {
            .*,
            relevance_score: score
        } as requirement
        ORDER BY score DESC
        LIMIT $limit
        """

        results = self.execute_query(query, {"query_text": query_text, "limit": limit})
        return [r["requirement"] for r in results]

    def search_by_id_pattern(self, pattern: str, limit: int = 20) -> List[Dict]:
        """Search by ID pattern (e.g., 'S1*', 'FuncR_*')"""
        query = """
        MATCH (r:Requirement)
        WHERE r.id =~ $pattern OR r.display_id =~ $pattern
        RETURN r {.*} as requirement
        ORDER BY r.id
        LIMIT $limit
        """

        # Convert pattern to regex (S1* -> S1.*)
        regex_pattern = pattern.replace("*", ".*")

        results = self.execute_query(query, {"pattern": regex_pattern, "limit": limit})
        return [r["requirement"] for r in results]

    # ========================================================================
    # Impact Analysis Queries
    # ========================================================================

    def get_impact_analysis(
        self,
        req_id: str,
        depth: int = 3,
        include_components: bool = True,
        include_tests: bool = True,
        include_requirements: bool = True,
        include_scenarios: bool = True
    ) -> Dict[str, Any]:
        """
        Get impact analysis for a requirement change
        """
        # Build conditional match patterns
        patterns = []
        if include_components:
            patterns.append("(r)-[:ALLOCATED_TO|REQUIRES]->(comp:Component|Subsystem|Interface)")
        if include_tests:
            patterns.append("(r)-[:VERIFIED_BY]->(test:TestCase)")
        if include_requirements:
            patterns.append("(r)-[:COVERS|REFINES]-(related:Requirement)")
        if include_scenarios:
            patterns.append("(r)-[:USED_IN_SCENARIOS]->(scenario:Scenario)")

        match_pattern = " OR ".join(patterns) if patterns else "(r)"

        query = f"""
        MATCH (r:Requirement)
        WHERE r.id = $req_id OR r.display_id = $req_id

        CALL {{
            WITH r
            MATCH path = (r)-[*1..{depth}]-(n)
            WHERE ({match_pattern})
            RETURN collect(DISTINCT n) as impacted_nodes,
                   reduce(rels = [], p in collect(path) |
                          rels + relationships(p)) as all_rels
        }}

        WITH r, impacted_nodes, all_rels

        RETURN
            [n IN impacted_nodes + [r] | {{
                id: toString(id(n)),
                labels: labels(n),
                properties: properties(n)
            }}] as nodes,
            [rel IN all_rels | {{
                id: toString(id(rel)),
                type: type(rel),
                startNode: toString(id(startNode(rel))),
                endNode: toString(id(endNode(rel))),
                properties: properties(rel)
            }}] as relationships,
            {{
                components: size([n IN impacted_nodes WHERE 'Component' IN labels(n) OR 'Subsystem' IN labels(n)]),
                tests: size([n IN impacted_nodes WHERE 'TestCase' IN labels(n)]),
                requirements: size([n IN impacted_nodes WHERE 'Requirement' IN labels(n)]),
                scenarios: size([n IN impacted_nodes WHERE 'Scenario' IN labels(n)])
            }} as stats
        """

        results = self.execute_query(query, {"req_id": req_id, "depth": depth})

        if not results:
            return {
                "nodes": [],
                "relationships": [],
                "stats": {"components": 0, "tests": 0, "requirements": 0, "scenarios": 0}
            }

        # Filter out relationships with None startNode or endNode
        relationships = [
            rel for rel in results[0].get("relationships", [])
            if rel.get("startNode") is not None and rel.get("endNode") is not None
        ]

        return {
            "nodes": results[0].get("nodes", []),
            "relationships": relationships,
            "stats": results[0].get("stats", {})
        }

    # ========================================================================
    # Traceability Queries
    # ========================================================================

    def get_vertical_traceability(self, req_id: str) -> List[Dict]:
        """
        Get vertical traceability path: Requirement → Component → Test → Scenario
        """
        query = """
        MATCH (r:Requirement)
        WHERE r.id = $req_id OR r.display_id = $req_id

        OPTIONAL MATCH path1 = (r)-[:ALLOCATED_TO]->(comp:Component)-[:TESTED_IN]->(test:TestCase)
        OPTIONAL MATCH path2 = (comp)-[:USED_IN_SCENARIOS]->(scenario:Scenario)

        RETURN
            collect(DISTINCT path1) as component_test_paths,
            collect(DISTINCT path2) as scenario_paths
        """

        return self.execute_query(query, {"req_id": req_id})

    # ========================================================================
    # Statistics Queries
    # ========================================================================

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics"""
        query = """
        MATCH (r:Requirement)
        OPTIONAL MATCH (c:Component)
        OPTIONAL MATCH (t:TestCase)
        OPTIONAL MATCH (s:Scenario)
        OPTIONAL MATCH (ch:Chunk)

        WITH
            count(DISTINCT r) as req_count,
            count(DISTINCT c) as comp_count,
            count(DISTINCT t) as test_count,
            count(DISTINCT s) as scenario_count,
            count(DISTINCT ch) as chunk_count

        MATCH (r:Requirement)
        WHERE r.embedding IS NOT NULL
        WITH req_count, comp_count, test_count, scenario_count, chunk_count,
             count(r) as req_with_emb

        MATCH (ch:Chunk)
        WHERE ch.embedding IS NOT NULL
        WITH req_count, comp_count, test_count, scenario_count, chunk_count,
             req_with_emb, count(ch) as chunk_with_emb

        MATCH ()-[rel]->()
        WITH req_count, comp_count, test_count, scenario_count, chunk_count,
             req_with_emb, chunk_with_emb, type(rel) as rel_type, count(*) as rel_count

        RETURN
            req_count, comp_count, test_count, scenario_count, chunk_count,
            req_with_emb, chunk_with_emb,
            collect({{type: rel_type, count: rel_count}}) as relationship_counts
        """

        results = self.execute_query(query)

        if not results:
            return {}

        data = results[0]

        return {
            "total_requirements": data.get("req_count", 0),
            "total_components": data.get("comp_count", 0),
            "total_tests": data.get("test_count", 0),
            "total_scenarios": data.get("scenario_count", 0),
            "total_chunks": data.get("chunk_count", 0),
            "embedding_coverage": {
                "requirements": data.get("req_with_emb", 0) / max(data.get("req_count", 1), 1),
                "chunks": data.get("chunk_with_emb", 0) / max(data.get("chunk_count", 1), 1)
            },
            "relationship_counts": {
                item["type"]: item["count"]
                for item in data.get("relationship_counts", [])
            }
        }


# Global service instance
neo4j_service = Neo4jService()
