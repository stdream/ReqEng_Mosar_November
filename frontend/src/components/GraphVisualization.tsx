/**
 * GraphVisualization Component
 * Wrapper for @neo4j-nvl/react
 */

import React from 'react';
import { BasicNvlWrapper } from '@neo4j-nvl/react';
import type { GraphData } from '../types';

interface GraphVisualizationProps {
  data: GraphData;
  height?: string;
  layout?: 'forceDirected' | 'hierarchical';
}

export const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  data,
  height = '600px',
  layout = 'forceDirected',
}) => {
  const nvlOptions = {
    layout,
    initialZoom: 0.8,
    allowDynamicMinZoom: true,
    disableWebGL: false,
    instanceId: 'mosar-graph',
  };

  const nvlCallbacks = {
    onLayoutComputing: (isComputing: boolean) => {
      if (isComputing) {
        console.log('[NVL] Computing layout...');
      }
    },
    onNodeClick: (node: any) => {
      console.log('[NVL] Node clicked:', node);
    },
    onRelationshipClick: (rel: any) => {
      console.log('[NVL] Relationship clicked:', rel);
    },
  };

  return (
    <div style={{ width: '100%', height, border: '1px solid #e5e7eb', borderRadius: '8px' }}>
      {data.nodes.length > 0 ? (
        <BasicNvlWrapper
          nodes={data.nodes}
          rels={data.relationships}
          nvlOptions={nvlOptions}
          nvlCallbacks={nvlCallbacks}
        />
      ) : (
        <div className="flex items-center justify-center h-full text-gray-500">
          No graph data available
        </div>
      )}
    </div>
  );
};
