# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **MOSAR Requirements Engineering & GraphRAG System** - a knowledge graph-based requirements management system that integrates system engineering lifecycle documents with Neo4j and GraphRAG capabilities. The project combines:

1. **MOSAR Project Documents**: System Requirements Document (SRD), Preliminary Design Document (PDD/D2.4), Detailed Design Document (DDD/D3.6), and Demonstration Procedures (D3.5)
2. **Neo4j GraphRAG Python Library**: Official Neo4j GraphRAG package for building graph retrieval augmented generation applications
3. **Custom RM System**: A requirements traceability and impact analysis system built on Neo4j

## Purpose

Build a GraphRAG-based requirements management system that:
- Converts MOSAR lifecycle documents into a Neo4j knowledge graph
- Enables traceability from requirements → design → components → tests → demonstrations
- Provides impact analysis and coverage verification
- Supports natural language queries over requirements using GraphRAG patterns

## Key Technologies

- **Database**: Neo4j 5.x (graph database for requirements, components, scenarios, tests)
- **Backend**: Python with FastAPI (specified in PRD)
- **GraphRAG**: Neo4j GraphRAG Python package (v1.10.1)
- **LLM Integration**: OpenAI, Anthropic, Cohere, Ollama, Vertex AI (configurable)
- **Embeddings**: OpenAI, Cohere, Mistral, Ollama, sentence-transformers

## Repository Structure

```
ReqEng_1114/
├── Documents/                          # MOSAR project documents (source data)
│   ├── System Requirements Document_MOSAR.md
│   ├── MOSAR-WP2-D2.4-SA_1.1.0-Preliminary-Design-Document.md
│   ├── MOSAR-WP3-D3.6-SA_1.2.0-Detailed-Design-Document.md
│   ├── MOSAR-WP3-D3.5-DLR_1.1.0-Demonstration-Procedures.md
│   └── mosar_requirements_all.csv     # Structured requirements data
├── neo4j-graphrag-python-main/        # Neo4j GraphRAG library
│   ├── src/neo4j_graphrag/
│   │   ├── embeddings/                # Various embedding providers
│   │   ├── llm/                       # LLM integrations
│   │   ├── retrievers/                # Vector, hybrid, text2cypher retrievers
│   │   ├── generation/                # RAG pipeline
│   │   ├── experimental/              # KG building pipelines & components
│   │   │   ├── pipeline/              # Pipeline, SimpleKGPipeline
│   │   │   └── components/            # Loaders, extractors, splitters, writers
│   │   ├── indexes.py                 # Vector/fulltext index operations
│   │   ├── schema.py                  # Graph schema definitions
│   │   └── types.py                   # Core type definitions
│   └── examples/                      # Reference implementations
└── prd.md                             # Product Requirements Document (Korean)
```

## Data Model (Neo4j Schema)

The system implements a **three-layer graph architecture** as defined in prd.md:

### Lexical Layer
- `(:Document)` - SRD, PDD, DDD, DEMO documents
- `(:Section)` - Document sections with hierarchical numbering (2 → 2.1 → 2.1.1)
- `(:Chunk)` - Text chunks with embeddings for vector search
- Relationships: `HAS_SECTION`, `HAS_SUBSECTION`, `HAS_CHUNK`, `NEXT_CHUNK`

### Domain Layer
- `(:Requirement)` - System requirements with properties: id, series (S100-S800), type (FuncR/PerfR/IntR/etc), level, statement, verification, responsible
- `(:Scenario)` - S1-S5 scenarios
- `(:Component)` - Hardware components (HOTDOCK, R-ICU, WM, cPDU, BAT, THS, VPS)
- `(:Subsystem)` - Power, Data, Thermal, Visual subsystems
- `(:SoftwareComponent)` - SW modules (Network Reconfiguration, Discovery, FES, Planner)
- `(:TestCase)` - Component tests (CT-*), Integration tests (IT-*), Demo tests
- `(:Interface)` - HOTDOCK interface, SpaceWire links
- Relationships: `REFINES`, `COVERS`, `ALLOCATED_TO`, `REALIZED_BY`, `VERIFIED_BY`, `TESTED_IN`, `DEMONSTRATED_BY`, `DESCRIBED_IN`

### Link Layer
- `(Chunk)-[:MENTIONS_REQUIREMENT]->(Requirement)`
- `(Chunk)-[:MENTIONS_COMPONENT]->(Component)`
- `(Chunk)-[:MENTIONS_SCENARIO]->(Scenario)`
- `(Chunk)-[:DESCRIBES_TEST]->(TestCase)`

## Neo4j GraphRAG Library Architecture

The `neo4j-graphrag-python-main/` directory contains the official Neo4j library with:

### Core Modules
- **Pipeline System** (`experimental/pipeline/`): Orchestrates KG construction workflows
  - `SimpleKGPipeline`: Simplified API for building knowledge graphs from text/PDF
  - `Pipeline`: Full customizable pipeline with components

- **Components** (`experimental/components/`):
  - Loaders: PDF, text, custom loaders
  - Splitters: Fixed-size, LangChain, LlamaIndex splitters
  - Extractors: LLM-based entity/relation extraction with JSON schema
  - Writers: Neo4j writer for graph persistence
  - Resolvers: Entity resolution (fuzzy matching, spaCy)
  - Schema builders: Extract or define graph schemas

- **Retrievers** (`retrievers/`):
  - `VectorRetriever`: Similarity search over embeddings
  - `VectorCypherRetriever`: Vector search + graph traversal
  - `HybridRetriever`: Combines vector + fulltext search
  - `HybridCypherRetriever`: Hybrid search + graph queries
  - `Text2CypherRetriever`: Natural language to Cypher query
  - External retrievers for Weaviate, Pinecone, Qdrant

- **Generation** (`generation/`): `GraphRAG` class for RAG pipeline (retriever + LLM)

## Development Commands

### Neo4j GraphRAG Library Development

```bash
# Install dependencies (requires Poetry)
cd neo4j-graphrag-python-main
poetry install --with dev

# Install with specific LLM provider
poetry install --with dev -E openai
poetry install --with dev -E anthropic

# Install all extras for full functionality
poetry install --all-extras

# Code formatting and linting (required before commits)
pre-commit run --file path/to/file

# Run unit tests
poetry run pytest tests/unit

# Run E2E tests (requires Neo4j, Weaviate via Docker)
docker compose -f tests/e2e/docker-compose.yml up
poetry run pytest tests/e2e
```

### MOSAR RM System Development (To Be Implemented)

Based on prd.md specifications, the custom system should support:

```bash
# Start Neo4j database
# (Connection details: NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

# Data ingestion pipeline
python ingest_documents.py      # Load SRD/PDD/DDD/DEMO into graph
python ingest_requirements.py   # Load mosar_requirements_all.csv

# Start API server (FastAPI)
python main.py  # or: uvicorn main:app --reload

# API endpoints (planned):
# GET /requirements/{id}          - Get requirement + 1-hop neighbors
# GET /trace/requirement/{id}/vertical - Vertical traceability
# GET /impact/requirement/{id}    - Impact analysis
# POST /rag/context               - GraphRAG context generation
```

## Important Implementation Notes

### Requirements CSV Structure
`Documents/mosar_requirements_all.csv` contains:
- `id`: Requirement identifier (S101, A113, etc.)
- `display_id`: Full ID with prefix (FuncR_S101, DesR_A401)
- `type`: FuncR, PerfR, IntR, DesR, PhyR, OpR, SafR, ConfR
- `series`: S100-S800 (Space Scenarios), A/B/C/D xxx (Demonstrator requirements)
- `level`: Mandatory, Desired, Optional
- `statement`: Requirement text
- `covers`: Related requirement IDs (for COVERS relationship)
- `verification`: Verification method
- `responsible`: Partner organization

### Neo4j Constraints & Indexes
Must create before ingestion:
```cypher
// Unique constraints
CREATE CONSTRAINT req_id IF NOT EXISTS FOR (r:Requirement) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;

// Vector indexes (dimension must match embedding model)
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:Chunk) ON c.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 3072,           // for text-embedding-3-large
  `vector.similarity_function`: 'euclidean'
}};

// Fulltext indexes for hybrid search
CREATE FULLTEXT INDEX chunk_text IF NOT EXISTS FOR (c:Chunk) ON EACH [c.text];
```

### Entity Extraction from Documents
Use LLM-based extraction to link Chunks to domain entities:
- Define Pydantic schema for entities (Requirement, Component, Scenario, TestCase)
- Use `LLMEntityRelationExtractor` with custom prompts
- Extract mentions from document chunks → create `MENTIONS_*` relationships

### GraphRAG Query Pattern
```python
from neo4j_graphrag import GraphRAG, VectorRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings

# 1. Vector search for relevant chunks
retriever = VectorRetriever(driver, "chunk_embeddings", embedder)

# 2. Expand to domain entities via graph traversal
# (Use VectorCypherRetriever with custom Cypher to get Requirements/Components)

# 3. Generate answer with LLM
rag = GraphRAG(retriever=retriever, llm=llm)
response = rag.search(query_text="What are the requirements for FuncR_S111?")
```

## Traceability Queries

Key Cypher queries for requirements management:

```cypher
// Vertical traceability: Requirement → Design → Test → Demo
MATCH path = (r:Requirement {id: 'FuncR_S111'})
  -[:REALIZED_BY]->(c:Component)
  -[:TESTED_IN]->(t:TestCase)
  -[:DEMONSTRATED_BY]->(s:Scenario)
RETURN path;

// Impact analysis: What depends on this requirement?
MATCH (r:Requirement {id: 'FuncR_S111'})
OPTIONAL MATCH (r)<-[:COVERS]-(dependent:Requirement)
OPTIONAL MATCH (r)-[:ALLOCATED_TO]->(comp)
OPTIONAL MATCH (r)-[:VERIFIED_BY]->(test)
RETURN r, collect(DISTINCT dependent) as dependents,
       collect(DISTINCT comp) as components,
       collect(DISTINCT test) as tests;

// Coverage analysis: Which requirements lack test verification?
MATCH (r:Requirement)
WHERE NOT EXISTS { (r)-[:VERIFIED_BY]->(:TestCase) }
RETURN r.id, r.statement;
```

## Key Design Decisions (from prd.md)

1. **APOC Core Library Required**: Neo4j APOC must be installed for pipeline operations
2. **Idempotent Ingestion**: Re-running ingestion should safely update or recreate nodes
3. **Project ID Field**: Include `project_id` for future multi-project support (currently MOSAR only)
4. **LLM Abstraction**: GraphRAG context generation returns JSON, LLM invocation happens externally
5. **Document Section Hierarchy**: Preserve section numbering (2 → 2.1 → 2.1.1) with `HAS_SUBSECTION` relationships

## Current Project Status

- **Phase 1 (In Progress)**: Data model design, document analysis, GraphRAG library integration
- **Next Steps**:
  1. Implement document parsers (Markdown → Neo4j)
  2. Build CSV ingestion pipeline for requirements
  3. Create entity extraction pipeline (Chunk → Domain entities)
  4. Develop FastAPI endpoints for traceability/search
  5. Build GraphRAG query interface

## Testing Strategy

- **Unit tests**: Test individual parsers, ingesters, query functions
- **Integration tests**: Test against live Neo4j instance with sample data
- **E2E tests**: Full pipeline from document ingestion → query → GraphRAG answer
- **Test data**: Use small subset of MOSAR documents for faster iteration
