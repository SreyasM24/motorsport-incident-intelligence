import React, { useState } from 'react';
import { RelevantRegulation } from '../lib/types';
import { ExternalLink, ChevronDown, ChevronUp, Scale } from 'lucide-react';

interface RegulationPanelProps {
  regulations: RelevantRegulation[];
}

export const RegulationPanel: React.FC<RegulationPanelProps> = ({ regulations }) => {
  const [expandedId, setExpandedId] = useState<string | null>(regulations[0]?.id || null);

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-white/10 bg-[#0a0a0b] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Scale className="w-4 h-4 text-red-600" />
          <div>
            <span className="text-xs font-bold text-white tracking-[0.2em] font-tech uppercase">
              RELEVANT REGULATIONS
            </span>
            <span className="ml-2 text-[10px] font-mono text-white/40">
              FIA Cross-Referenced Sporting Code
            </span>
          </div>
        </div>
        <span className="text-[10px] font-mono bg-white/10 text-white/80 px-2 py-0.5 rounded-sm border border-white/10">
          FIA 2024
        </span>
      </div>

      {/* Regulation Articles */}
      <div className="divide-y divide-white/5">
        {regulations.map((reg) => {
          const isExpanded = expandedId === reg.id;
          const isHigh = reg.relevance === 'High';
          return (
            <div key={reg.id} className="transition-colors hover:bg-white/[0.02]">
              <button
                onClick={() => toggleExpand(reg.id)}
                className="w-full p-4 flex items-center justify-between text-left cursor-pointer"
              >
                <div>
                  <div className="text-[9px] font-mono tracking-widest text-white/40 uppercase">
                    {reg.document}
                  </div>
                  <div className="flex items-center gap-2.5 mt-0.5">
                    <span className={`text-sm font-bold font-mono ${isHigh ? 'text-red-500' : 'text-white'}`}>
                      {reg.article.toUpperCase()}
                    </span>
                    <span className="text-xs text-white/80 font-medium">
                      — {reg.title}
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-white/40 mt-1">
                    Match Rationale: <span className="text-white/70">{reg.matchReason}</span>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span
                    className={`text-[9px] font-mono px-2 py-0.5 rounded-sm uppercase font-bold border ${
                      isHigh
                        ? 'bg-red-600/10 text-red-500 border-red-600/20'
                        : 'bg-white/10 text-white/60 border-white/10'
                    }`}
                  >
                    MATCH: {reg.relevance.toUpperCase()}
                  </span>
                  <div className="text-white/40">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </div>
                </div>
              </button>

              {isExpanded && (
                <div className="px-5 pb-5 pt-2 bg-[#0a0a0b]/60 border-t border-white/5 space-y-3 text-xs">
                  {/* Regulation Text */}
                  <div className="p-4 rounded-sm bg-white/5 border border-white/5 text-white/80 font-sans text-xs italic leading-relaxed">
                    <div className="text-[9px] text-white/40 uppercase tracking-wider mb-1.5 font-mono font-bold not-italic">
                      OFFICIAL SPORTING CODE EXCERPT
                    </div>
                    "{reg.regulationTextPlaceholder}"
                  </div>

                  {/* Why relevant */}
                  <div className="p-3.5 rounded-sm bg-white/5 border border-white/5">
                    <div className="text-[10px] font-mono text-red-500 uppercase font-bold mb-1 tracking-wider">
                      WHY THIS ARTICLE IS RELEVANT
                    </div>
                    <p className="text-white/80 leading-relaxed font-sans text-xs">
                      {reg.whyRelevant}
                    </p>
                  </div>

                  {/* Source metadata */}
                  <div className="flex items-center justify-between pt-2 border-t border-white/5 text-[10px] font-mono text-white/40">
                    <div>
                      <span className="text-white/40 font-bold">SOURCE: </span>
                      <span className="text-white/70">{reg.source}</span>
                    </div>
                    <button className="flex items-center gap-1 text-white/60 hover:text-white transition-colors">
                      <span className="uppercase tracking-wider text-[9px]">Official Rulebook</span>
                      <ExternalLink className="w-3 h-3" />
                    </button>
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
