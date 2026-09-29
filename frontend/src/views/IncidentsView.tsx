import React, { useState, useEffect } from 'react';
import { getIncidents } from '../lib/api';
import { Incident } from '../lib/types';
import { 
  Search, 
  ArrowRight, 
  RefreshCw 
} from 'lucide-react';

interface IncidentsViewProps {
  onNavigate: (view: string, id?: string) => void;
}

export const IncidentsView: React.FC<IncidentsViewProps> = ({ onNavigate }) => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedStatus, setSelectedStatus] = useState<string>('ALL');
  const [selectedDriver, setSelectedDriver] = useState<string>('ALL');
  const [minConfidence, setMinConfidence] = useState<number>(0);

  useEffect(() => {
    loadIncidents();
  }, [selectedStatus, selectedDriver, minConfidence, searchQuery]);

  const loadIncidents = () => {
    getIncidents({
      status: selectedStatus,
      driver: selectedDriver !== 'ALL' ? selectedDriver : undefined,
      minConfidence,
      search: searchQuery,
    }).then(setIncidents);
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Page Header */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 md:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[10px] font-mono tracking-[0.2em] text-red-600 uppercase font-bold mb-1">
            STEWARD OPERATIONS • SESSION EVIDENCE
          </div>
          <h1 className="text-2xl sm:text-3xl font-light tracking-tight text-white font-tech uppercase">
            INCIDENT EXPLORER
          </h1>
          <p className="text-xs font-sans text-white/50 mt-1 max-w-2xl">
            Objective algorithmic review of detected vehicle interactions and telemetry anomalies.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="px-3 py-1.5 bg-white/5 border border-white/10 rounded-sm text-xs font-mono text-white/70">
            <span>Showing <strong className="text-white">{incidents.length}</strong> Incidents</span>
          </div>
          <button
            onClick={loadIncidents}
            className="p-2 rounded-sm bg-white/5 hover:bg-white/10 border border-white/10 text-white/60 hover:text-white transition-colors cursor-pointer"
            title="Refresh Ingest Stream"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Filter Controls & Search */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-5 space-y-4">
        <div className="flex flex-col md:flex-row items-center gap-3">
          {/* Search Field */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 text-white/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search driver (VER, HAM), incident ID (INC-024), turn, lap..."
              className="w-full bg-[#0a0a0b] border border-white/10 focus:border-red-600 rounded-sm pl-10 pr-3 py-2 text-xs text-white placeholder:text-white/30 outline-none font-mono transition-colors"
            />
          </div>

          {/* Quick Clear Filter */}
          {(searchQuery || selectedStatus !== 'ALL' || selectedDriver !== 'ALL' || minConfidence > 0) && (
            <button
              onClick={() => {
                setSearchQuery('');
                setSelectedStatus('ALL');
                setSelectedDriver('ALL');
                setMinConfidence(0);
              }}
              className="text-xs font-mono text-white/60 hover:text-white px-3 py-2 rounded-sm bg-white/5 border border-white/10 shrink-0 cursor-pointer"
            >
              Reset Filters
            </button>
          )}
        </div>

        {/* Multi-Filter Selects */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono">
          {/* Status Filter */}
          <div>
            <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">
              Status
            </label>
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="w-full bg-[#0a0a0b] border border-white/10 rounded-sm px-2.5 py-1.5 text-white outline-none cursor-pointer focus:border-red-600"
            >
              <option value="ALL">All Statuses</option>
              <option value="REQUIRES_REVIEW">Requires Review</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="REVIEWED">Reviewed</option>
              <option value="DISMISSED">Dismissed</option>
              <option value="DETECTED">Detected</option>
            </select>
          </div>

          {/* Driver Filter */}
          <div>
            <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">
              Driver
            </label>
            <select
              value={selectedDriver}
              onChange={(e) => setSelectedDriver(e.target.value)}
              className="w-full bg-[#0a0a0b] border border-white/10 rounded-sm px-2.5 py-1.5 text-white outline-none cursor-pointer focus:border-red-600"
            >
              <option value="ALL">All Drivers</option>
              <option value="VER">VER #1 (Verstappen)</option>
              <option value="HAM">HAM #44 (Hamilton)</option>
              <option value="NOR">NOR #4 (Norris)</option>
              <option value="PIA">PIA #81 (Piastri)</option>
              <option value="LEC">LEC #16 (Leclerc)</option>
              <option value="SAI">SAI #55 (Sainz)</option>
              <option value="RUS">RUS #63 (Russell)</option>
              <option value="PER">PER #11 (Perez)</option>
              <option value="RIC">RIC #3 (Ricciardo)</option>
              <option value="HUL">HUL #27 (Hulkenberg)</option>
              <option value="TSU">TSU #22 (Tsunoda)</option>
              <option value="MAG">MAG #20 (Magnussen)</option>
              <option value="GAS">GAS #10 (Gasly)</option>
            </select>
          </div>

          {/* Confidence Slider */}
          <div>
            <div className="flex items-center justify-between text-[10px] text-white/40 uppercase tracking-wider mb-1">
              <span>Min Confidence</span>
              <span className="text-white font-mono font-bold">{minConfidence}%</span>
            </div>
            <input
              type="range"
              min="0"
              max="95"
              step="5"
              value={minConfidence}
              onChange={(e) => setMinConfidence(Number(e.target.value))}
              className="w-full h-1.5 bg-white/10 rounded-sm appearance-none cursor-pointer accent-red-600 mt-2"
            />
          </div>
        </div>
      </div>

      {/* Main Incidents Table (Section 2 Exact Specification) */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-[#0a0a0b] border-b border-white/10 text-[10px] text-white/40 uppercase tracking-wider">
              <tr>
                <th className="p-4 pl-5">INCIDENT ID</th>
                <th className="p-4">TIME</th>
                <th className="p-4">LAP</th>
                <th className="p-4">DRIVER A</th>
                <th className="p-4">DRIVER B</th>
                <th className="p-4">INCIDENT TYPE</th>
                <th className="p-4">CONFIDENCE</th>
                <th className="p-4">STATUS</th>
                <th className="p-4 pr-5 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {incidents.map((inc) => (
                <tr
                  key={inc.id}
                  onClick={() => onNavigate(`incident-${inc.id}`, inc.id)}
                  className="hover:bg-white/5 cursor-pointer transition-colors group"
                >
                  <td className="p-4 pl-5">
                    <span className="font-bold text-white bg-white/5 group-hover:bg-red-600/20 px-2 py-0.5 rounded-sm transition-colors group-hover:text-red-500 border border-white/10">
                      {inc.id}
                    </span>
                  </td>
                  <td className="p-4 text-white/70 font-mono">
                    {inc.timestamp}
                  </td>
                  <td className="p-4 text-white font-semibold font-mono">
                    Lap {inc.lap}
                  </td>
                  <td className="p-4">
                    <span className="font-mono text-white font-bold bg-white/5 px-2 py-0.5 rounded-sm border border-white/10">
                      {inc.driverA}
                    </span>
                  </td>
                  <td className="p-4">
                    <span className="font-mono text-white font-bold bg-white/5 px-2 py-0.5 rounded-sm border border-white/10">
                      {inc.driverB}
                    </span>
                  </td>
                  <td className="p-4">
                    <div className="text-white font-medium">
                      {inc.incidentType}
                    </div>
                    <div className="text-[10px] text-white/40">
                      {inc.turn}
                    </div>
                  </td>
                  <td className="p-4">
                    <div className="flex items-center gap-2">
                      <div className="w-12 bg-white/10 h-1.5 rounded-sm overflow-hidden">
                        <div 
                          className="h-full bg-red-600"
                          style={{ width: `${inc.confidence}%` }}
                        />
                      </div>
                      <span className={`font-bold font-mono ${inc.confidence >= 85 ? 'text-red-500' : 'text-yellow-500'}`}>
                        {inc.confidence}%
                      </span>
                    </div>
                  </td>
                  <td className="p-4">
                    <span
                      className={`text-[9px] px-2 py-0.5 rounded-sm uppercase font-bold border ${
                        inc.status === 'REQUIRES_REVIEW'
                          ? 'bg-red-600/10 text-red-500 border-red-600/30'
                          : inc.status === 'UNDER_REVIEW'
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : inc.status === 'DISMISSED'
                          ? 'bg-white/5 text-white/50 border-white/20'
                          : 'bg-emerald-500/10 text-emerald-500 border-emerald-500/30'
                      }`}
                    >
                      {inc.status.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="p-4 pr-5 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onNavigate(`incident-${inc.id}`, inc.id);
                      }}
                      className="px-3 py-1 bg-white/5 hover:bg-red-600 hover:text-white border border-white/10 text-white/80 text-[10px] font-mono font-bold uppercase rounded-sm transition-colors cursor-pointer"
                    >
                      VIEW
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {incidents.length === 0 && (
          <div className="p-12 text-center text-white/40 font-mono text-xs">
            No incident records match the current filter criteria.
          </div>
        )}

        <div className="p-3.5 bg-[#0a0a0b] border-t border-white/10 flex items-center justify-between text-[10px] font-mono text-white/40">
          <span>Confidence metrics denote algorithmic correlation, not certainty of sporting infringement.</span>
          <span>FastF1 25Hz Ingest Engine</span>
        </div>
      </div>
    </div>
  );
};
