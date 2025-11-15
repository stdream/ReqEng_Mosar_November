# MOSAR GraphRAG API Backend

FastAPI backend for MOSAR Requirements Management System.

## Installation

```bash
cd backend
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root with:

```env
NEO4J_URI=neo4j://127.0.0.1:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=password
OPENAI_API_KEY=your_key_here
```

## Run

```bash
cd src
python -m api.main
```

Or with uvicorn:

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

## API Documentation

Once running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Endpoints

### Requirements
- `GET /api/requirements/{id}` - Get requirement with graph
- `GET /api/requirements/` - List all requirements

### Graph
- `GET /api/graph/requirement/{id}` - Get requirement graph
- `GET /api/graph/impact/{id}` - Get impact analysis graph

### Search
- `GET /api/search?q={query}` - Search requirements
- `GET /api/search/suggest?q={query}` - Autocomplete

### System
- `GET /health` - Health check
- `GET /api/stats` - System statistics

## Project Structure

```
backend/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI app
│   │   └── routers/             # API routers
│   │       ├── requirements.py
│   │       ├── graph.py
│   │       └── search.py
│   ├── services/
│   │   └── neo4j_service.py     # Neo4j operations
│   ├── models/
│   │   └── schemas.py           # Pydantic models
│   └── config/
│       └── settings.py          # Configuration
└── requirements.txt
```

## Development

### Install dev dependencies

```bash
pip install -r requirements.txt
pip install pytest httpx
```

### Run tests

```bash
pytest
```
