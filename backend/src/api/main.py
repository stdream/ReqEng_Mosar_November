"""
MOSAR GraphRAG API - Main FastAPI Application
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config.settings import settings
from api.routers import requirements, graph, search
from services.neo4j_service import neo4j_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Connecting to Neo4j at {settings.NEO4J_URI}")

    yield

    # Shutdown
    logger.info("Shutting down application")
    neo4j_service.close()
    logger.info("Neo4j connection closed")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    ## MOSAR GraphRAG Requirements Management API

    A GraphRAG-based requirements traceability and impact analysis system.

    ### Features
    - **Requirements Management**: CRUD operations for requirements
    - **Graph Visualization**: Neo4j graph data for @neo4j-nvl/react
    - **Impact Analysis**: Analyze impact of requirement changes
    - **Search**: Full-text and pattern-based search
    - **GraphRAG**: Natural language queries over requirements (coming soon)

    ### Data Model
    - 220 Requirements
    - 298 Components
    - 21 Test Cases
    - 23 Scenarios
    - 2,853 Total Nodes
    - 15,292 Relationships
    """,
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(
    requirements.router,
    prefix=f"{settings.API_PREFIX}/requirements",
    tags=["Requirements"]
)
app.include_router(
    graph.router,
    prefix=f"{settings.API_PREFIX}/graph",
    tags=["Graph Visualization"]
)
app.include_router(
    search.router,
    prefix=f"{settings.API_PREFIX}/search",
    tags=["Search"]
)


# Root endpoint
@app.get("/")
def read_root():
    """API root endpoint"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "requirements": f"{settings.API_PREFIX}/requirements",
            "graph": f"{settings.API_PREFIX}/graph",
            "search": f"{settings.API_PREFIX}/search"
        }
    }


# Health check
@app.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        # Test Neo4j connection
        neo4j_service.driver.verify_connectivity()
        neo4j_status = "connected"
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        neo4j_status = "disconnected"

    return {
        "status": "healthy" if neo4j_status == "connected" else "unhealthy",
        "neo4j": neo4j_status,
        "version": settings.APP_VERSION
    }


# Statistics endpoint
@app.get(f"{settings.API_PREFIX}/stats")
def get_statistics():
    """Get system statistics"""
    stats = neo4j_service.get_system_statistics()
    return stats


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Development only
        log_level="info"
    )
