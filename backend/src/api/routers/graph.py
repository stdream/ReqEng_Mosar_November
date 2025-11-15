"""
Graph Router
Handles graph visualization endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from models.schemas import GraphData
from services.neo4j_service import neo4j_service

router = APIRouter()


@router.get("/requirement/{req_id}", response_model=GraphData)
def get_requirement_graph(
    req_id: str,
    depth: int = Query(2, ge=1, le=4, description="Graph depth")
):
    """
    Get graph data for a requirement

    Returns data compatible with @neo4j-nvl/react:
    - nodes: Array of NodeModel
    - relationships: Array of RelationshipModel

    Args:
        req_id: Requirement ID
        depth: Traversal depth (1-4)

    Returns:
        Graph data with nodes and relationships
    """
    graph_data = neo4j_service.get_requirement_graph(req_id, depth)

    if not graph_data.get("nodes"):
        raise HTTPException(status_code=404, detail=f"No graph data found for {req_id}")

    return graph_data


@router.get("/impact/{req_id}", response_model=GraphData)
def get_impact_graph(
    req_id: str,
    depth: int = Query(3, ge=1, le=5),
    components: bool = Query(True, description="Include components"),
    tests: bool = Query(True, description="Include tests"),
    requirements: bool = Query(True, description="Include related requirements"),
    scenarios: bool = Query(True, description="Include scenarios")
):
    """
    Get impact analysis graph

    Args:
        req_id: Requirement ID to analyze
        depth: Analysis depth (1-5)
        components: Include affected components
        tests: Include affected tests
        requirements: Include related requirements
        scenarios: Include affected scenarios

    Returns:
        Graph data showing impact of requirement change
    """
    result = neo4j_service.get_impact_analysis(
        req_id=req_id,
        depth=depth,
        include_components=components,
        include_tests=tests,
        include_requirements=requirements,
        include_scenarios=scenarios
    )

    if not result.get("nodes"):
        raise HTTPException(status_code=404, detail=f"No impact data found for {req_id}")

    # Return only nodes and relationships (compatible with GraphData schema)
    return {
        "nodes": result["nodes"],
        "relationships": result["relationships"]
    }
