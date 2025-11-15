/**
 * Requirement Types
 */

import type { GraphData } from './graph';

export interface RequirementDetail {
  id: string;
  display_id: string;
  type: string;
  level: string;
  statement: string;
  verification?: string;
  responsible?: string;
}

export interface RequirementStatistics {
  components: number;
  tests: number;
  scenarios: number;
  related_requirements: number;
}

export interface RequirementWithGraph {
  requirement: RequirementDetail;
  graph: GraphData;
  statistics: RequirementStatistics;
}

export interface SearchResult {
  id: string;
  type: string;
  title: string;
  description: string;
  properties: Record<string, any>;
  relevance_score: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
}
