"""
Pydantic models for API request/response schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


# ============================================================================
# Node & Relationship Models (for NVL compatibility)
# ============================================================================

class NodeModel(BaseModel):
    """Node model compatible with @neo4j-nvl/react"""
    id: str
    labels: List[str] = []
    properties: Dict[str, Any] = {}
    caption: Optional[str] = None
    size: Optional[int] = None
    color: Optional[str] = None


class RelationshipModel(BaseModel):
    """Relationship model compatible with @neo4j-nvl/react"""
    id: str
    type: str
    startNode: str = Field(alias="from")
    endNode: str = Field(alias="to")
    properties: Dict[str, Any] = {}
    caption: Optional[str] = None
    color: Optional[str] = None

    class Config:
        populate_by_name = True


class GraphData(BaseModel):
    """Graph data for visualization"""
    nodes: List[NodeModel]
    relationships: List[RelationshipModel]


# ============================================================================
# Requirement Models
# ============================================================================

class RequirementType(str, Enum):
    """Requirement types"""
    FUNCTIONAL = "FuncR"
    PERFORMANCE = "PerfR"
    INTERFACE = "IntR"
    DESIGN = "DesR"
    PHYSICAL = "PhyR"
    OPERATIONAL = "OpR"
    SAFETY = "SafR"
    CONFIGURATION = "ConfR"


class RequirementLevel(str, Enum):
    """Requirement levels"""
    MANDATORY = "Mandatory"
    DESIRED = "Desired"
    OPTIONAL = "Optional"


class RequirementDetail(BaseModel):
    """Detailed requirement information"""
    id: str
    display_id: str
    type: str
    series: Optional[str] = None
    level: str
    statement: str
    verification: Optional[str] = None
    responsible: Optional[str] = None
    covers: Optional[List[str]] = []
    comment: Optional[str] = None


class RequirementWithGraph(BaseModel):
    """Requirement with its graph context"""
    requirement: RequirementDetail
    graph: GraphData
    statistics: Dict[str, int] = Field(
        default_factory=lambda: {
            "components": 0,
            "tests": 0,
            "scenarios": 0,
            "related_requirements": 0
        }
    )


# ============================================================================
# Search Models
# ============================================================================

class SearchRequest(BaseModel):
    """Search request"""
    query: str
    type: Optional[str] = None  # "requirement", "component", "test", etc.
    filters: Optional[Dict[str, Any]] = {}
    limit: int = 20


class SearchResult(BaseModel):
    """Single search result"""
    id: str
    type: str
    title: str
    description: Optional[str] = None
    properties: Dict[str, Any] = {}
    relevance_score: Optional[float] = None


class SearchResponse(BaseModel):
    """Search response"""
    query: str
    total: int
    results: List[SearchResult]


# ============================================================================
# Impact Analysis Models
# ============================================================================

class ImpactAnalysisRequest(BaseModel):
    """Impact analysis request"""
    requirement_id: str
    depth: int = Field(default=3, ge=1, le=5)
    include_components: bool = True
    include_tests: bool = True
    include_requirements: bool = True
    include_scenarios: bool = True


class ImpactStats(BaseModel):
    """Impact analysis statistics"""
    affected_components: int = 0
    affected_tests: int = 0
    related_requirements: int = 0
    affected_scenarios: int = 0
    total_nodes: int = 0
    total_relationships: int = 0


class ImpactAnalysisResponse(BaseModel):
    """Impact analysis response"""
    requirement_id: str
    graph: GraphData
    stats: ImpactStats
    critical_paths: List[List[str]] = []


# ============================================================================
# GraphRAG Models
# ============================================================================

class GraphRAGRequest(BaseModel):
    """GraphRAG query request"""
    question: str
    requirement_ids: Optional[List[str]] = None  # Seed requirements
    top_k: int = Field(default=10, ge=1, le=50)
    depth: int = Field(default=2, ge=1, le=4)


class GraphRAGContext(BaseModel):
    """GraphRAG context for LLM"""
    question: str
    direct_chunks: List[Dict[str, Any]] = []
    graph_context: Dict[str, Any] = {}
    graph_summary: Dict[str, int] = {}


class GraphRAGResponse(BaseModel):
    """GraphRAG response"""
    question: str
    answer: Optional[str] = None  # If LLM integrated
    context: GraphRAGContext
    graph: Optional[GraphData] = None


# ============================================================================
# Traceability Models
# ============================================================================

class TraceabilityPath(BaseModel):
    """Traceability path"""
    path_type: str  # "vertical", "horizontal", "coverage"
    nodes: List[NodeModel]
    relationships: List[RelationshipModel]
    description: str


class TraceabilityResponse(BaseModel):
    """Traceability response"""
    requirement_id: str
    paths: List[TraceabilityPath]
    graph: GraphData


# ============================================================================
# Statistics Models
# ============================================================================

class SystemStats(BaseModel):
    """System statistics"""
    total_requirements: int
    total_components: int
    total_tests: int
    total_scenarios: int
    total_chunks: int
    embedding_coverage: Dict[str, float]
    relationship_counts: Dict[str, int]
