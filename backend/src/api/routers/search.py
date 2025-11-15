"""
Search Router
Handles search endpoints
"""

from fastapi import APIRouter, Query
from typing import List
from models.schemas import SearchResult, SearchResponse
from services.neo4j_service import neo4j_service

router = APIRouter()


@router.get("/", response_model=SearchResponse)
def search(
    q: str = Query(..., min_length=1, description="Search query"),
    type: str = Query(None, description="Entity type filter"),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Search for requirements and entities

    Supports:
    - ID pattern matching (e.g., 'S1*', 'FuncR_*')
    - Full-text search

    Args:
        q: Search query
        type: Optional type filter ('requirement', 'component', etc.)
        limit: Maximum results (1-100)

    Returns:
        Search results with relevance scores
    """
    results = []

    # Check if query looks like an ID pattern
    if any(char in q for char in ['*', '_', '-']) or q.isupper():
        # ID pattern search
        req_results = neo4j_service.search_by_id_pattern(q, limit)

        for req in req_results:
            results.append({
                "id": req.get("id", ""),
                "type": "requirement",
                "title": req.get("display_id", req.get("id", "")),
                "description": req.get("statement", "")[:200],
                "properties": req,
                "relevance_score": 1.0  # Exact match
            })
    else:
        # Full-text search
        req_results = neo4j_service.search_requirements(q, limit)

        for req in req_results:
            results.append({
                "id": req.get("id", ""),
                "type": "requirement",
                "title": req.get("display_id", req.get("id", "")),
                "description": req.get("statement", "")[:200],
                "properties": req,
                "relevance_score": req.get("relevance_score", 0.5)
            })

    # Sort by relevance
    results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

    return {
        "query": q,
        "total": len(results),
        "results": results[:limit]
    }


@router.get("/suggest")
def suggest(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=20)
):
    """
    Get search suggestions (autocomplete)

    Args:
        q: Partial query string
        limit: Maximum suggestions (1-20)

    Returns:
        List of suggested IDs/titles
    """
    # Pattern: q* (starts with q)
    pattern = f"{q}.*"

    results = neo4j_service.search_by_id_pattern(pattern, limit)

    suggestions = [
        {
            "id": req.get("id", ""),
            "display": req.get("display_id", req.get("id", "")),
            "type": req.get("type", "")
        }
        for req in results
    ]

    return suggestions
