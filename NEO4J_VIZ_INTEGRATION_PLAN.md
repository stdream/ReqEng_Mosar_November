# Neo4j-Viz Integration Plan for MOSAR GraphRAG UI

**Date**: 2025-11-16
**Package**: `neo4j-viz` (Neo4j Graph Visualization for Python)
**Location**: `C:\Hee\SpaceAI\ReqEng_1114\python-graph-visualization-main`

---

## 1. Package Overview

### What is neo4j-viz?

`neo4j-viz` is Neo4j's official Python package for creating interactive graph visualizations:
- Wraps the Neo4j Visualization JavaScript library (NVL)
- Outputs `IPython.display.HTML` for Jupyter Notebooks or Streamlit
- Can export to standalone HTML files for web browsers

### Key Features Relevant to Our Project

**✅ Perfect Match for MOSAR GraphRAG:**

1. **Direct Neo4j Integration**
   - `from_neo4j(driver)` - Direct connection to our Neo4j database
   - Query results → Visualization in one step
   - Supports Neo4j Driver, Result, or Graph objects

2. **Node Customization**
   - Sizing by property (e.g., requirement criticality)
   - Colors by type (Requirement, Component, Scenario, Test)
   - Captions (requirement IDs, component names)
   - Tooltips on hover (show statement, metadata)
   - Pinning nodes

3. **Relationship Features**
   - Color coding (ALLOCATED_TO, VERIFIED_BY, COVERS, etc.)
   - Captions (relationship types)
   - Tooltips (confidence scores, evidence)

4. **Interactive Graph**
   - Zoom & pan
   - Move nodes
   - Multiple layouts (force-directed, hierarchical)
   - Click to expand

5. **Multiple Output Options**
   - Jupyter Notebook (IPython.display.HTML)
   - Streamlit app (streamlit.components.html)
   - Standalone HTML export
   - FastAPI/Flask web embedding

---

## 2. Integration Architecture

### Option 1: Streamlit-Based UI (Recommended ⭐)

**Why Streamlit?**
- Fastest development (Python-only, no React/JS needed)
- Native support for `neo4j-viz` (see `streamlit-example.py`)
- Built-in widgets (sliders, checkboxes, text inputs)
- Easy deployment (Streamlit Cloud, Docker)
- Perfect for research/demo applications

**Architecture:**
```
User Browser
    ↓
Streamlit App (Python)
    ↓
Neo4j-Viz VisualizationGraph
    ↓
Neo4j Database (Local)
```

**Tech Stack:**
- Frontend: Streamlit (Python)
- Visualization: neo4j-viz
- Backend Logic: Python services (same as planned FastAPI)
- Database: Neo4j (local)

---

### Option 2: FastAPI + HTML Export

**Architecture:**
```
React Frontend
    ↓ (API calls)
FastAPI Backend
    ↓ (generate visualization)
Neo4j-Viz → HTML export
    ↓ (return HTML)
React embeds <iframe>
```

**Tech Stack:**
- Frontend: React + TypeScript
- Backend: FastAPI
- Visualization: neo4j-viz (HTML export)
- Database: Neo4j

---

### Option 3: Hybrid (Streamlit + FastAPI)

**Use Streamlit for visualization-heavy pages:**
- Graph exploration
- Impact analysis
- Traceability views

**Use React for data-heavy pages:**
- Search interface
- Requirement detail tables
- Coverage dashboards

---

## 3. Detailed Streamlit Implementation Plan

### 3.1 Project Structure

```
src/
├── ui/                                    # Streamlit UI
│   ├── app.py                            # Main Streamlit app
│   ├── pages/
│   │   ├── 1_🔍_Search.py               # Search interface
│   │   ├── 2_📊_Requirement_Detail.py   # Req detail + graph
│   │   ├── 3_🌐_Graph_Explorer.py       # Interactive graph
│   │   ├── 4_💥_Impact_Analysis.py      # Impact analysis
│   │   └── 5_🤖_GraphRAG_Chat.py        # Natural language Q&A
│   ├── components/
│   │   ├── graph_viz.py                 # Graph visualization wrapper
│   │   ├── requirement_card.py          # Requirement display
│   │   └── filters.py                   # Search filters
│   └── services/
│       ├── neo4j_service.py             # Neo4j queries
│       ├── graphrag_service.py          # GraphRAG logic
│       └── viz_service.py               # Visualization generation
└── api/                                  # FastAPI (optional)
    └── main.py                           # REST API endpoints
```

### 3.2 Core Components

#### Main App (app.py)
```python
import streamlit as st
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

# Page config
st.set_page_config(
    page_title="MOSAR GraphRAG Requirements Management",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Neo4j connection (cached)
@st.cache_resource
def get_neo4j_driver():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )

driver = get_neo4j_driver()

# Home page
st.title("🚀 MOSAR Requirements Management System")
st.markdown("""
**GraphRAG-based Requirements Traceability & Impact Analysis**

- 220 Requirements
- 2,853 Nodes
- 15,292 Relationships
- 100% Embedding Coverage
""")

# Quick stats
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Requirements", "220")
with col2:
    st.metric("Components", "298")
with col3:
    st.metric("Test Cases", "21")
with col4:
    st.metric("Scenarios", "23")
```

#### Graph Visualization Component (components/graph_viz.py)
```python
from neo4j_viz import VisualizationGraph
from neo4j_viz.neo4j import from_neo4j
import streamlit.components.v1 as components

def render_requirement_graph(driver, req_id: str, depth: int = 2):
    """
    Render graph for a specific requirement with its neighbors
    """
    query = f"""
    MATCH path = (r:Requirement {{id: $req_id}})-[*1..{depth}]-(n)
    RETURN path
    LIMIT 100
    """

    with driver.session() as session:
        result = session.run(query, req_id=req_id)

        # Create VisualizationGraph from Neo4j result
        VG = from_neo4j(result)

        # Customize node colors by type
        for node in VG.nodes:
            labels = node.properties.get("labels", [])
            if "Requirement" in labels:
                node.color = "#FF6B6B"  # Red
                node.size = 20
            elif "Component" in labels:
                node.color = "#4ECDC4"  # Teal
                node.size = 15
            elif "TestCase" in labels:
                node.color = "#45B7D1"  # Blue
                node.size = 12
            elif "Scenario" in labels:
                node.color = "#FFA07A"  # Light Salmon
                node.size = 15

        # Customize relationship colors
        for rel in VG.relationships:
            rel_type = rel.properties.get("type", "")
            if rel_type == "ALLOCATED_TO":
                rel.color = "#2ECC71"
            elif rel_type == "VERIFIED_BY":
                rel.color = "#3498DB"
            elif rel_type == "COVERS":
                rel.color = "#E74C3C"

        # Render
        html = VG.render(height="600px", initial_zoom=0.5)

        return html

def display_graph(html_output):
    """Display the graph visualization in Streamlit"""
    components.html(html_output.data, height=600)
```

#### Requirement Detail Page (pages/2_📊_Requirement_Detail.py)
```python
import streamlit as st
from components.graph_viz import render_requirement_graph, display_graph
from services.neo4j_service import get_requirement_details

st.title("📊 Requirement Detail View")

# Sidebar: Requirement selector
with st.sidebar:
    req_id = st.text_input("Requirement ID", "S101", key="req_id_input")
    depth = st.slider("Graph Depth", 1, 3, 2)
    show_properties = st.checkbox("Show All Properties", value=False)

if req_id:
    # Get requirement details from Neo4j
    req_data = get_requirement_details(st.session_state.driver, req_id)

    if req_data:
        # Display requirement card
        st.subheader(f"Requirement: {req_data['display_id']}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Type", req_data['type'])
        with col2:
            st.metric("Level", req_data['level'])
        with col3:
            st.metric("Responsible", req_data.get('responsible', 'N/A'))

        st.markdown(f"**Statement:** {req_data['statement']}")

        # Graph visualization
        st.subheader("🌐 Traceability Graph")
        html_output = render_requirement_graph(
            st.session_state.driver,
            req_id,
            depth
        )
        display_graph(html_output)

        # Connected entities (table view)
        st.subheader("🔗 Connected Entities")

        tab1, tab2, tab3 = st.tabs(["Components", "Tests", "Scenarios"])

        with tab1:
            components = get_connected_components(st.session_state.driver, req_id)
            st.dataframe(components)

        with tab2:
            tests = get_connected_tests(st.session_state.driver, req_id)
            st.dataframe(tests)

        with tab3:
            scenarios = get_connected_scenarios(st.session_state.driver, req_id)
            st.dataframe(scenarios)
    else:
        st.error(f"Requirement {req_id} not found")
```

#### Impact Analysis Page (pages/4_💥_Impact_Analysis.py)
```python
import streamlit as st
from components.graph_viz import display_graph
from neo4j_viz import VisualizationGraph
from neo4j_viz.neo4j import from_neo4j

st.title("💥 Impact Analysis")

st.markdown("""
Analyze the impact of changing a requirement on the system.
This shows all entities that depend on or are related to the selected requirement.
""")

# Sidebar
with st.sidebar:
    req_id = st.text_input("Requirement to Change", "S111")
    max_depth = st.slider("Analysis Depth", 1, 4, 3)

    st.markdown("---")
    st.markdown("**Impact Types:**")
    show_allocated = st.checkbox("Allocated Components", value=True)
    show_tests = st.checkbox("Verification Tests", value=True)
    show_related = st.checkbox("Related Requirements", value=True)
    show_scenarios = st.checkbox("Scenarios", value=True)

if req_id:
    # Build dynamic query based on selected impact types
    query_parts = []

    if show_allocated:
        query_parts.append("(r)-[:ALLOCATED_TO]->(comp:Component)")
    if show_tests:
        query_parts.append("(r)-[:VERIFIED_BY]->(test:TestCase)")
    if show_related:
        query_parts.append("(r)-[:COVERS|REQUIRES]-(related:Requirement)")
    if show_scenarios:
        query_parts.append("(r)-[:USED_IN_SCENARIOS]->(scenario:Scenario)")

    query = f"""
    MATCH (r:Requirement {{id: $req_id}})
    OPTIONAL MATCH path1 = {query_parts[0] if query_parts else "(r)"}
    RETURN r, path1
    LIMIT 200
    """

    with st.session_state.driver.session() as session:
        result = session.run(query, req_id=req_id)

        # Create visualization
        VG = from_neo4j(result)

        # Highlight the changed requirement
        for node in VG.nodes:
            if node.properties.get("id") == req_id:
                node.color = "#E74C3C"  # Red for changed req
                node.size = 30

        html = VG.render(height="700px", initial_zoom=0.4)
        display_graph(html)

    # Summary statistics
    st.subheader("📊 Impact Summary")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        affected_components = count_affected(driver, req_id, "Component")
        st.metric("Affected Components", affected_components)

    with col2:
        affected_tests = count_affected(driver, req_id, "TestCase")
        st.metric("Affected Tests", affected_tests)

    with col3:
        related_reqs = count_affected(driver, req_id, "Requirement")
        st.metric("Related Requirements", related_reqs)

    with col4:
        affected_scenarios = count_affected(driver, req_id, "Scenario")
        st.metric("Affected Scenarios", affected_scenarios)

    # Export impact report
    if st.button("📥 Export Impact Report (CSV)"):
        csv_data = generate_impact_csv(driver, req_id)
        st.download_button(
            "Download CSV",
            csv_data,
            f"impact_analysis_{req_id}.csv",
            "text/csv"
        )
```

---

## 4. Implementation Phases

### Phase 5-A: Streamlit Setup & Basic Visualization (Day 1-2)

**Tasks:**
1. ✅ Install neo4j-viz package
   ```bash
   pip install neo4j-viz
   ```

2. ✅ Create Streamlit project structure
   ```bash
   mkdir -p src/ui/{pages,components,services}
   ```

3. ✅ Implement main app.py with Neo4j connection

4. ✅ Create basic graph visualization component

5. ✅ Test with simple query (e.g., show all requirements)

**Deliverables:**
- Working Streamlit app with Neo4j connection
- Basic graph visualization rendering
- Simple navigation structure

---

### Phase 5-B: Core Pages Implementation (Day 3-5)

**Tasks:**
1. ✅ Search Interface page
   - Text search (requirement ID, keywords)
   - Filters (type, level, responsible)
   - Results table with click-to-view

2. ✅ Requirement Detail page
   - Requirement metadata card
   - Traceability graph (depth 1-3)
   - Connected entities tables
   - Related chunks/documents

3. ✅ Graph Explorer page
   - Full graph visualization
   - Node filtering by type
   - Edge filtering by relationship type
   - Click to expand neighborhoods

4. ✅ Impact Analysis page
   - Select requirement to change
   - Show affected entities
   - Export impact report (CSV)

**Deliverables:**
- 4 functional Streamlit pages
- Interactive graph visualizations
- Data export functionality

---

### Phase 5-C: GraphRAG Integration (Day 6-7)

**Tasks:**
1. ✅ Implement GraphRAG service
   - Vector search integration
   - Graph traversal logic
   - Context generation

2. ✅ Create GraphRAG Chat page
   - Natural language input
   - Context visualization (which chunks/entities used)
   - LLM response display
   - Follow-up questions

3. ✅ Add vector similarity visualization
   - Show similar chunks in graph
   - Visualize SIMILAR_TO relationships
   - Show embedding space neighbors

**Deliverables:**
- Working GraphRAG chat interface
- Context visualization
- Similarity-based graph views

---

## 5. Advantages of neo4j-viz for MOSAR

### ✅ Perfect Fit

1. **Native Neo4j Integration**
   - Direct driver connection → visualization
   - No data transformation needed
   - Automatic property mapping

2. **Python-Only Development**
   - No JavaScript/React required
   - Faster development (Streamlit is Python)
   - Easier for researchers/students to modify

3. **Research-Friendly**
   - Jupyter Notebook support
   - Export standalone HTML for papers/presentations
   - Easy to share visualizations

4. **Cost-Effective**
   - Free & open-source
   - No additional infrastructure
   - Runs on same machine as Neo4j

5. **Flexible Deployment**
   - Streamlit Cloud (free tier available)
   - Docker container
   - Local development server

---

## 6. Comparison with Alternatives

| Feature | neo4j-viz (Streamlit) | React + D3.js | Cytoscape.js |
|---------|----------------------|---------------|--------------|
| **Development Speed** | ⭐⭐⭐⭐⭐ Fast | ⭐⭐⭐ Medium | ⭐⭐⭐ Medium |
| **Neo4j Integration** | ⭐⭐⭐⭐⭐ Native | ⭐⭐⭐ Manual | ⭐⭐⭐ Manual |
| **Customization** | ⭐⭐⭐⭐ High | ⭐⭐⭐⭐⭐ Full | ⭐⭐⭐⭐ High |
| **Python-Only** | ✅ Yes | ❌ No (JS) | ❌ No (JS) |
| **Research Use** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good | ⭐⭐⭐ Good |
| **Deployment** | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐ Medium | ⭐⭐⭐ Medium |
| **Interactive** | ⭐⭐⭐⭐ High | ⭐⭐⭐⭐⭐ Full | ⭐⭐⭐⭐⭐ Full |

**Recommendation:** Use `neo4j-viz` with Streamlit for Phase 5 ⭐

---

## 7. Example Code Snippets

### Direct Neo4j Query → Visualization

```python
from neo4j_viz.neo4j import from_neo4j

# Option 1: From driver (automatic query)
VG = from_neo4j(driver, row_limit=1000)

# Option 2: From query result
with driver.session() as session:
    result = session.run("""
        MATCH (r:Requirement)-[:ALLOCATED_TO]->(c:Component)
        RETURN r, c
        LIMIT 50
    """)
    VG = from_neo4j(result)

# Customize
VG.color_nodes(property="type")
VG.resize_nodes(property="size", normalize=True)

# Render
html = VG.render(height="600px", initial_zoom=0.5)
```

### Hierarchical Layout for Traceability

```python
from neo4j_viz import Layout, HierarchicalLayoutOptions, Direction

# Vertical traceability view
VG.set_layout(
    Layout.HIERARCHICAL,
    options=HierarchicalLayoutOptions(
        direction=Direction.DOWN,
        node_spacing=100,
        level_separation=150
    )
)

html = VG.render()
```

### Custom Node Styling

```python
for node in VG.nodes:
    labels = node.properties.get("labels", [])

    if "Requirement" in labels:
        node.color = "#FF6B6B"
        node.size = 20
        node.caption = node.properties.get("id", "")
        node.tooltip = node.properties.get("statement", "")
    elif "Component" in labels:
        node.color = "#4ECDC4"
        node.size = 15
        node.caption = node.properties.get("name", "")
```

---

## 8. Next Steps

### Immediate (Today):
1. ✅ Install neo4j-viz
2. ✅ Create basic Streamlit app
3. ✅ Test simple graph visualization

### This Week:
1. ✅ Implement Search page
2. ✅ Implement Requirement Detail page
3. ✅ Implement Graph Explorer page
4. ✅ Implement Impact Analysis page

### Next Week:
1. ✅ GraphRAG Chat interface
2. ✅ Polish UI/UX
3. ✅ Add export features
4. ✅ Documentation & deployment

---

## 9. Decision: Use neo4j-viz + Streamlit ✅

**Reasons:**
1. **Perfect alignment** with project needs (Neo4j + Python + Graph viz)
2. **Faster development** than React + D3.js
3. **Research-friendly** (Jupyter support, HTML export)
4. **Official Neo4j tool** (well-maintained, documented)
5. **Streamlit ecosystem** (widgets, deployment, community)

**Start Implementation:** Now! 🚀
