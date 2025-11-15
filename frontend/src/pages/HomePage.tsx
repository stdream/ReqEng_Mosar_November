/**
 * Home Page
 * Landing page with search and quick stats
 */

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const quickLinks = [
    { id: 'S111', label: 'FuncR_S111 - HOTDOCK Functionality' },
    { id: 'S112', label: 'FuncR_S112 - Network Reconfiguration' },
    { id: 'S211', label: 'FuncR_S211 - Power Distribution' },
    { id: 'S311', label: 'FuncR_S311 - Thermal Management' },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            MOSAR GraphRAG
          </h1>
          <p className="text-xl text-gray-600">
            Requirements Management & Traceability System
          </p>
        </div>

        {/* Search */}
        <form onSubmit={handleSearch} className="max-w-2xl mx-auto mb-12">
          <div className="flex gap-2">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search requirements (e.g., S111, FuncR_*, power distribution...)"
              className="flex-1 px-6 py-4 text-lg border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <button
              type="submit"
              className="px-8 py-4 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition"
            >
              Search
            </button>
          </div>
        </form>

        {/* Quick Stats */}
        <div className="max-w-4xl mx-auto grid grid-cols-4 gap-6 mb-12">
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">220</div>
            <div className="text-gray-600">Requirements</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <div className="text-4xl font-bold text-green-600 mb-2">298</div>
            <div className="text-gray-600">Components</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <div className="text-4xl font-bold text-purple-600 mb-2">21</div>
            <div className="text-gray-600">Test Cases</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <div className="text-4xl font-bold text-orange-600 mb-2">23</div>
            <div className="text-gray-600">Scenarios</div>
          </div>
        </div>

        {/* Quick Links */}
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-semibold mb-4 text-gray-800">Quick Access</h2>
          <div className="bg-white rounded-lg shadow-md divide-y">
            {quickLinks.map((link) => (
              <button
                key={link.id}
                onClick={() => navigate(`/requirement/${link.id}`)}
                className="w-full px-6 py-4 text-left hover:bg-gray-50 transition flex items-center justify-between"
              >
                <span className="text-gray-700">{link.label}</span>
                <svg
                  className="w-5 h-5 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            ))}
          </div>
        </div>

        {/* Features */}
        <div className="max-w-4xl mx-auto mt-16 grid grid-cols-3 gap-8">
          <div className="text-center">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-800 mb-2">Smart Search</h3>
            <p className="text-sm text-gray-600">Pattern matching and full-text search across requirements</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-800 mb-2">Graph Visualization</h3>
            <p className="text-sm text-gray-600">Interactive Neo4j graph explorer with @neo4j-nvl/react</p>
          </div>
          <div className="text-center">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="font-semibold text-gray-800 mb-2">Impact Analysis</h3>
            <p className="text-sm text-gray-600">Analyze requirement changes and traceability paths</p>
          </div>
        </div>
      </div>
    </div>
  );
};
