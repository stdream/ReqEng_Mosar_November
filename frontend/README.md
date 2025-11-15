# MOSAR GraphRAG - React Frontend

Professional React + TypeScript frontend for the MOSAR Requirements Management System.

## Tech Stack

- **React 18** + **TypeScript** - Modern UI framework
- **Vite** - Fast build tool and dev server
- **@neo4j-nvl/react** - Official Neo4j graph visualization
- **React Router** - Client-side routing
- **TanStack Query** - Data fetching and caching
- **Tailwind CSS** - Utility-first styling
- **Axios** - HTTP client

## Installation

```bash
npm install
```

## Development

Start the dev server (default: http://localhost:5173):

```bash
npm run dev
```

The app will connect to the FastAPI backend at `http://localhost:8000` (configurable via `.env`).

## Environment Variables

Create a `.env` file:

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Project Structure

```
src/
├── components/           # Reusable React components
│   └── GraphVisualization.tsx
├── pages/               # Page components (routes)
│   ├── HomePage.tsx
│   └── RequirementDetailPage.tsx
├── services/            # API service layer
│   ├── requirements-service.ts
│   └── graph-service.ts
├── types/               # TypeScript type definitions
│   ├── graph.ts
│   ├── requirement.ts
│   └── index.ts
├── lib/                 # Utilities and libraries
│   └── api-client.ts
├── App.tsx              # Main app with routing
└── main.tsx             # Entry point
```

## Features

### Home Page (`/`)
- Search requirements by ID pattern or full-text
- Quick statistics (220 requirements, 298 components, 21 tests, 23 scenarios)
- Quick access links to common requirements

### Requirement Detail (`/requirement/:reqId`)
- Requirement metadata (type, level, responsible)
- Full statement and verification method
- Statistics (connected components, tests, scenarios, related requirements)
- **Interactive Graph Visualization** with @neo4j-nvl/react
- Adjustable graph depth (1-4 hops)

### Graph Visualization
- Powered by `@neo4j-nvl/react` (official Neo4j React library)
- Force-directed layout
- Interactive node/relationship clicking
- Console logging for debugging

## API Integration

The frontend connects to the FastAPI backend via Axios:

- `GET /api/requirements/{id}` - Requirement with graph
- `GET /api/requirements/` - List requirements
- `GET /api/search` - Search requirements
- `GET /api/graph/requirement/{id}` - Graph data (NVL format)
- `GET /api/graph/impact/{id}` - Impact analysis

## Build for Production

```bash
npm run build
```

Output: `dist/` directory (static files ready for deployment)

## Preview Production Build

```bash
npm run preview
```

## Development Notes

- The app uses **Tailwind CSS** for styling (no CSS modules)
- All API calls are centralized in `services/` layer
- TypeScript types are shared with backend schema (NodeModel, RelationshipModel)
- React Query handles caching and background refetching
- Graph data format is **100% compatible with @neo4j-nvl/react**

## Troubleshooting

**CORS errors:**
- Ensure backend CORS allows `http://localhost:5173` (check `backend/src/config/settings.py`)

**Graph not rendering:**
- Check browser console for @neo4j-nvl/react errors
- Verify API returns `nodes` and `relationships` arrays
- Ensure NVL options are compatible with your data

**Backend connection failed:**
- Verify FastAPI is running: `cd backend/src && python -m api.main`
- Check `.env` has correct `VITE_API_BASE_URL`
