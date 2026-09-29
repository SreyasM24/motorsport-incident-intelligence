import React from 'react';
import { EvidenceRegulationConnection } from '../lib/types';
import { ArrowDown, GitMerge } from 'lucide-react';

interface EvidenceRegulationFlowProps {
  connections: EvidenceRegulationConnection[];
}

export const EvidenceRegulationFlow: React.FC<EvidenceRegulationFlowProps> = ({ connections }) => {
  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm overflow-hidden">
      <div className="p-4 border-b border-white/10 bg-[#0a0a0b] flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <GitMerge className="w-4 h-4 text-red-600" />
          <div>
            <span className="text-xs font-bold text-white tracking-[0.2em] font-tech uppercase">
              EVIDENCE ↔ REGULATION CORRELATION
            </span>
            <span className="ml-2 text-[10px] font-mono text-white/40">
              Evidence-Rule Pipeline
            </span>
          </div>
        </div>
        <span className="text-[10px] font-mono text-white/70 bg-white/10 border border-white/10 px-2 py-0.5 rounded-sm uppercase tracking-wider">
          STEWARD WORKFLOW
        </span>
      </div>

      <div className="p-5 space-y-4">
        {connections.map((item, index) => (
          <div 
            key={index}
            className="p-4 rounded-sm bg-[#0a0a0b] border border-white/10 space-y-3"
          >
            {/* Step 1: Observed Evidence */}
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-sm bg-white/10 border border-white/10 flex items-center justify-center text-[10px] font-mono font-bold text-yellow-500 shrink-0 mt-0.5">
                01
              </div>
              <div className="flex-1">
                <div className="text-[9px] font-mono tracking-widest text-white/40 uppercase font-bold">
                  OBSERVED EVIDENCE
                </div>
                <div className="text-xs font-medium text-white/90 mt-0.5 font-sans">
                  {item.observedEvidence}
                </div>
              </div>
            </div>

            {/* Connector */}
            <div className="flex items-center justify-center text-white/20 my-0.5">
              <ArrowDown className="w-3.5 h-3.5" />
            </div>

            {/* Step 2: Relevant Regulation */}
            <div className="flex items-start gap-3">
              <div className="w-6 h-6 rounded-sm bg-white/10 border border-white/10 flex items-center justify-center text-[10px] font-mono font-bold text-red-500 shrink-0 mt-0.5">
                02
              </div>
              <div className="flex-1">
                <div className="text-[9px] font-mono tracking-widest text-white/40 uppercase font-bold">
                  RELEVANT REGULATION
                </div>
                <div className="text-xs font-mono font-bold text-white mt-0.5">
                  {item.relevantRegulation}
                </div>
              </div>
            </div>

            {/* Connector */}
            <div className="flex items-center justify-center text-white/20 my-0.5">
              <ArrowDown className="w-3.5 h-3.5" />
            </div>

            {/* Step 3: Human Steward Action */}
            <div className="flex items-start gap-3 bg-white/5 p-3 rounded-sm border border-white/5">
              <div className="w-6 h-6 rounded-sm bg-white/10 border border-white/10 flex items-center justify-center text-[10px] font-mono font-bold text-emerald-500 shrink-0 mt-0.5">
                03
              </div>
              <div className="flex-1">
                <div className="text-[9px] font-mono tracking-widest text-emerald-500 uppercase font-bold">
                  STEWARD REVIEW INQUIRY
                </div>
                <div className="text-xs font-medium text-white/90 mt-0.5 font-sans">
                  {item.stewardReviewAction}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
