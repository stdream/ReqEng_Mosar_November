# React + Neo4j NVL Architecture for MOSAR GraphRAG UI

**Date**: 2025-11-16
**Decision**: React + TypeScript + @neo4j-nvl/react + FastAPI
**Rationale**: Professional-grade UI with Neo4j's official React visualization library

---

## 1. 핵심 발견: @neo4j-nvl/react ⭐

### Neo4j Visualization Library (NVL)의 구성

Neo4j는 **3-tier 시각화 라이브러리**를 제공합니다:

1. **@neo4j-nvl/base** (TypeScript)
   - 핵심 그래프 시각화 엔진
   - Framework-agnostic (순수 JS/TS)
   - Neo4j Bloom과 동일한 렌더링 엔진

2. **@neo4j-nvl/react** (React wrapper)
   - React 컴포넌트로 wrapping
   - Hooks 지원 (useRef로 NVL instance 제어)
   - Props 기반 구성

3. **@neo4j-nvl/interaction-handlers**
   - Zoom, Pan, Drag, Hover 등
   - 즉시 사용 가능한 인터랙션

---

## 2. React 아키텍처 (권장 ✅)

### 전체 스택

```
┌─────────────────────────────────────────┐
│   React Frontend (TypeScript)           │
│   - Vite or Next.js                     │
│   - @neo4j-nvl/react                    │
│   - TailwindCSS                         │
│   - React Query                         │
└─────────────────────────────────────────┘
              ↓ (REST API)
┌─────────────────────────────────────────┐
│   FastAPI Backend (Python)              │
│   - GraphRAG service                    │
│   - Neo4j driver                        │
│   - OpenAI/Anthropic                    │
└─────────────────────────────────────────┘
              ↓
┌─────────────────────────────────────────┐
│   Neo4j Database (Local)                │
│   - 2,853 nodes                         │
│   - 15,292 relationships                │
└─────────────────────────────────────────┘
```

### Why React + NVL > Streamlit?

| 기준 | React + NVL | Streamlit |
|------|------------|-----------|
| **UI 품질** | ⭐⭐⭐⭐⭐ Professional | ⭐⭐⭐ Prototyping |
| **성능** | ⭐⭐⭐⭐⭐ Fast (SPA) | ⭐⭐⭐ Slow (reload) |
| **커스터마이징** | ⭐⭐⭐⭐⭐ Full control | ⭐⭐⭐ Limited |
| **UX** | ⭐⭐⭐⭐⭐ Modern SPA | ⭐⭐ Form-based |
| **확장성** | ⭐⭐⭐⭐⭐ Scalable | ⭐⭐⭐ Limited |
| **개발 속도** | ⭐⭐⭐ Medium | ⭐⭐⭐⭐⭐ Fast |
| **프로페셔널** | ✅ Production-ready | ⚠️ Research/demo |

**결론**:
- **Prototyping**: Streamlit ⭐
- **Production**: React + NVL ⭐⭐⭐⭐⭐

---

## 3. React 프로젝트 구조

```
mosar-graphrag-ui/
├── frontend/                          # React app (Vite + TypeScript)
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── graph/
│   │   │   │   ├── GraphVisualization.tsx    # NVL wrapper
│   │   │   │   ├── GraphLegend.tsx           # Node/edge legend
│   │   │   │   ├── GraphControls.tsx         # Zoom/layout controls
│   │   │   │   └── useGraphData.ts           # Custom hook
│   │   │   ├── requirement/
│   │   │   │   ├── RequirementCard.tsx
│   │   │   │   ├── RequirementDetail.tsx
│   │   │   │   └── RequirementList.tsx
│   │   │   ├── search/
│   │   │   │   ├── SearchBar.tsx
│   │   │   │   ├── SearchFilters.tsx
│   │   │   │   └── SearchResults.tsx
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       └── Layout.tsx
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── SearchPage.tsx
│   │   │   ├── RequirementDetailPage.tsx
│   │   │   ├── GraphExplorerPage.tsx
│   │   │   ├── ImpactAnalysisPage.tsx
│   │   │   └── GraphRAGChatPage.tsx
│   │   ├── hooks/
│   │   │   ├── useNeo4jQuery.ts              # React Query wrapper
│   │   │   ├── useGraphRAG.ts                # GraphRAG hook
│   │   │   └── useRequirement.ts             # Requirement hook
│   │   ├── services/
│   │   │   ├── api.ts                        # Axios instance
│   │   │   ├── requirements.ts               # API calls
│   │   │   ├── graph.ts                      # Graph data API
│   │   │   └── graphrag.ts                   # GraphRAG API
│   │   ├── types/
│   │   │   ├── graph.ts                      # NVL types
│   │   │   ├── requirement.ts                # Domain types
│   │   │   └── api.ts                        # API response types
│   │   ├── utils/
│   │   │   ├── graphTransform.ts             # Neo4j → NVL
│   │   │   ├── colors.ts                     # Color schemes
│   │   │   └── formatters.ts                 # Data formatters
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── index.css
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
└── backend/                           # FastAPI (Python)
    ├── src/
    │   ├── api/
    │   │   ├── main.py
    │   │   ├── routers/
    │   │   │   ├── requirements.py
    │   │   │   ├── graph.py
    │   │   │   ├── search.py
    │   │   │   └── graphrag.py
    │   │   └── models/
    │   │       └── schemas.py
    │   ├── services/
    │   │   ├── neo4j_service.py
    │   │   ├── graphrag_service.py
    │   │   └── vector_service.py
    │   └── config/
    │       └── settings.py
    ├── requirements.txt
    └── .env
```

---

## 4. 핵심 컴포넌트 구현

### 4.1 GraphVisualization.tsx (Main Component)

```typescript
import React, { useRef, useEffect } from 'react';
import { BasicNvlWrapper } from '@neo4j-nvl/react';
import type { NVL, Node, Relationship } from '@neo4j-nvl/base';

interface GraphVisualizationProps {
  nodes: Node[];
  relationships: Relationship[];
  onNodeClick?: (node: Node) => void;
  height?: string;
}

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  nodes,
  relationships,
  onNodeClick,
  height = '600px'
}) => {
  const nvlRef = useRef<NVL>(null);

  // NVL options
  const nvlOptions = {
    layout: 'forceDirected',
    initialZoom: 0.5,
    enableDragNodes: true,
    enablePan: true,
    enableZoom: true,
  };

  // Callbacks
  const nvlCallbacks = {
    onLayoutDone: () => console.log('Layout complete'),
    onNodeClick: (node: Node) => {
      console.log('Node clicked:', node);
      onNodeClick?.(node);
    },
  };

  // Customize node appearance based on labels
  useEffect(() => {
    if (nvlRef.current && nodes.length > 0) {
      nodes.forEach(node => {
        const labels = (node.properties as any)?.labels || [];

        if (labels.includes('Requirement')) {
          node.color = '#FF6B6B';  // Red
          node.size = 20;
        } else if (labels.includes('Component')) {
          node.color = '#4ECDC4';  // Teal
          node.size = 15;
        } else if (labels.includes('TestCase')) {
          node.color = '#45B7D1';  // Blue
          node.size = 12;
        } else if (labels.includes('Scenario')) {
          node.color = '#FFA07A';  // Light Salmon
          node.size = 15;
        }
      });

      nvlRef.current.updateNodesAndRelationships(nodes, relationships);
    }
  }, [nodes, relationships]);

  return (
    <div style={{ height, border: '1px solid #e5e7eb', borderRadius: '8px' }}>
      <BasicNvlWrapper
        nodes={nodes}
        rels={relationships}
        nvlOptions={nvlOptions}
        nvlCallbacks={nvlCallbacks}
        ref={nvlRef}
      />
    </div>
  );
};
```

### 4.2 useGraphData.ts (Custom Hook)

```typescript
import { useQuery } from '@tanstack/react-query';
import type { Node, Relationship } from '@neo4j-nvl/base';
import { graphApi } from '../services/api';

interface GraphData {
  nodes: Node[];
  relationships: Relationship[];
}

export const useGraphData = (requirementId: string, depth: number = 2) => {
  return useQuery<GraphData>({
    queryKey: ['graph', requirementId, depth],
    queryFn: async () => {
      const response = await graphApi.get(`/graph/requirement/${requirementId}`, {
        params: { depth }
      });

      // Transform Neo4j response to NVL format
      return transformNeo4jToNVL(response.data);
    },
    enabled: !!requirementId,
  });
};

function transformNeo4jToNVL(neo4jData: any): GraphData {
  const nodes: Node[] = neo4jData.nodes.map((n: any) => ({
    id: n.id.toString(),
    caption: n.properties.id || n.properties.name || '',
    properties: n.properties,
    labels: n.labels,
  }));

  const relationships: Relationship[] = neo4jData.relationships.map((r: any) => ({
    id: r.id.toString(),
    from: r.startNode.toString(),
    to: r.endNode.toString(),
    type: r.type,
    caption: r.type,
    properties: r.properties,
  }));

  return { nodes, relationships };
}
```

### 4.3 RequirementDetailPage.tsx

```typescript
import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { GraphVisualization } from '../components/graph/GraphVisualization';
import { RequirementCard } from '../components/requirement/RequirementCard';
import { useGraphData } from '../hooks/useGraphData';
import { useRequirement } from '../hooks/useRequirement';

export const RequirementDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [depth, setDepth] = useState(2);

  // Fetch requirement details
  const { data: requirement, isLoading: reqLoading } = useRequirement(id!);

  // Fetch graph data
  const { data: graphData, isLoading: graphLoading } = useGraphData(id!, depth);

  const handleNodeClick = (node: any) => {
    console.log('Navigate to:', node.properties.id);
    // Navigate to the clicked entity
  };

  if (reqLoading || graphLoading) {
    return <div className="flex items-center justify-center h-screen">
      <div className="text-xl">Loading...</div>
    </div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Requirement Metadata */}
      <RequirementCard requirement={requirement} />

      {/* Graph Controls */}
      <div className="my-6 flex items-center gap-4">
        <label className="font-semibold">Graph Depth:</label>
        <input
          type="range"
          min="1"
          max="4"
          value={depth}
          onChange={(e) => setDepth(Number(e.target.value))}
          className="w-48"
        />
        <span>{depth}</span>
      </div>

      {/* Graph Visualization */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Traceability Graph</h2>
        {graphData && (
          <GraphVisualization
            nodes={graphData.nodes}
            relationships={graphData.relationships}
            onNodeClick={handleNodeClick}
            height="700px"
          />
        )}
      </div>

      {/* Connected Entities Table */}
      <div className="mt-8 bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4">Connected Entities</h2>
        {/* Tables for Components, Tests, Scenarios */}
      </div>
    </div>
  );
};
```

### 4.4 ImpactAnalysisPage.tsx

```typescript
import React, { useState } from 'react';
import { GraphVisualization } from '../components/graph/GraphVisualization';
import { useQuery } from '@tanstack/react-query';
import { graphApi } from '../services/api';

export const ImpactAnalysisPage: React.FC = () => {
  const [requirementId, setRequirementId] = useState('S111');
  const [impactTypes, setImpactTypes] = useState({
    components: true,
    tests: true,
    requirements: true,
    scenarios: true,
  });

  const { data: impactData, isLoading } = useQuery({
    queryKey: ['impact', requirementId, impactTypes],
    queryFn: async () => {
      const response = await graphApi.get(`/impact/requirement/${requirementId}`, {
        params: impactTypes
      });
      return response.data;
    },
    enabled: !!requirementId,
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold mb-6">💥 Impact Analysis</h1>

      {/* Input Section */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <div className="mb-4">
          <label className="block font-semibold mb-2">
            Requirement to Change:
          </label>
          <input
            type="text"
            value={requirementId}
            onChange={(e) => setRequirementId(e.target.value)}
            className="border rounded px-4 py-2 w-64"
            placeholder="e.g., S111"
          />
        </div>

        {/* Impact Type Toggles */}
        <div className="flex gap-4">
          {Object.entries(impactTypes).map(([key, value]) => (
            <label key={key} className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={value}
                onChange={(e) => setImpactTypes({
                  ...impactTypes,
                  [key]: e.target.checked
                })}
              />
              <span className="capitalize">{key}</span>
            </label>
          ))}
        </div>
      </div>

      {/* Graph Visualization */}
      {impactData && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h2 className="text-2xl font-bold mb-4">Impact Graph</h2>
          <GraphVisualization
            nodes={impactData.nodes}
            relationships={impactData.relationships}
            height="800px"
          />
        </div>
      )}

      {/* Impact Summary */}
      {impactData && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-blue-100 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-blue-600">
              {impactData.stats.components}
            </div>
            <div className="text-gray-600">Affected Components</div>
          </div>
          <div className="bg-green-100 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-green-600">
              {impactData.stats.tests}
            </div>
            <div className="text-gray-600">Affected Tests</div>
          </div>
          <div className="bg-yellow-100 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-yellow-600">
              {impactData.stats.requirements}
            </div>
            <div className="text-gray-600">Related Requirements</div>
          </div>
          <div className="bg-purple-100 rounded-lg p-6 text-center">
            <div className="text-3xl font-bold text-purple-600">
              {impactData.stats.scenarios}
            </div>
            <div className="text-gray-600">Affected Scenarios</div>
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## 5. FastAPI Backend Structure

### 5.1 main.py

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import requirements, graph, search, graphrag

app = FastAPI(
    title="MOSAR GraphRAG API",
    version="1.0.0",
    description="Requirements Management & GraphRAG API"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(requirements.router, prefix="/api/requirements", tags=["Requirements"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(graphrag.router, prefix="/api/graphrag", tags=["GraphRAG"])

@app.get("/")
def read_root():
    return {"message": "MOSAR GraphRAG API", "version": "1.0.0"}
```

### 5.2 routers/graph.py

```python
from fastapi import APIRouter, Query
from services.neo4j_service import Neo4jService
from pydantic import BaseModel

router = APIRouter()
neo4j = Neo4jService()

class GraphData(BaseModel):
    nodes: list
    relationships: list

@router.get("/requirement/{req_id}", response_model=GraphData)
def get_requirement_graph(req_id: str, depth: int = Query(2, ge=1, le=4)):
    """
    Get graph data for a requirement with specified depth
    """
    query = f"""
    MATCH path = (r:Requirement {{id: $req_id}})-[*1..{depth}]-(n)
    WITH DISTINCT r, n, relationships(path) as rels
    RETURN
        collect(DISTINCT r) + collect(DISTINCT n) as nodes,
        reduce(allRels = [], rel in rels | allRels + rel) as relationships
    """

    result = neo4j.run_query(query, {"req_id": req_id})

    # Transform to NVL format
    nodes = []
    relationships = []

    for record in result:
        for node in record["nodes"]:
            nodes.append({
                "id": node.id,
                "labels": list(node.labels),
                "properties": dict(node)
            })

        for rel in record["relationships"]:
            relationships.append({
                "id": rel.id,
                "type": rel.type,
                "startNode": rel.start_node.id,
                "endNode": rel.end_node.id,
                "properties": dict(rel)
            })

    return GraphData(nodes=nodes, relationships=relationships)
```

---

## 6. 개발 순서

### Phase 5-A: Backend API (Day 1-2)
1. ✅ FastAPI project setup
2. ✅ Core routers (requirements, graph, search)
3. ✅ Neo4j service layer
4. ✅ Test with Postman

### Phase 5-B: React Frontend Setup (Day 3-4)
1. ✅ Create Vite + React + TypeScript project
2. ✅ Install dependencies:
   ```bash
   npm install @neo4j-nvl/react @neo4j-nvl/base
   npm install @tanstack/react-query axios react-router-dom
   npm install -D tailwindcss postcss autoprefixer
   ```
3. ✅ Setup routing, layout, and basic pages
4. ✅ Test graph visualization component

### Phase 5-C: Core Pages (Day 5-7)
1. ✅ Search page
2. ✅ Requirement detail page
3. ✅ Graph explorer page
4. ✅ Impact analysis page

### Phase 5-D: GraphRAG Integration (Day 8-9)
1. ✅ GraphRAG API endpoints
2. ✅ Chat interface
3. ✅ Context visualization

### Phase 5-E: Polish & Deploy (Day 10)
1. ✅ UI/UX improvements
2. ✅ Error handling
3. ✅ Docker containerization
4. ✅ Documentation

**Total**: ~10 days (2 weeks with buffer)

---

## 7. 최종 결정: React + NVL ✅

### Pros
- ⭐⭐⭐⭐⭐ **Professional UI** - Production-grade, not prototype
- ⭐⭐⭐⭐⭐ **Neo4j Official Library** - Best integration with Neo4j
- ⭐⭐⭐⭐⭐ **Performance** - SPA, no page reloads
- ⭐⭐⭐⭐⭐ **Customization** - Full control over UI/UX
- ⭐⭐⭐⭐ **Ecosystem** - Huge React ecosystem

### Cons
- ⚠️ **Development Time** - 2x slower than Streamlit
- ⚠️ **Complexity** - More code to maintain

### 결론
"싸보이지 않는" 프로페셔널한 UI를 원한다면 **React + @neo4j-nvl/react**가 정답입니다! ✅

---

**시작하시겠습니까?** 🚀
