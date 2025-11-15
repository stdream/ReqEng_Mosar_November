// ============================================================
// MOSAR Requirements Management System - Neo4j Schema
// ============================================================
// This file defines the complete graph schema for MOSAR RM system
// including constraints, indexes, and vector indexes

// ============================================================
// 1. CONSTRAINTS (Uniqueness)
// ============================================================

// Lexical Layer
CREATE CONSTRAINT document_id IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE;
CREATE CONSTRAINT section_id IF NOT EXISTS FOR (s:Section) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (c:Chunk) REQUIRE c.id IS UNIQUE;

// Domain Layer - Requirements
CREATE CONSTRAINT requirement_id IF NOT EXISTS FOR (r:Requirement) REQUIRE r.id IS UNIQUE;

// Domain Layer - Scenarios and Components
CREATE CONSTRAINT scenario_id IF NOT EXISTS FOR (s:Scenario) REQUIRE s.id IS UNIQUE;
CREATE CONSTRAINT component_name IF NOT EXISTS FOR (c:Component) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT subsystem_name IF NOT EXISTS FOR (s:Subsystem) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT interface_name IF NOT EXISTS FOR (i:Interface) REQUIRE i.name IS UNIQUE;
CREATE CONSTRAINT software_component_name IF NOT EXISTS FOR (sc:SoftwareComponent) REQUIRE sc.name IS UNIQUE;

// Domain Layer - Testing
CREATE CONSTRAINT testcase_id IF NOT EXISTS FOR (t:TestCase) REQUIRE t.id IS UNIQUE;

// Domain Layer - Partners (optional)
CREATE CONSTRAINT partner_name IF NOT EXISTS FOR (p:Partner) REQUIRE p.name IS UNIQUE;

// ============================================================
// 2. VECTOR INDEXES (for embeddings)
// ============================================================

// Vector index for Chunk embeddings
// Dimension: 3072 for OpenAI text-embedding-3-large
// Dimension: 1536 for OpenAI text-embedding-ada-002
DROP INDEX chunk_embeddings IF EXISTS;
CREATE VECTOR INDEX chunk_embeddings IF NOT EXISTS
FOR (c:Chunk) ON c.embedding
OPTIONS {indexConfig: {
  `vector.dimensions`: 1536,
  `vector.similarity_function`: 'cosine'
}};

// ============================================================
// 3. FULLTEXT INDEXES (for hybrid search)
// ============================================================

// Fulltext index for Chunk text
DROP INDEX chunk_fulltext IF EXISTS;
CREATE FULLTEXT INDEX chunk_fulltext IF NOT EXISTS
FOR (c:Chunk) ON EACH [c.text];

// Fulltext index for Requirement statements
DROP INDEX requirement_fulltext IF EXISTS;
CREATE FULLTEXT INDEX requirement_fulltext IF NOT EXISTS
FOR (r:Requirement) ON EACH [r.statement, r.title, r.display_id];

// Fulltext index for Document sections
DROP INDEX section_fulltext IF EXISTS;
CREATE FULLTEXT INDEX section_fulltext IF NOT EXISTS
FOR (s:Section) ON EACH [s.title, s.number];

// ============================================================
// 4. PROPERTY INDEXES (for faster lookups)
// ============================================================

// Requirement indexes
CREATE INDEX req_series IF NOT EXISTS FOR (r:Requirement) ON (r.series);
CREATE INDEX req_type IF NOT EXISTS FOR (r:Requirement) ON (r.type);
CREATE INDEX req_domain IF NOT EXISTS FOR (r:Requirement) ON (r.domain);
CREATE INDEX req_level IF NOT EXISTS FOR (r:Requirement) ON (r.level);

// Document indexes
CREATE INDEX doc_type IF NOT EXISTS FOR (d:Document) ON (d.doc_type);

// Section indexes
CREATE INDEX section_number IF NOT EXISTS FOR (s:Section) ON (s.number);

// TestCase indexes
CREATE INDEX test_phase IF NOT EXISTS FOR (t:TestCase) ON (t.phase);

// Component indexes
CREATE INDEX component_kind IF NOT EXISTS FOR (c:Component) ON (c.kind);

// ============================================================
// 5. SCHEMA INFORMATION
// ============================================================

// Node Labels and their properties:
//
// LEXICAL LAYER:
// (:Document {id, title, doc_type, version, date})
// (:Section {id, number, title, level, page_start, page_end})
// (:Chunk {id, text, embedding, order_in_section})
//
// DOMAIN LAYER:
// (:Requirement {id, display_id, series, type, domain, level, statement,
//                title, verification, responsible, comment, pageno, covers})
// (:Scenario {id, name, description})
// (:Component {name, kind, role})
// (:Subsystem {name, description})
// (:Interface {name, description})
// (:SoftwareComponent {name, description})
// (:TestCase {id, name, phase, description})
// (:Partner {name, organization})
//
// RELATIONSHIPS:
//
// LEXICAL LAYER:
// (Document)-[:HAS_SECTION]->(Section)
// (Section)-[:HAS_SUBSECTION]->(Section)
// (Section)-[:HAS_CHUNK]->(Chunk)
// (Chunk)-[:NEXT_CHUNK]->(Chunk)
//
// DOMAIN LAYER - Requirements:
// (Requirement)-[:REFINES]->(Requirement)
// (Requirement)-[:COVERS]->(Requirement)
// (Requirement)-[:ALLOCATED_TO]->(Component|Subsystem)
// (Requirement)-[:REALIZED_BY]->(SoftwareComponent|Component)
// (Requirement)-[:VERIFIED_BY]->(TestCase)
//
// DOMAIN LAYER - Testing:
// (Component|Subsystem)-[:TESTED_IN]->(TestCase)
// (Scenario)-[:DEMONSTRATED_BY]->(TestCase)
//
// DOMAIN LAYER - Documentation:
// (Scenario|Component|SoftwareComponent)-[:DESCRIBED_IN]->(Section)
//
// DOMAIN LAYER - Responsibility:
// (Requirement|Component|TestCase)-[:RESPONSIBLE]->(Partner)
//
// LINK LAYER (Lexical ↔ Domain):
// (Chunk)-[:MENTIONS_REQUIREMENT]->(Requirement)
// (Chunk)-[:MENTIONS_COMPONENT]->(Component)
// (Chunk)-[:MENTIONS_SCENARIO]->(Scenario)
// (Chunk)-[:DESCRIBES_TEST]->(TestCase)
