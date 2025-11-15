"""
Requirements Router
Handles requirement-related endpoints
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from models.schemas import (
    RequirementDetail,
    RequirementWithGraph,
    GraphData,
    NodeModel,
    RelationshipModel
)
from services.neo4j_service import neo4j_service

router = APIRouter()


@router.get("/{req_id}", response_model=RequirementWithGraph)
def get_requirement(
    req_id: str,
    depth: int = Query(2, ge=1, le=4, description="Graph depth to fetch")
):
    """
    Get requirement details with graph context

    Args:
        req_id: Requirement ID (e.g., 'S111', 'FuncR_S111')
        depth: Depth of graph traversal (1-4)

    Returns:
        Requirement details + graph data + statistics
    """
    # Get requirement details
    req_data = neo4j_service.get_requirement_by_id(req_id)

    if not req_data:
        raise HTTPException(status_code=404, detail=f"Requirement {req_id} not found")

    # Get graph context
    graph_data = neo4j_service.get_requirement_graph(req_id, depth)

    # Count connected entities
    nodes = graph_data.get("nodes", [])
    stats = {
        "components": sum(1 for n in nodes if "Component" in n.get("labels", []) or "Subsystem" in n.get("labels", [])),
        "tests": sum(1 for n in nodes if "TestCase" in n.get("labels", [])),
        "scenarios": sum(1 for n in nodes if "Scenario" in n.get("labels", [])),
        "related_requirements": sum(1 for n in nodes if "Requirement" in n.get("labels", [])) - 1  # Exclude self
    }

    return {
        "requirement": req_data,
        "graph": graph_data,
        "statistics": stats
    }


@router.get("/", response_model=List[RequirementDetail])
def list_requirements(
    type: Optional[str] = Query(None, description="Filter by requirement type"),
    limit: int = Query(100, ge=1, le=500)
):
    """
    List all requirements with optional filtering

    Args:
        type: Requirement type filter (e.g., 'FuncR', 'PerfR')
        limit: Maximum number of results (1-500)

    Returns:
        List of requirements
    """
    requirements = neo4j_service.get_all_requirements(type=type, limit=limit)

    return requirements
