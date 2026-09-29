import React, { useState, useEffect } from 'react';
import { IncidentTimeline } from '../components/IncidentTimeline';
import { SystemPipeline } from '../components/SystemPipeline';
import { 
  getIncidents, 
  getRaceActivity 
} from '../lib/api';
import { Incident } from '../lib/types';
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
} from 'recharts';
import { 
  Users, 
  AlertTriangle, 
  ShieldCheck, 
  Activity, 
  ArrowRight,
  ChevronRight,
  Radio,
  Video,
  Scale,
  Bot,
  Binary
} from 'lucide-react';

interface DashboardViewProps {
  onNavigate: (view: string, id?: string) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({ onNavigate }) => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [activityData, setActivityData] = useState<any[]>([]);
  const [activeActivityMetric, setActiveActivityMetric] = useState<'all' | 'candidates' | 'abnormal' | 'highConfidence'>('all');

  useEffect(() => {
    getIncidents().then(setIncidents);
    getRaceActivity().then(setActivityData);
  }, []);

  const timelineIncidents = [
    {
      id: 'INC-005',
      lap: 1,
      timestamp: '13:03:50',
      label: 'Close interaction (multi-car concertina)',
      confidence: 74,
      status: 'DETECTED_INTERACTION' as const,
      drivers: 'ALO → HUL',
    },
    {
      id: 'INC-004',
      lap: 12,
      timestamp: '13:18:04',
      label: 'Possible vehicle disturbance & wheel crowding',
      confidence: 82,
      status: 'REVIEWED' as const,
      drivers: 'RUS → PER',
    },
    {
      id: 'INC-024',
      lap: 31,
      timestamp: '13:42:18',
      label: 'Possible contact / vehicle disturbance',
      confidence: 87,
      status: 'REQUIRES_REVIEW' as const,
      drivers: 'VER → HAM',
    },
    {
      id: 'INC-002',
      lap: 36,
      timestamp: '13:55:21',
      label: 'Abnormal interaction & late apex line',
      confidence: 78,
      status: 'ABNORMAL_INTERACTION' as const,
      drivers: 'NOR → PIA',
    },
    {
      id: 'INC-003',
      lap: 42,
      timestamp: '14:03:42',
      label: 'Vehicle aerodynamic disturbance',
      confidence: 88,
      status: 'REVIEWED' as const,
      drivers: 'LEC → SAI',
    },
  ];

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Session Hero Header */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 md:p-8 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="text-[10px] font-mono tracking-[0.2em] text-red-600 uppercase font-bold">
              Round 16 • F1 World Championship
            </span>
            <span className="text-white/20">•</span>
            <span className="text-[10px] font-mono uppercase tracking-wider text-white/40">
              Autodromo Nazionale Monza
            </span>
          </div>

          <h1 className="text-2xl md:text-4xl font-light tracking-tight text-white uppercase font-tech">
            Italian Grand Prix <span className="text-white/40 text-xl font-normal">2024 • Race</span>
          </h1>

          <div className="flex flex-wrap items-center gap-6 mt-3 text-xs font-mono text-white/60">
            <span>Circuit: <strong className="text-white font-semibold">Monza (5.793 km)</strong></span>
            <span>Length: <strong className="text-white font-semibold">53 Laps</strong></span>
            <span>Telemetry: <strong className="text-emerald-400 font-semibold">25Hz FastF1 Ingest</strong></span>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-4">
          <span className="px-2.5 py-1.5 bg-emerald-500/10 text-emerald-400 text-[10px] font-bold tracking-widest border border-emerald-500/20 rounded-sm font-mono inline-flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
            ANALYSIS READY
          </span>

          <button
            onClick={() => onNavigate('incident-INC-024', 'INC-024')}
            className="bg-red-600 hover:bg-red-700 text-white text-[10px] font-bold py-3 px-5 uppercase tracking-[0.2em] transition-colors rounded-sm flex items-center gap-2 cursor-pointer shadow-sm"
          >
            <span>Review Incident #024</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6">
          <div className="flex items-center justify-between text-white/40 text-[10px] uppercase tracking-widest font-mono mb-2">
            <span>Drivers Tracked</span>
            <Users className="w-3.5 h-3.5 text-white/30" />
          </div>
          <div className="text-3xl md:text-4xl font-mono font-light text-white leading-none">
            20
          </div>
          <div className="text-[10px] font-mono text-white/40 mt-3">
            All transponders calibrated
          </div>
        </div>

        <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6">
          <div className="flex items-center justify-between text-white/40 text-[10px] uppercase tracking-widest font-mono mb-2">
            <span>Incident Candidates</span>
            <Activity className="w-3.5 h-3.5 text-white/30" />
          </div>
          <div className="text-3xl md:text-4xl font-mono font-light text-white leading-none">
            1,298
          </div>
          <div className="text-[10px] font-mono text-white/40 mt-3">
            Proximity & motion anomalies
          </div>
        </div>

        <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6">
          <div className="flex items-center justify-between text-white/40 text-[10px] uppercase tracking-widest font-mono mb-2">
            <span>Requires Review</span>
            <AlertTriangle className="w-3.5 h-3.5 text-red-500" />
          </div>
          <div className="text-3xl md:text-4xl font-mono font-light text-red-500 leading-none">
            3
          </div>
          <div className="text-[10px] font-mono text-yellow-500 mt-3 font-semibold uppercase">
            Awaiting Human Review
          </div>
        </div>

        <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6">
          <div className="flex items-center justify-between text-white/40 text-[10px] uppercase tracking-widest font-mono mb-2">
            <span>Reviewed</span>
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
          </div>
          <div className="text-3xl md:text-4xl font-mono font-light text-white leading-none">
            12
          </div>
          <div className="text-[10px] font-mono text-emerald-400 mt-3">
            Completed by Stewards
          </div>
        </div>
      </div>

      {/* SECTION 6 & D: SESSION OVERVIEW & BACKEND STATUSES */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Incident Activity Chart (2 Columns) */}
        <div className="lg:col-span-2 bg-[#0d0d0f] border border-white/10 rounded-sm p-6 flex flex-col justify-between">
          <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
            <div>
              <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech">
                INCIDENT ACTIVITY DISTRIBUTION
              </div>
              <div className="text-[10px] font-mono text-white/40 mt-0.5">
                Detection density across 53 race laps
              </div>
            </div>

            {/* Filter Toggle */}
            <div className="flex items-center bg-[#0a0a0b] border border-white/10 rounded-sm p-0.5 text-[10px] font-mono">
              <button
                onClick={() => setActiveActivityMetric('all')}
                className={`px-2.5 py-1 rounded-sm transition-colors ${
                  activeActivityMetric === 'all'
                    ? 'bg-white/10 text-white font-bold'
                    : 'text-white/40 hover:text-white'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setActiveActivityMetric('candidates')}
                className={`px-2.5 py-1 rounded-sm transition-colors ${
                  activeActivityMetric === 'candidates'
                    ? 'bg-white/10 text-white font-bold'
                    : 'text-white/40 hover:text-white'
                }`}
              >
                Candidates
              </button>
              <button
                onClick={() => setActiveActivityMetric('abnormal')}
                className={`px-2.5 py-1 rounded-sm transition-colors ${
                  activeActivityMetric === 'abnormal'
                    ? 'bg-white/10 text-white font-bold'
                    : 'text-white/40 hover:text-white'
                }`}
              >
                Abnormal
              </button>
              <button
                onClick={() => setActiveActivityMetric('highConfidence')}
                className={`px-2.5 py-1 rounded-sm transition-colors ${
                  activeActivityMetric === 'highConfidence'
                    ? 'bg-white/10 text-white font-bold'
                    : 'text-white/40 hover:text-white'
                }`}
              >
                High-Confidence
              </button>
            </div>
          </div>

          <div className="h-64 w-full bg-white/5 border border-white/5 rounded-sm p-3">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={activityData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="lap" stroke="#52525b" fontSize={10} tickFormatter={(v) => `Lap ${v}`} />
                <YAxis stroke="#52525b" fontSize={10} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#0d0d0f', borderColor: 'rgba(255, 255, 255, 0.1)', fontSize: '11px', fontFamily: 'monospace' }}
                  itemStyle={{ color: '#e0e0e0' }}
                />
                {(activeActivityMetric === 'all' || activeActivityMetric === 'candidates') && (
                  <Bar dataKey="candidates" name="Candidates" fill="#3b82f6" radius={[1, 1, 0, 0]} />
                )}
                {(activeActivityMetric === 'all' || activeActivityMetric === 'abnormal') && (
                  <Bar dataKey="abnormal" name="Abnormal" fill="#f59e0b" radius={[1, 1, 0, 0]} />
                )}
                {(activeActivityMetric === 'all' || activeActivityMetric === 'highConfidence') && (
                  <Bar dataKey="highConfidence" name="High-Confidence" fill="#dc2626" radius={[1, 1, 0, 0]} />
                )}
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="mt-4 flex items-center justify-between text-[10px] font-mono text-white/40">
            <span>Peak interaction density recorded at Lap 31 (Turn 4 incident)</span>
            <span className="text-red-500 font-bold uppercase tracking-wider">● 4 High-Confidence flagged</span>
          </div>
        </div>

        {/* Section 6: Official Session Overview & Backend Pipeline Statuses */}
        <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 flex flex-col justify-between">
          <div>
            <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech mb-1">
              SESSION OVERVIEW
            </div>
            <div className="text-[10px] font-mono text-white/40 mb-3">
              FastAPI Ingest & Evidence Verification
            </div>

            {/* Core Session Identity */}
            <div className="grid grid-cols-2 gap-2 text-xs font-mono mb-4">
              <div className="p-2 rounded-sm bg-white/5 border border-white/5">
                <div className="text-[9px] text-white/40 uppercase">Race</div>
                <div className="font-bold text-white mt-0.5">Italian Grand Prix</div>
              </div>
              <div className="p-2 rounded-sm bg-white/5 border border-white/5">
                <div className="text-[9px] text-white/40 uppercase">Circuit</div>
                <div className="font-bold text-white mt-0.5">Monza</div>
              </div>
              <div className="p-2 rounded-sm bg-white/5 border border-white/5">
                <div className="text-[9px] text-white/40 uppercase">Season</div>
                <div className="font-bold text-white mt-0.5">2024</div>
              </div>
              <div className="p-2 rounded-sm bg-white/5 border border-white/5">
                <div className="text-[9px] text-white/40 uppercase">Session / Drivers</div>
                <div className="font-bold text-white mt-0.5">Race (20 Drivers)</div>
              </div>
            </div>

            {/* Backend Capability Statuses (Section 6 Exact Specs) */}
            <div className="space-y-2 text-xs font-mono">
              <div className="p-2.5 rounded-sm bg-white/5 border border-white/5 flex items-center justify-between">
                <span className="text-white/60">TELEMETRY STATUS</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  CONNECTED / AVAILABLE
                </span>
              </div>

              <div className="p-2.5 rounded-sm bg-white/5 border border-white/5 flex items-center justify-between">
                <span className="text-white/60">INCIDENT ANALYSIS</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  AVAILABLE
                </span>
              </div>

              <div className="p-2.5 rounded-sm bg-white/5 border border-white/5 flex items-center justify-between">
                <span className="text-white/60">REGULATIONS</span>
                <span className="text-emerald-400 font-bold flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
                  AVAILABLE / CONNECTED
                </span>
              </div>

              <div className="p-2.5 rounded-sm bg-white/5 border border-white/5 flex items-center justify-between">
                <span className="text-white/60">VIDEO EVIDENCE</span>
                <span className="text-cyan-400 font-bold flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                  AVAILABLE / NOT LINKED
                </span>
              </div>

              <div className="p-2.5 rounded-sm bg-white/5 border border-white/5 flex items-center justify-between">
                <span className="text-white/60">AI ANALYSIS</span>
                <span className="text-purple-400 font-bold flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                  IN DEVELOPMENT / AVAILABLE
                </span>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-[11px] font-mono">
            <span className="text-white/40">API Target:</span>
            <span className="text-white/80 font-mono">FastAPI /api/v1/session/ita-2024</span>
          </div>
        </div>
      </div>

      {/* Incident Timeline Section */}
      <IncidentTimeline
        mode="race-dashboard"
        raceIncidents={timelineIncidents}
        onSelectIncident={(id) => onNavigate(`incident-${id}`, id)}
      />

      {/* System Pipeline Section */}
      <SystemPipeline />

      {/* Priority Incident Candidates Table */}
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm overflow-hidden">
        <div className="p-5 border-b border-white/10 bg-[#0a0a0b] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-600" />
            <span className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech">
              PRIORITY INCIDENT CANDIDATES
            </span>
          </div>
          <button
            onClick={() => onNavigate('incidents')}
            className="text-xs font-mono text-white/40 hover:text-white flex items-center gap-1 transition-colors cursor-pointer"
          >
            <span>View All Incidents</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>
        </div>

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
              {incidents.slice(0, 5).map((inc) => (
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
                  <td className="p-4 text-white/70">{inc.timestamp}</td>
                  <td className="p-4 text-white font-semibold">Lap {inc.lap}</td>
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
                    <div className="text-white font-medium">{inc.incidentType}</div>
                    <div className="text-[10px] text-white/40">{inc.turn}</div>
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
                          ? 'bg-yellow-500/10 text-yellow-500 border-yellow-500/30'
                          : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
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
      </div>
    </div>
  );
};
