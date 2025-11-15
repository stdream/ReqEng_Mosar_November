/**
 * Requirements API Service
 */

import { apiClient } from '../lib/api-client';
import type { RequirementDetail, RequirementWithGraph, SearchResponse } from '../types';

export const requirementsService = {
  /**
   * Get requirement by ID with graph data
   */
  async getRequirement(reqId: string, depth: number = 2): Promise<RequirementWithGraph> {
    const response = await apiClient.get(`/api/requirements/${reqId}`, {
      params: { depth },
    });
    return response.data;
  },

  /**
   * List all requirements
   */
  async listRequirements(type?: string, limit: number = 100): Promise<RequirementDetail[]> {
    const response = await apiClient.get('/api/requirements/', {
      params: { type, limit },
    });
    return response.data;
  },

  /**
   * Search requirements
   */
  async search(query: string, type?: string, limit: number = 20): Promise<SearchResponse> {
    const response = await apiClient.get('/api/search/', {
      params: { q: query, type, limit },
    });
    return response.data;
  },

  /**
   * Get search suggestions (autocomplete)
   */
  async suggest(query: string, limit: number = 10): Promise<any[]> {
    const response = await apiClient.get('/api/search/suggest', {
      params: { q: query, limit },
    });
    return response.data;
  },
};
