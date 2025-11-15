/**
 * Graph API Service
 */

import { apiClient } from '../lib/api-client';
import type { GraphData } from '../types';

export const graphService = {
  /**
   * Get requirement graph
   */
  async getRequirementGraph(reqId: string, depth: number = 2): Promise<GraphData> {
    const response = await apiClient.get(`/api/graph/requirement/${reqId}`, {
      params: { depth },
    });
    return response.data;
  },

  /**
   * Get impact analysis graph
   */
  async getImpactGraph(
    reqId: string,
    depth: number = 3,
    options?: {
      components?: boolean;
      tests?: boolean;
      requirements?: boolean;
      scenarios?: boolean;
    }
  ): Promise<GraphData> {
    const response = await apiClient.get(`/api/graph/impact/${reqId}`, {
      params: {
        depth,
        components: options?.components ?? true,
        tests: options?.tests ?? true,
        requirements: options?.requirements ?? true,
        scenarios: options?.scenarios ?? true,
      },
    });
    return response.data;
  },
};
