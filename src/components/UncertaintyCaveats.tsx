import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

interface UncertaintyCaveatsProps {
  uncertainties?: string[];
}

export const UncertaintyCaveats: React.FC<UncertaintyCaveatsProps> = ({
  uncertainties = [
    'Video evidence not yet synchronized to sub-millisecond ECU timestamps.',
    'GPS/position data may contain measurement noise (±0.28m) over curb kerbing.',
    'Telemetry alone establishes mechanical vehicle states, not driver intent.',
    'Automated analysis surfaces data anomalies and does not determine sporting fault.',
    'Final decision strictly requires human race steward review.',
  ],
}) => {
  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-5 text-xs font-mono">
      <div className="flex items-center gap-2.5 text-yellow-500 font-bold mb-3">
        <AlertTriangle className="w-4 h-4 shrink-0 text-yellow-500" />
        <span className="tracking-[0.2em] uppercase font-tech text-xs">
          UNCERTAINTY & CAVEATS
        </span>
        <span className="text-[10px] text-white/40 font-mono font-normal ml-auto uppercase tracking-wider">
          Mandatory Evidentiary Notice
        </span>
      </div>

      <ul className="space-y-2 text-white/80">
        {uncertainties.map((item, index) => (
          <li key={index} className="flex items-start gap-2.5">
            <span className="text-yellow-500 font-bold shrink-0 mt-0.5">•</span>
            <span className="leading-relaxed font-sans text-xs text-white/80">{item}</span>
          </li>
        ))}
      </ul>

      <div className="mt-4 pt-3 border-t border-white/10 flex items-center justify-between text-[10px] text-white/40">
        <div className="flex items-center gap-1.5 text-emerald-500">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="font-semibold uppercase tracking-wider">AI assists • Evidence supports • Humans decide</span>
        </div>
        <span className="text-white/30 uppercase tracking-wider">MII Standard v1.0</span>
      </div>
    </div>
  );
};
