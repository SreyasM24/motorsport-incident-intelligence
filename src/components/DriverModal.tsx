import React from 'react';
import { Driver } from '../lib/types';
import { X, Gauge, Flag, AlertTriangle, Activity } from 'lucide-react';

interface DriverModalProps {
  driver: Driver | null;
  onClose: () => void;
  onViewIncidents?: (driverCode: string) => void;
}

export const DriverModal: React.FC<DriverModalProps> = ({
  driver,
  onClose,
  onViewIncidents,
}) => {
  if (!driver) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div 
        className="bg-[#0d0d0f] border border-white/10 rounded-sm max-w-md w-full overflow-hidden shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with team color accent */}
        <div 
          className="p-6 border-b border-white/10 relative flex items-center justify-between bg-[#0a0a0b]"
          style={{ borderTop: `3px solid ${driver.teamColor}` }}
        >
          <div className="flex items-center gap-4">
            <div 
              className="w-12 h-12 rounded-sm flex items-center justify-center text-xl font-bold font-mono text-white shadow-md"
              style={{ backgroundColor: driver.teamColor }}
            >
              #{driver.number}
            </div>
            <div>
              <div className="text-[10px] font-mono tracking-widest text-white/40 uppercase">
                {driver.team}
              </div>
              <h3 className="text-lg font-light text-white font-tech uppercase tracking-wide">
                {driver.name}
              </h3>
              <div className="text-[11px] font-mono text-white/50">
                Driver Code: <span className="text-white font-bold">{driver.code}</span> • {driver.country}
              </div>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-sm text-white/40 hover:text-white hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Session Stats Grid */}
        <div className="p-6 space-y-4">
          <div className="text-[10px] font-mono uppercase tracking-widest text-white/40 font-bold">
            Italian Grand Prix 2024 — Session Telemetry Record
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="p-3.5 rounded-sm bg-white/5 border border-white/10">
              <div className="flex items-center gap-1.5 text-white/40 text-[10px] uppercase font-mono mb-1">
                <Flag className="w-3 h-3 text-white/40" />
                Laps Completed
              </div>
              <div className="text-lg font-bold text-white font-mono">
                {driver.stats.lapsCompleted} / 53
              </div>
            </div>

            <div className="p-3.5 rounded-sm bg-white/5 border border-white/10">
              <div className="flex items-center gap-1.5 text-white/40 text-[10px] uppercase font-mono mb-1">
                <Gauge className="w-3 h-3 text-cyan-400" />
                Average Lap Speed
              </div>
              <div className="text-lg font-bold text-white font-mono">
                {driver.stats.avgSpeedKmh} <span className="text-xs text-white/40 font-normal">km/h</span>
              </div>
            </div>

            <div className="p-3.5 rounded-sm bg-white/5 border border-white/10">
              <div className="flex items-center gap-1.5 text-white/40 text-[10px] uppercase font-mono mb-1">
                <Gauge className="w-3 h-3 text-yellow-500" />
                Max Trap Speed
              </div>
              <div className="text-lg font-bold text-white font-mono">
                {driver.stats.maxSpeedKmh} <span className="text-xs text-white/40 font-normal">km/h</span>
              </div>
            </div>

            <div className="p-3.5 rounded-sm bg-white/5 border border-white/10">
              <div className="flex items-center gap-1.5 text-white/40 text-[10px] uppercase font-mono mb-1">
                <AlertTriangle className="w-3 h-3 text-red-500" />
                Incidents Involved
              </div>
              <div className="text-lg font-bold text-white font-mono">
                {driver.stats.incidentsInvolved} <span className="text-xs text-white/40 font-normal">flagged</span>
              </div>
            </div>
          </div>

          <div className="p-3.5 rounded-sm bg-white/5 border border-white/10 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <Activity className="w-4 h-4 text-purple-400" />
              <div>
                <div className="text-xs font-semibold text-white uppercase tracking-wide font-tech">
                  Proximity Events Detected
                </div>
                <div className="text-[10px] font-mono text-white/40">
                  Relative distance &lt; 5m events
                </div>
              </div>
            </div>
            <div className="text-sm font-bold font-mono text-purple-400">
              {driver.stats.interactionsDetected}
            </div>
          </div>

          <div className="pt-2">
            <button
              onClick={() => {
                if (onViewIncidents) onViewIncidents(driver.code);
                onClose();
              }}
              className="w-full py-2.5 bg-white/10 hover:bg-white/15 border border-white/20 text-xs font-mono font-bold uppercase tracking-wider text-white rounded-sm transition-colors cursor-pointer"
            >
              Filter Incidents by {driver.code}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
