import React, { useState, useEffect, useRef } from 'react';
import { Search, X, AlertTriangle, Users, Flag, BookOpen, ArrowRight } from 'lucide-react';
import { getIncidents, getDrivers, getRaces, getRegulations } from '../lib/api';
import { Incident, Driver, Race, RelevantRegulation } from '../lib/types';

interface GlobalSearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onNavigate: (view: string, id?: string) => void;
}

export const GlobalSearchModal: React.FC<GlobalSearchModalProps> = ({
  isOpen,
  onClose,
  onNavigate,
}) => {
  const [query, setQuery] = useState('');
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [races, setRaces] = useState<Race[]>([]);
  const [regulations, setRegulations] = useState<RelevantRegulation[]>([]);
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
      getIncidents().then(setIncidents);
      getDrivers().then(setDrivers);
      getRaces().then(setRaces);
      getRegulations().then(setRegulations);
    } else {
      setQuery('');
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        if (isOpen) onClose();
        else onNavigate('search-modal-trigger');
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, onNavigate]);

  if (!isOpen) return null;

  const q = query.toLowerCase().trim();

  const matchingIncidents = q
    ? incidents.filter(
        (inc) =>
          inc.id.toLowerCase().includes(q) ||
          inc.driverA.toLowerCase().includes(q) ||
          inc.driverB.toLowerCase().includes(q) ||
          inc.incidentType.toLowerCase().includes(q) ||
          inc.turn.toLowerCase().includes(q) ||
          `${inc.driverA} ${inc.driverB}`.toLowerCase().includes(q) ||
          `lap ${inc.lap}`.includes(q)
      )
    : incidents.slice(0, 3);

  const matchingDrivers = q
    ? drivers.filter(
        (d) =>
          d.code.toLowerCase().includes(q) ||
          d.name.toLowerCase().includes(q) ||
          d.team.toLowerCase().includes(q)
      )
    : [];

  const matchingRegulations = q
    ? regulations.filter(
        (r) =>
          r.article.toLowerCase().includes(q) ||
          r.title.toLowerCase().includes(q) ||
          (r.whyRelevant && r.whyRelevant.toLowerCase().includes(q))
      )
    : regulations.slice(0, 2);

  const matchingRaces = q
    ? races.filter(
        (r) =>
          r.name.toLowerCase().includes(q) ||
          r.circuit.toLowerCase().includes(q) ||
          r.country.toLowerCase().includes(q)
      )
    : [];

  return (
    <div 
      className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-start justify-center pt-20 p-4"
      onClick={onClose}
    >
      <div 
        className="bg-[#0b0e14] border border-[#233144] rounded-xl max-w-2xl w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Search Bar Input */}
        <div className="p-4 border-b border-[#1b2535] flex items-center gap-3 bg-[#0d121b]">
          <Search className="w-5 h-5 text-zinc-400" />
          <input
            ref={inputRef}
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search drivers (VER, HAM), incident ID (#024), turn, regulations (Article 33.4)..."
            className="flex-1 bg-transparent text-sm text-white placeholder:text-zinc-500 outline-none font-mono"
          />
          {query && (
            <button 
              onClick={() => setQuery('')}
              className="text-zinc-400 hover:text-white"
            >
              <X className="w-4 h-4" />
            </button>
          )}
          <kbd className="hidden sm:inline text-[10px] font-mono bg-zinc-800 text-zinc-400 px-1.5 py-0.5 rounded border border-zinc-700">
            ESC
          </kbd>
        </div>

        {/* Search Results */}
        <div className="max-h-[60vh] overflow-y-auto p-3 space-y-4 divide-y divide-[#17212e]">
          {/* Incidents Section */}
          {matchingIncidents.length > 0 && (
            <div className="pt-2 first:pt-0">
              <div className="text-[10px] font-mono uppercase text-zinc-400 px-2 mb-2 flex items-center gap-1.5 font-semibold">
                <AlertTriangle className="w-3.5 h-3.5 text-[#ff1801]" />
                <span>INCIDENTS ({matchingIncidents.length})</span>
              </div>
              <div className="space-y-1">
                {matchingIncidents.map((inc) => (
                  <div
                    key={inc.id}
                    onClick={() => {
                      onNavigate(`incident-${inc.id}`, inc.id);
                      onClose();
                    }}
                    className="p-2.5 rounded hover:bg-[#121924] cursor-pointer flex items-center justify-between transition-colors group"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-mono text-xs font-bold text-white bg-[#1a2537] px-2 py-0.5 rounded">
                        {inc.id}
                      </span>
                      <div>
                        <div className="text-xs font-semibold text-zinc-200 group-hover:text-white">
                          Lap {inc.lap} • {inc.turn}: <span className="text-[#ff1801] font-mono">{inc.driverA} → {inc.driverB}</span>
                        </div>
                        <div className="text-[10px] text-zinc-400 font-mono">
                          {inc.incidentType} • {inc.confidence}% Conf.
                        </div>
                      </div>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-zinc-500 group-hover:text-white group-hover:translate-x-0.5 transition-all" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Regulations Section */}
          {matchingRegulations.length > 0 && (
            <div className="pt-3">
              <div className="text-[10px] font-mono uppercase text-zinc-400 px-2 mb-2 flex items-center gap-1.5 font-semibold">
                <BookOpen className="w-3.5 h-3.5 text-cyan-400" />
                <span>REGULATIONS ({matchingRegulations.length})</span>
              </div>
              <div className="space-y-1">
                {matchingRegulations.map((reg) => (
                  <div
                    key={reg.id}
                    onClick={() => {
                      onNavigate('regulations', reg.id);
                      onClose();
                    }}
                    className="p-2.5 rounded hover:bg-[#121924] cursor-pointer flex items-center justify-between transition-colors group"
                  >
                    <div>
                      <div className="text-xs font-bold font-mono text-cyan-400">
                        {reg.article} — {reg.title}
                      </div>
                      <div className="text-[10px] text-zinc-400 font-mono line-clamp-1">
                        {reg.whyRelevant}
                      </div>
                    </div>
                    <span className="text-[9px] font-mono bg-zinc-800 text-zinc-300 px-1.5 py-0.5 rounded">
                      {reg.relevance}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Drivers Section */}
          {matchingDrivers.length > 0 && (
            <div className="pt-3">
              <div className="text-[10px] font-mono uppercase text-zinc-400 px-2 mb-2 flex items-center gap-1.5 font-semibold">
                <Users className="w-3.5 h-3.5 text-emerald-400" />
                <span>DRIVERS ({matchingDrivers.length})</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
                {matchingDrivers.map((d) => (
                  <div
                    key={d.code}
                    onClick={() => {
                      onNavigate('incidents');
                      onClose();
                    }}
                    className="p-2 rounded bg-[#090c12] border border-[#1a2434] hover:border-[#2b394f] cursor-pointer flex items-center gap-2.5"
                  >
                    <span
                      className="w-6 h-6 rounded flex items-center justify-center font-mono font-bold text-white text-[10px]"
                      style={{ backgroundColor: d.teamColor }}
                    >
                      {d.number}
                    </span>
                    <div>
                      <div className="text-xs font-semibold text-white">
                        {d.name} ({d.code})
                      </div>
                      <div className="text-[10px] text-zinc-400 font-mono">
                        {d.team}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Races Section */}
          {matchingRaces.length > 0 && (
            <div className="pt-3">
              <div className="text-[10px] font-mono uppercase text-zinc-400 px-2 mb-2 flex items-center gap-1.5 font-semibold">
                <Flag className="w-3.5 h-3.5 text-amber-400" />
                <span>RACES & SESSIONS</span>
              </div>
              <div className="space-y-1">
                {matchingRaces.map((r) => (
                  <div
                    key={r.id}
                    onClick={() => {
                      onNavigate('dashboard');
                      onClose();
                    }}
                    className="p-2 rounded hover:bg-[#121924] cursor-pointer flex items-center justify-between text-xs"
                  >
                    <span className="font-semibold text-white">{r.name} — {r.circuit}</span>
                    <span className="text-[10px] font-mono text-emerald-400">ANALYSIS READY</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {matchingIncidents.length === 0 && matchingRegulations.length === 0 && matchingDrivers.length === 0 && matchingRaces.length === 0 && (
            <div className="p-8 text-center text-zinc-500 font-mono text-xs">
              No evidence matching "{query}". Try searching "VER", "33.4", "Monza", or "contact".
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
