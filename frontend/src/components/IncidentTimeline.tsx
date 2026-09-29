import React from 'react';
import { 
  IncidentTimelineMilestone 
} from '../lib/types';
import { 
  Clock, 
  AlertCircle, 
  Zap, 
  Activity, 
  Flag, 
  MoveRight, 
  ShieldAlert 
} from 'lucide-react';

interface IncidentTimelineProps {
  milestones?: IncidentTimelineMilestone[];
  onSelectMilestone?: (timestamp: string) => void;
  selectedTimestamp?: string;
  raceIncidents?: Array<{
    id: string;
    lap: number;
    timestamp: string;
    label: string;
    confidence: number;
    status: string;
    drivers: string;
  }>;
  onSelectIncident?: (id: string) => void;
  mode?: 'incident-detail' | 'race-dashboard';
}

export const IncidentTimeline: React.FC<IncidentTimelineProps> = ({
  milestones = [],
  onSelectMilestone,
  selectedTimestamp,
  raceIncidents = [],
  onSelectIncident,
  mode = 'incident-detail',
}) => {
  const getIcon = (type: string) => {
    switch (type) {
      case 'approach':
        return <MoveRight className="w-3.5 h-3.5 text-white/40" />;
      case 'proximity':
        return <Zap className="w-3.5 h-3.5 text-yellow-500" />;
      case 'contact':
        return <AlertCircle className="w-3.5 h-3.5 text-red-500" />;
      case 'motion':
        return <Activity className="w-3.5 h-3.5 text-cyan-400" />;
      case 'response':
        return <ShieldAlert className="w-3.5 h-3.5 text-red-500" />;
      case 'exit':
        return <Flag className="w-3.5 h-3.5 text-emerald-500" />;
      default:
        return <Clock className="w-3.5 h-3.5 text-white/40" />;
    }
  };

  // RACE DASHBOARD MODE
  if (mode === 'race-dashboard') {
    return (
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm overflow-hidden">
        <div className="p-4 border-b border-white/10 bg-[#0a0a0b] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-red-600" />
            <span className="text-xs font-bold text-white tracking-[0.2em] font-tech uppercase">
              RACE INCIDENT TIMELINE
            </span>
          </div>
          <span className="text-[10px] font-mono text-white/40">
            53 Laps • 1,298 Interaction Candidates
          </span>
        </div>

        {/* Interactive Horizontal Timeline */}
        <div className="p-4 overflow-x-auto">
          <div className="flex flex-col md:flex-row gap-3 min-w-[640px]">
            {raceIncidents.map((item) => (
              <div
                key={item.id}
                onClick={() => onSelectIncident && onSelectIncident(item.id)}
                className={`flex-1 p-3.5 rounded-sm border transition-all cursor-pointer group ${
                  item.id === 'INC-024' || item.id === 'INC-001'
                    ? 'bg-red-600/5 border-red-600/30 hover:border-red-600'
                    : 'bg-white/5 border-white/10 hover:border-white/20'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono font-bold text-white bg-white/10 px-2 py-0.5 rounded-sm">
                    LAP {item.lap < 10 ? `0${item.lap}` : item.lap}
                  </span>
                  <span className="text-[10px] font-mono text-white/40">
                    {item.timestamp}
                  </span>
                </div>

                <div className="text-xs font-semibold text-white/90 group-hover:text-white line-clamp-1 mb-1 font-tech uppercase">
                  {item.label}
                </div>

                <div className="flex items-center justify-between text-[10px] font-mono mt-3 pt-2 border-t border-white/5">
                  <span className="text-white/40">{item.drivers}</span>
                  <span
                    className={`font-bold ${
                      item.confidence >= 85 ? 'text-red-500' : 'text-yellow-500'
                    }`}
                  >
                    {item.confidence}% Conf.
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // INCIDENT DETAIL FINE-GRAINED TIMELINE
  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm overflow-hidden">
      <div className="p-4 border-b border-white/10 bg-[#0a0a0b] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-red-600" />
          <span className="text-xs font-bold text-white tracking-[0.2em] font-tech uppercase">
            CHRONOLOGICAL EVENT MILESTONES
          </span>
        </div>
        <span className="text-[10px] font-mono text-white/40">
          Sub-second Telemetry Reconstructed
        </span>
      </div>

      <div className="p-5">
        <div className="relative border-l-2 border-white/10 ml-3 pl-5 space-y-4">
          {milestones.map((item, idx) => {
            const isCritical = item.iconType === 'contact' || item.iconType === 'response';
            return (
              <div
                key={idx}
                onClick={() => onSelectMilestone && onSelectMilestone(item.timestamp)}
                className={`relative group cursor-pointer p-3 rounded-sm transition-colors ${
                  selectedTimestamp === item.timestamp
                    ? 'bg-white/10 border border-white/20'
                    : 'hover:bg-white/5'
                }`}
              >
                {/* Node on vertical line */}
                <div
                  className={`absolute -left-[31px] top-3.5 w-6 h-6 rounded-full border flex items-center justify-center ${
                    isCritical
                      ? 'bg-red-600/20 border-red-600 text-red-500'
                      : 'bg-[#0a0a0b] border-white/20 text-white/40'
                  }`}
                >
                  {getIcon(item.iconType)}
                </div>

                <div className="flex flex-wrap items-center justify-between gap-1 mb-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-bold text-yellow-500">
                      {item.timestamp}
                    </span>
                    <span className="text-xs font-semibold text-white font-tech uppercase">
                      {item.label}
                    </span>
                  </div>
                  {item.evidenceRef && (
                    <span className="text-[9px] font-mono bg-white/10 text-white/70 px-1.5 py-0.5 rounded-sm border border-white/10">
                      {item.evidenceRef}
                    </span>
                  )}
                </div>

                <p className="text-xs text-white/60 font-sans leading-relaxed">
                  {item.description}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
