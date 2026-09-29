import React, { useState, useEffect } from 'react';
import { getRaces } from '../lib/api';
import { Race } from '../lib/types';
import { Search, MapPin, ArrowRight, Calendar, Flag } from 'lucide-react';

interface RacesViewProps {
  onNavigate: (view: string, raceId?: string) => void;
}

export const RacesView: React.FC<RacesViewProps> = ({ onNavigate }) => {
  const [races, setRaces] = useState<Race[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSeason, setSelectedSeason] = useState<string>('2024');

  useEffect(() => {
    getRaces().then(setRaces);
  }, []);

  const filteredRaces = races.filter((r) => {
    const matchesSearch =
      r.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.circuit.toLowerCase().includes(searchQuery.toLowerCase()) ||
      r.country.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesSeason = selectedSeason === 'ALL' || r.season.toString() === selectedSeason;
    return matchesSearch && matchesSeason;
  });

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 md:p-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="text-[10px] font-mono tracking-[0.2em] text-red-600 uppercase font-bold mb-1">
            DATA INGEST & TELEMETRY ARCHIVE
          </div>
          <h1 className="text-2xl sm:text-3xl font-light tracking-tight text-white font-tech uppercase">
            RACES & SESSIONS
          </h1>
          <p className="text-xs font-sans text-white/50 mt-1 max-w-xl">
            Select Formula 1 Grand Prix sessions to explore incident reconstructions and telemetry evidence.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-white/40">Season:</span>
          <select
            value={selectedSeason}
            onChange={(e) => setSelectedSeason(e.target.value)}
            className="bg-[#0a0a0b] border border-white/10 rounded-sm px-3 py-1.5 text-xs font-mono text-white outline-none focus:border-red-600 cursor-pointer"
          >
            <option value="2024">2024</option>
            <option value="2023">2023</option>
            <option value="ALL">All Seasons</option>
          </select>
        </div>
      </div>

      {/* Search Input */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-4">
        <div className="relative">
          <Search className="w-4 h-4 text-white/40 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Grand Prix (Monza, Silverstone, Spa), circuit, country..."
            className="w-full bg-[#0a0a0b] border border-white/10 focus:border-red-600 rounded-sm pl-10 pr-3 py-2 text-xs text-white placeholder:text-white/30 outline-none font-mono transition-colors"
          />
        </div>
      </div>

      {/* Races Table / Cards (Section 9 Exact Specification) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredRaces.map((race) => (
          <div
            key={race.id}
            className="bg-[#0d0d0f] border border-white/10 rounded-sm overflow-hidden flex flex-col justify-between"
          >
            {/* Race & Circuit */}
            <div className="p-6 border-b border-white/10 bg-[#0a0a0b]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-[10px] font-mono tracking-widest text-white/40 uppercase font-semibold">
                  SEASON {race.season} • ROUND {race.round ?? 1}
                </span>
                <span
                  className={`text-[9px] font-mono px-2 py-0.5 rounded-sm font-bold uppercase border ${
                    race.status === 'ANALYSIS_READY' || race.status === 'ANALYSIS READY'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                      : 'bg-white/5 text-white/50 border-white/10'
                  }`}
                >
                  {race.status.replace('_', ' ')}
                </span>
              </div>

              <h2 className="text-xl font-light text-white font-tech tracking-wide uppercase mb-1">
                {race.name}
              </h2>

              <div className="flex items-center gap-2 text-xs font-mono text-white/60">
                <MapPin className="w-3.5 h-3.5 text-red-600 shrink-0" />
                <span>{race.circuit}, {race.country}</span>
              </div>

              <div className="flex items-center gap-2 text-xs font-mono text-white/40 mt-2">
                <Calendar className="w-3.5 h-3.5 text-white/30 shrink-0" />
                <span>{race.date}</span>
              </div>
            </div>

            {/* Ingested Sessions */}
            <div className="p-5 space-y-2 flex-1">
              <div className="text-[10px] font-mono uppercase tracking-widest text-white/40 font-bold mb-2">
                Session Feeds
              </div>

              {(race.sessions && race.sessions.length > 0) ? (
                race.sessions.map((session, sIdx) => (
                  <div
                    key={sIdx}
                    className="p-2.5 rounded-sm bg-white/5 border border-white/5 flex items-center justify-between text-xs font-mono"
                  >
                    <div>
                      <span className="text-white font-bold uppercase">{session.name}</span>
                      <span className="text-[10px] text-white/40 ml-2">
                        {session.laps ? `${session.laps} Laps` : 'Timed'}
                      </span>
                    </div>
                    <span className="text-[9px] font-mono text-emerald-400 uppercase font-semibold">
                      {session.status.replace('_', ' ')}
                    </span>
                  </div>
                ))
              ) : (
                <div className="p-2.5 rounded-sm bg-white/5 border border-white/5 flex items-center justify-between text-xs font-mono">
                  <div>
                    <span className="text-white font-bold uppercase">{race.sessionType || 'Race'}</span>
                    <span className="text-[10px] text-white/40 ml-2">53 Laps</span>
                  </div>
                  <span className="text-[9px] font-mono text-emerald-400 uppercase font-semibold">
                    ANALYSIS READY
                  </span>
                </div>
              )}
            </div>

            {/* Action: VIEW SESSION (Section 9 Requirement) */}
            <div className="p-4 border-t border-white/10 bg-[#0a0a0b] flex items-center justify-between">
              <span className="text-[10px] font-mono text-white/40">
                FastF1 25Hz Ingest
              </span>
              <button
                onClick={() => onNavigate('dashboard')}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-sm transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <span>VIEW SESSION</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
