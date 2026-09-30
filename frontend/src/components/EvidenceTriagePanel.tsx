import React, { useState } from 'react';
import {
  WorkspaceEvidenceItem,
  TriageEpistemicType,
  AcknowledgementAction,
} from '../lib/types';
import {
  ShieldAlert,
  CheckCircle,
  HelpCircle,
  Eye,
  Sliders,
  Cpu,
  FileText,
  AlertOctagon,
  Tag,
  Clock,
  Send,
  Check,
  ChevronDown,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';

interface EvidenceTriagePanelProps {
  evidenceItems: WorkspaceEvidenceItem[];
  candidateId: string;
  onRecordAcknowledgement: (
    evidenceId: string,
    action: AcknowledgementAction,
    note?: string
  ) => Promise<void>;
}

export const EvidenceTriagePanel: React.FC<EvidenceTriagePanelProps> = ({
  evidenceItems,
  candidateId,
  onRecordAcknowledgement,
}) => {
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [expandedItemId, setExpandedItemId] = useState<string | null>(null);
  const [pendingAction, setPendingAction] = useState<Record<string, AcknowledgementAction>>({});
  const [pendingNote, setPendingNote] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState<Record<string, boolean>>({});

  const epistemicCounts = {
    ALL: evidenceItems.length,
    OBSERVED: evidenceItems.filter((i) => i.epistemicType === 'OBSERVED').length,
    DERIVED: evidenceItems.filter((i) => i.epistemicType === 'DERIVED').length,
    MODEL_DERIVED: evidenceItems.filter((i) => i.epistemicType === 'MODEL_DERIVED').length,
    DOCUMENTARY: evidenceItems.filter((i) => i.epistemicType === 'DOCUMENTARY').length,
    UNAVAILABLE: evidenceItems.filter((i) => i.epistemicType === 'UNAVAILABLE').length,
  };

  const filteredItems = evidenceItems.filter((item) => {
    if (selectedFilter === 'ALL') return true;
    return item.epistemicType === selectedFilter;
  });

  const getEpistemicBadge = (type: TriageEpistemicType) => {
    switch (type) {
      case 'OBSERVED':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <Eye className="w-2.5 h-2.5" />
            1. OBSERVED
          </span>
        );
      case 'DERIVED':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center gap-1">
            <Sliders className="w-2.5 h-2.5" />
            2. DERIVED
          </span>
        );
      case 'MODEL_DERIVED':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-purple-500/10 text-purple-400 border border-purple-500/30 flex items-center gap-1">
            <Cpu className="w-2.5 h-2.5" />
            3. MODEL-DERIVED
          </span>
        );
      case 'DOCUMENTARY':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <FileText className="w-2.5 h-2.5" />
            4. DOCUMENTARY
          </span>
        );
      case 'UNAVAILABLE':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/30 flex items-center gap-1">
            <AlertOctagon className="w-2.5 h-2.5" />
            5. UNAVAILABLE
          </span>
        );
    }
  };

  const handleActionSubmit = async (evidenceId: string) => {
    const action = pendingAction[evidenceId] || 'CONSIDERED';
    const note = pendingNote[evidenceId];
    setIsSubmitting((prev) => ({ ...prev, [evidenceId]: true }));
    try {
      await onRecordAcknowledgement(evidenceId, action, note);
      // Clear note field on success
      setPendingNote((prev) => ({ ...prev, [evidenceId]: '' }));
    } finally {
      setIsSubmitting((prev) => ({ ...prev, [evidenceId]: false }));
    }
  };

  return (
    <div className="space-y-4 bg-[#0d0d0f] border border-white/10 rounded-sm p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
        <div>
          <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
            <span className="w-2 h-2 bg-red-600 rounded-full"></span>
            EVIDENCE TRIAGE & EPISTEMIC TAXONOMY
          </div>
          <div className="text-[10px] font-mono text-white/40 mt-0.5">
            Strict epistemic separation • UX prioritization ordering (NOT proof of fault)
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-sm">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Non-Adjudicative Review Tool</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex flex-wrap items-center gap-1.5 pt-1">
        {(['ALL', 'OBSERVED', 'DERIVED', 'MODEL_DERIVED', 'DOCUMENTARY', 'UNAVAILABLE'] as const).map(
          (filter) => {
            const count = epistemicCounts[filter];
            const isActive = selectedFilter === filter;
            return (
              <button
                key={filter}
                onClick={() => setSelectedFilter(filter)}
                className={`px-3 py-1.5 text-[11px] font-mono font-bold uppercase rounded-sm border transition-colors cursor-pointer flex items-center gap-1.5 ${
                  isActive
                    ? 'bg-red-600 text-white border-red-500 shadow-sm'
                    : 'bg-white/5 hover:bg-white/10 border-white/10 text-white/70 hover:text-white'
                }`}
              >
                <span>{filter.replace('_', ' ')}</span>
                <span
                  className={`text-[9px] px-1.5 py-0.2 rounded-full ${
                    isActive ? 'bg-black/30 text-white' : 'bg-white/10 text-white/50'
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          }
        )}
      </div>

      {/* Triage Items List */}
      <div className="space-y-2.5 pt-1">
        {filteredItems.length === 0 ? (
          <div className="p-6 text-center text-xs font-mono text-white/40 bg-[#0a0a0b] border border-white/5 rounded-sm">
            No evidence items in this epistemic category.
          </div>
        ) : (
          filteredItems.map((item) => {
            const isExpanded = expandedItemId === item.evidenceId;
            const latestAck = item.latestAcknowledgement;
            const currentSelectedAction = pendingAction[item.evidenceId] || latestAck?.action || 'CONSIDERED';

            return (
              <div
                key={item.evidenceId}
                className="bg-[#0a0a0b] border border-white/10 hover:border-white/20 rounded-sm transition-colors overflow-hidden"
              >
                {/* Collapsed Header Bar */}
                <div
                  onClick={() => setExpandedItemId(isExpanded ? null : item.evidenceId)}
                  className="p-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 cursor-pointer"
                >
                  <div className="flex items-start md:items-center gap-3">
                    <button className="text-white/40 hover:text-white mt-0.5 md:mt-0">
                      {isExpanded ? (
                        <ChevronDown className="w-4 h-4" />
                      ) : (
                        <ChevronRight className="w-4 h-4" />
                      )}
                    </button>

                    <div className="space-y-1">
                      <div className="flex flex-wrap items-center gap-2">
                        {getEpistemicBadge(item.epistemicType)}
                        <span className="font-mono text-xs font-bold text-white tracking-wide">
                          {item.evidenceId}
                        </span>
                        <span className="text-[10px] font-mono text-white/40">
                          [{item.evidenceType}]
                        </span>
                      </div>
                      <div className="text-xs text-white/90 font-mono">
                        {item.observation}
                      </div>
                    </div>
                  </div>

                  {/* Right Meta & Ack Badge */}
                  <div className="flex items-center gap-2 shrink-0 pl-7 md:pl-0">
                    <span className="text-[10px] font-mono text-white/40 bg-white/5 border border-white/10 px-2 py-0.5 rounded-xs">
                      {item.source}
                    </span>

                    {latestAck ? (
                      <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
                        <Check className="w-2.5 h-2.5" />
                        {latestAck.action}
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] uppercase tracking-wider bg-white/5 text-white/40 border border-white/10">
                        PENDING TRIAGE
                      </span>
                    )}
                  </div>
                </div>

                {/* Expanded Details Drawer */}
                {isExpanded && (
                  <div className="border-t border-white/10 bg-[#0d0d10] p-4 space-y-4 text-xs font-mono">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Technical Details */}
                      <div className="space-y-2 bg-[#08080a] border border-white/5 p-3 rounded-xs">
                        <div className="text-[10px] text-white/40 uppercase tracking-wider font-bold">
                          Technical Provenance & Lineage
                        </div>
                        <div className="text-[11px] text-white/80">
                          <span className="text-white/40">Provenance:</span> {item.provenance}
                        </div>
                        {item.parentEvidenceIds.length > 0 && (
                          <div className="text-[11px] text-white/80">
                            <span className="text-white/40">Derived From:</span>{' '}
                            {item.parentEvidenceIds.join(', ')}
                          </div>
                        )}
                        <div className="text-[11px] text-white/80">
                          <span className="text-white/40">Availability:</span> {item.availability}
                        </div>
                        <div className="text-[11px] text-white/80">
                          <span className="text-white/40">Data Quality:</span> {item.quality}
                        </div>
                        {item.timestamp && (
                          <div className="text-[11px] text-white/80">
                            <span className="text-white/40">Timestamp:</span> {item.timestamp}
                          </div>
                        )}
                      </div>

                      {/* Known Limitations */}
                      <div className="space-y-2 bg-[#08080a] border border-white/5 p-3 rounded-xs">
                        <div className="text-[10px] text-white/40 uppercase tracking-wider font-bold">
                          Known Measurement Limitations
                        </div>
                        {item.limitations.length > 0 ? (
                          <ul className="list-disc list-inside space-y-1 text-[11px] text-white/70">
                            {item.limitations.map((lim, lIdx) => (
                              <li key={lIdx}>{lim}</li>
                            ))}
                          </ul>
                        ) : (
                          <div className="text-[11px] text-white/40">No critical sensor caveats logged.</div>
                        )}
                      </div>
                    </div>

                    {/* Reviewer Triage Action Form */}
                    <div className="bg-[#121216] border border-white/10 p-3 rounded-xs space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-amber-400 flex items-center gap-1.5">
                          <Tag className="w-3 h-3" />
                          Record Human Steward Acknowledgement
                        </span>
                        {latestAck && (
                          <span className="text-[9px] text-white/40">
                            Last reviewed by {latestAck.reviewerId}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-2">
                        {(
                          [
                            'CONSIDERED',
                            'NOT_RELEVANT',
                            'INSUFFICIENT',
                            'CONTRADICTORY',
                            'REQUIRES_FOLLOW_UP',
                          ] as const
                        ).map((action) => (
                          <button
                            key={action}
                            type="button"
                            onClick={() =>
                              setPendingAction((prev) => ({ ...prev, [item.evidenceId]: action }))
                            }
                            className={`px-2.5 py-1 text-[10px] uppercase font-bold rounded-xs border transition-colors cursor-pointer ${
                              currentSelectedAction === action
                                ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                                : 'bg-white/5 hover:bg-white/10 text-white/60 border-white/10'
                            }`}
                          >
                            {action.replace('_', ' ')}
                          </button>
                        ))}
                      </div>

                      <div className="flex gap-2">
                        <input
                          type="text"
                          value={pendingNote[item.evidenceId] || ''}
                          onChange={(e) =>
                            setPendingNote((prev) => ({
                              ...prev,
                              [item.evidenceId]: e.target.value,
                            }))
                          }
                          placeholder="Optional human note (e.g. Telemetry verified against reference trace)..."
                          className="flex-1 bg-[#09090b] border border-white/10 focus:border-amber-500 text-xs px-3 py-1.5 rounded-xs text-white placeholder:text-white/30 outline-none"
                        />
                        <button
                          type="button"
                          disabled={isSubmitting[item.evidenceId]}
                          onClick={() => handleActionSubmit(item.evidenceId)}
                          className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-[11px] font-bold uppercase tracking-wider rounded-xs transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                        >
                          <span>{isSubmitting[item.evidenceId] ? 'Saving...' : 'Acknowledge'}</span>
                          <Send className="w-3 h-3" />
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
