/**
 * Graph Data Types - Compatible with @neo4j-nvl/react
 */

export interface NodeModel {
  id: string;
  labels: string[];
  properties: Record<string, any>;
  caption?: string;
  size?: number;
  color?: string;
}

export interface RelationshipModel {
  id: string;
  type: string;
  from: string;
  to: string;
  startNode?: string;
  endNode?: string;
  properties: Record<string, any>;
  caption?: string;
  color?: string;
}

export interface GraphData {
  nodes: NodeModel[];
  relationships: RelationshipModel[];
}
