import React, { useState } from 'react';
import { EvidenceItem, EvidenceCategory } from '../lib/types';
import { 
  ChevronDown, 
  ChevronUp, 
  ShieldAlert, 
  Compass, 
  Gauge, 
  Zap, 
  MoveDiagonal, 
  Sliders 
} from 'lucide-react';

interface EvidencePanelProps {
  evidenceList: EvidenceItem[];
}

export const EvidencePanel: React.FC<EvidencePanelProps> = ({ evidenceList }) => {
  const [expandedId, setExpandedId] = useState<string | null>(evidenceList[0]?.id || null);

  const getCategoryIcon = (category: EvidenceCategory) => {
    switch (category) {
      case 'PROXIMITY':
        return <MoveDiagonal className="w-3.5 h-3.5 text-yellow-500" />;
      case 'RELATIVE_MOTION':
        return <Gauge className="w-3.5 h-3.5 text-cyan-400" />;
      case 'VEHICLE_RESPONSE':
        return <ShieldAlert className="w-3.5 h-3.5 text-red-500" />;
      case 'TRAJECTORY':
        return <Compass className="w-3.5 h-3.5 text-purple-400" />;
      case 'BRAKING':
        return <Zap className="w-3.5 h-3.5 text-emerald-500" />;
    }
  };

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm overflow-hidden">
      {/* Panel Header */}
      <div className="p-4 border-b border-white/10 bg-[#0a0a0b] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Sliders className="w-4 h-4 text-red-600" />
          <div>
            <span className="text-xs font-bold text-white tracking-[0.2em] font-tech uppercase">
              EVIDENCE ASSESSMENT
            </span>
            <span className="ml-2 text-[10px] font-mono text-white/40">
              Categorized Telemetry & Ingest Metrics
            </span>
          </div>
        </div>
        <div className="text-[10px] font-mono text-white/40">
          5 Observations
        </div>
      </div>

      {/* Categories & Items List */}
      <div className="divide-y divide-white/5">
        {evidenceList.map((item) => {
          const isExpanded = expandedId === item.id;
          return (
            <div key={item.id} className="transition-colors hover:bg-white/[0.02]">
              {/* Collapsed Header */}
              <button
                onClick={() => toggleExpand(item.id)}
                className="w-full p-4 flex items-center justify-between text-left cursor-pointer"
              >
                <div className="flex items-center gap-3.5">
                  <div className="p-2 rounded-sm bg-white/5 border border-white/10">
                    {getCategoryIcon(item.category)}
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-[9px] font-mono tracking-widest text-white/40 uppercase font-semibold">
                        {item.category.replace('_', ' ')}
                      </span>
                      <span className="text-emerald-500 text-xs font-bold">✓</span>
                    </div>
                    <div className="text-xs font-medium text-white/90 mt-0.5 font-sans">
                      {item.title}: <span className="font-mono font-bold text-white">{item.observedValue}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="hidden sm:flex flex-col items-end">
                    <span className="text-[9px] font-mono text-white/40 uppercase">Confidence</span>
                    <span className="text-xs font-mono font-bold text-white">
                      {item.confidence}%
                    </span>
                  </div>
                  <div className="text-white/40">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </div>
              </button>

              {/* Expanded Assessment Details */}
              {isExpanded && (
                <div className="px-5 pb-5 pt-2 bg-[#0a0a0b]/60 border-t border-white/5 text-xs font-mono space-y-3">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <div className="p-3 rounded-sm bg-white/5 border border-white/5">
                      <div className="text-[9px] text-white/40 uppercase tracking-wider mb-1">
                        Observed Value
                      </div>
                      <div className="text-sm font-bold text-white font-mono-num">
                        {item.observedValue}
                      </div>
                    </div>

                    <div className="p-3 rounded-sm bg-white/5 border border-white/5">
                      <div className="text-[9px] text-white/40 uppercase tracking-wider mb-1">
                        Expected / Baseline Context
                      </div>
                      <div className="text-xs text-white/80 font-sans">
                        {item.expectedContext}
                      </div>
                    </div>
                  </div>

                  <div className="text-xs text-white/70 leading-relaxed font-sans p-1">
                    {item.description}
                  </div>

                  <div className="flex flex-wrap items-center justify-between pt-3 border-t border-white/5 text-[10px] text-white/40">
                    <div className="flex items-center gap-1.5">
                      <span className="text-white/40 font-bold">SOURCE:</span>
                      <span className="text-white/80 font-semibold">{item.source}</span>
                    </div>
                    <div className="text-[10px] text-white/30 italic">
                      Deterministic calculation • Intent not implied
                    </div>
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
