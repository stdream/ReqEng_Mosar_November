# MOSAR GraphRAG Complete Structure

## 전체 시스템 구조

```mermaid
graph TB
    subgraph LEXICAL["📄 LEXICAL LAYER - Document Structure"]
        DOC[("Document (4)<br/>SRD, PDD, DDD, DEMO")]
        SEC[("Section (527)")]
        CHUNK[("Chunk (1,659)")]

        DOC -->|HAS_SECTION<br/>527| SEC
        SEC -->|HAS_SUBSECTION<br/>301| SEC
        SEC -->|HAS_CHUNK<br/>1,659| CHUNK
        CHUNK -->|NEXT_CHUNK<br/>1,208| CHUNK
    end

    subgraph DOMAIN["🧠 DOMAIN LAYER - Knowledge Graph"]
        REQ[("Requirement (220)")]
        COMP[("Component (298)")]
        SUB[("Subsystem (51)")]
        INTF[("Interface (37)")]
        SCEN[("Scenario (23)")]
        TEST[("TestCase (21)")]

        REQ -->|COVERS<br/>53| REQ
        REQ -->|ALLOCATED_TO<br/>51| COMP
        REQ -->|VERIFIED_BY<br/>2| TEST
        REQ -->|USED_IN_SCENARIOS<br/>44| SCEN
        REQ -->|REQUIRES<br/>341| COMP
        REQ -->|REQUIRES| SUB
        REQ -->|REQUIRES| INTF

        COMP -->|CONNECTS_TO<br/>199| COMP
        COMP -->|PART_OF<br/>83| COMP
        COMP -->|USES<br/>179| INTF
        COMP -->|REQUIRES<br/>136| SUB
    end

    subgraph LINK["🔗 LINK LAYER - Connections"]
        CHUNK -->|MENTIONS_REQUIREMENT<br/>4,832| REQ
        CHUNK -->|MENTIONS<br/>5,610| ENT["Entity (429)"]

        ENT -.->|298| COMP
        ENT -.->|51| SUB
        ENT -.->|37| INTF
        ENT -.->|23| SCEN
        ENT -.->|21| TEST
    end

    style LEXICAL fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style DOMAIN fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    style LINK fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style DOC fill:#bbdefb,stroke:#1976d2,stroke-width:2px
    style CHUNK fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style REQ fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style COMP fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style ENT fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px
```

## 상세 관계도

```mermaid
graph LR
    subgraph Documents["📚 Documents & Chunks"]
        D[Document: 4]
        S[Section: 527]
        C[Chunk: 1,659]
    end

    subgraph Requirements["📋 Requirements"]
        R[Requirement: 220]
    end

    subgraph Entities["🏗️ Entities (429)"]
        direction TB
        COMP[Component: 298]
        SUB[Subsystem: 51]
        INTF[Interface: 37]
        SCEN[Scenario: 23]
        TEST[TestCase: 21]
    end

    D -->|HAS_SECTION: 527| S
    S -->|HAS_SUBSECTION: 301| S
    S -->|HAS_CHUNK: 1,659| C
    C -->|NEXT_CHUNK: 1,208| C

    C ==>|MENTIONS_REQUIREMENT<br/>4,832| R
    C ==>|MENTIONS<br/>5,610| COMP
    C ==>|MENTIONS| SUB
    C ==>|MENTIONS| INTF
    C ==>|MENTIONS| SCEN
    C ==>|MENTIONS| TEST

    R -->|COVERS: 53| R
    R -->|ALLOCATED_TO: 51| COMP
    R -->|VERIFIED_BY: 2| TEST
    R -->|USED_IN_SCENARIOS: 44| SCEN
    R -->|REQUIRES: 341| COMP

    COMP -->|CONNECTS_TO: 199| COMP
    COMP -->|PART_OF: 83| COMP
    COMP -->|USES: 179| INTF
    COMP -->|REQUIRES: 136| SUB

    style D fill:#bbdefb,stroke:#1976d2,stroke-width:2px
    style C fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style R fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style COMP fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style SUB fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px
    style INTF fill:#b3e5fc,stroke:#0288d1,stroke-width:2px
    style SCEN fill:#f8bbd0,stroke:#c2185b,stroke-width:2px
    style TEST fill:#d7ccc8,stroke:#5d4037,stroke-width:2px
```

## GraphRAG Query Flow

```mermaid
flowchart TD
    START([User Query:<br/>'HOTDOCK power requirements'])

    VECTOR[Step 1: Vector Search<br/>Find relevant Chunks]
    EXTRACT[Step 2: Entity Extraction<br/>Identify: HOTDOCK, Power]
    TRAVERSE[Step 3: Graph Traversal]
    ENRICH[Step 4: Enriched Context]
    LLM[Step 5: LLM Answer]

    START --> VECTOR
    VECTOR --> EXTRACT
    EXTRACT --> TRAVERSE

    subgraph "Graph Traversal Paths"
        T1[Chunks mentioning HOTDOCK]
        T2[HOTDOCK Component]
        T3[Requirements allocated to HOTDOCK]
        T4[Power Subsystem]
        T5[HOTDOCK REQUIRES Power]
        T6[Related Components]

        T1 -->|MENTIONS| T2
        T2 -->|ALLOCATED_TO| T3
        T2 -->|REQUIRES| T4
        T2 -->|CONNECTS_TO| T6
        T3 -->|MENTIONS_REQUIREMENT| T1
    end

    TRAVERSE --> T1 & T2 & T3 & T4 & T5 & T6
    T1 & T2 & T3 & T4 & T5 & T6 --> ENRICH
    ENRICH --> LLM

    LLM --> ANSWER([Complete Answer with:<br/>- Power specs from Requirements<br/>- HOTDOCK connections<br/>- Related components<br/>- Supporting evidence])

    style START fill:#c8e6c9,stroke:#388e3c,stroke-width:2px
    style ANSWER fill:#bbdefb,stroke:#1976d2,stroke-width:2px
    style TRAVERSE fill:#ffe0b2,stroke:#f57c00,stroke-width:2px
    style ENRICH fill:#e1bee7,stroke:#7b1fa2,stroke-width:2px
```

## Relationship 분포

```mermaid
%%{init: {'theme':'base', 'themeVariables': { 'fontSize':'16px'}}}%%
pie title "Total Relationships: 15,225"
    "MENTIONS (Chunk→Entity)" : 5610
    "MENTIONS_REQUIREMENT (Chunk→Req)" : 4832
    "HAS_CHUNK" : 1659
    "NEXT_CHUNK" : 1208
    "HAS_SECTION" : 527
    "REQUIRES (Req→Entity)" : 477
    "HAS_SUBSECTION" : 301
    "CONNECTS_TO (Comp→Comp)" : 199
    "USES (Comp→Interface)" : 179
    "PART_OF (Comp→Comp)" : 83
    "COVERS (Req→Req)" : 53
    "ALLOCATED_TO (Req→Comp)" : 51
    "USED_IN_SCENARIOS (Req→Scenario)" : 44
    "VERIFIED_BY (Req→Test)" : 2
```

## Entity 분포

```mermaid
%%{init: {'theme':'base'}}%%
pie title "Entities by Category (Total: 429)"
    "Component" : 298
    "Subsystem" : 51
    "Interface" : 37
    "Scenario" : 23
    "TestCase" : 21
```

## 3-Layer Architecture

```mermaid
graph TB
    subgraph Layer1["Layer 1: LEXICAL (3,695 rels)"]
        L1A[Document Structure]
        L1B[Section Hierarchy]
        L1C[Chunk Sequencing]
    end

    subgraph Layer2["Layer 2: LINK (10,442 rels)"]
        L2A[Chunk → Requirement<br/>4,832 MENTIONS_REQUIREMENT]
        L2B[Chunk → Entity<br/>5,610 MENTIONS]
    end

    subgraph Layer3["Layer 3: DOMAIN (1,088 rels)"]
        L3A[Requirement Traceability<br/>53 COVERS]
        L3B[Requirement → Entity<br/>508 relationships]
        L3C[Component Connections<br/>199 CONNECTS_TO]
        L3D[Component Hierarchy<br/>83 PART_OF]
        L3E[Component → Interface<br/>179 USES]
        L3F[Dependencies<br/>136 REQUIRES]
    end

    Layer1 -.->|Connects via| Layer2
    Layer2 -.->|Enables| Layer3

    style Layer1 fill:#e3f2fd,stroke:#1976d2,stroke-width:2px
    style Layer2 fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    style Layer3 fill:#fff3e0,stroke:#f57c00,stroke-width:2px
```

---

## 통계 요약

### Nodes
- **Documents**: 4
- **Sections**: ~527
- **Chunks**: 1,659
- **Requirements**: 220
- **Entities**: 429
  - Components: 298
  - Subsystems: 51
  - Interfaces: 37
  - Scenarios: 23
  - TestCases: 21

**총 Nodes**: ~2,839개

### Relationships
- **Lexical Layer**: 3,695 (문서 구조)
- **Link Layer**: 10,442 (Chunk 연결)
- **Domain Layer**: 1,088 (지식 그래프)

**총 Relationships**: **15,225개**

---

## 사용 방법

이 Mermaid 다이어그램들은 다음 도구들에서 볼 수 있습니다:

1. **GitHub**: 이 파일을 GitHub에 업로드하면 자동으로 렌더링됩니다
2. **VSCode**: Mermaid Preview 확장 설치 후 미리보기
3. **온라인**: https://mermaid.live 에서 코드 복사-붙여넣기
4. **Obsidian**: Mermaid 플러그인 활성화
