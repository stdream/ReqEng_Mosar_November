/**
 * Requirement Detail Page
 * Shows requirement details with graph visualization
 */

import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { GraphVisualization } from '../components/GraphVisualization';
import { requirementsService } from '../services/requirements-service';
import type { RequirementWithGraph } from '../types';

export const RequirementDetailPage: React.FC = () => {
  const { reqId } = useParams<{ reqId: string }>();
  const [data, setData] = useState<RequirementWithGraph | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [depth, setDepth] = useState(2);

  useEffect(() => {
    if (!reqId) return;

    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await requirementsService.getRequirement(reqId, depth);
        setData(result);
      } catch (err: any) {
        setError(err.response?.data?.detail || err.message || 'Failed to fetch requirement');
        console.error('Error fetching requirement:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [reqId, depth]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-gray-600">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl text-gray-600">Requirement not found</div>
      </div>
    );
  }

  const { requirement, graph, statistics } = data;

  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">{requirement.display_id}</h1>
        <div className="flex gap-4 text-sm text-gray-600">
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full">{requirement.type}</span>
          <span className="px-3 py-1 bg-green-100 text-green-800 rounded-full">{requirement.level}</span>
          {requirement.responsible && (
            <span className="px-3 py-1 bg-purple-100 text-purple-800 rounded-full">
              {requirement.responsible}
            </span>
          )}
        </div>
      </div>

      {/* Statement */}
      <div className="mb-6 p-4 bg-gray-50 rounded-lg">
        <h2 className="text-lg font-semibold mb-2">Statement</h2>
        <p className="text-gray-700">{requirement.statement}</p>
      </div>

      {/* Verification */}
      {requirement.verification && (
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h2 className="text-lg font-semibold mb-2">Verification</h2>
          <p className="text-gray-700">{requirement.verification}</p>
        </div>
      )}

      {/* Statistics */}
      <div className="mb-6 grid grid-cols-4 gap-4">
        <div className="p-4 bg-white border rounded-lg">
          <div className="text-2xl font-bold text-blue-600">{statistics.components}</div>
          <div className="text-sm text-gray-600">Components</div>
        </div>
        <div className="p-4 bg-white border rounded-lg">
          <div className="text-2xl font-bold text-green-600">{statistics.tests}</div>
          <div className="text-sm text-gray-600">Tests</div>
        </div>
        <div className="p-4 bg-white border rounded-lg">
          <div className="text-2xl font-bold text-purple-600">{statistics.scenarios}</div>
          <div className="text-sm text-gray-600">Scenarios</div>
        </div>
        <div className="p-4 bg-white border rounded-lg">
          <div className="text-2xl font-bold text-orange-600">{statistics.related_requirements}</div>
          <div className="text-sm text-gray-600">Related Reqs</div>
        </div>
      </div>

      {/* Graph Controls */}
      <div className="mb-4 flex items-center gap-4">
        <label className="text-sm font-medium">Graph Depth:</label>
        <select
          value={depth}
          onChange={(e) => setDepth(Number(e.target.value))}
          className="px-3 py-2 border rounded-md"
        >
          <option value={1}>1 hop</option>
          <option value={2}>2 hops</option>
          <option value={3}>3 hops</option>
          <option value={4}>4 hops</option>
        </select>
        <div className="text-sm text-gray-600">
          {graph.nodes.length} nodes, {graph.relationships.length} relationships
        </div>
      </div>

      {/* Graph Visualization */}
      <GraphVisualization data={graph} height="700px" />
    </div>
  );
};
