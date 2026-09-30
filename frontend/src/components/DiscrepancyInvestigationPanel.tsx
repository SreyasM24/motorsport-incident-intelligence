import React, { useState } from 'react';
import { WorkspaceDiscrepancyItem, DiscrepancyStatus } from '../lib/types';
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  HelpCircle,
  ShieldCheck,
  Send,
  Eye,
  SlidersHorizontal,
} from 'lucide-react';

interface DiscrepancyInvestigationPanelProps {
  discrepancies: WorkspaceDiscrepancyItem[];
  candidateId: string;
  onUpdateStatus: (
    discrepancyId: string,
    status: DiscrepancyStatus,
    note?: string
  ) => Promise<void>;
}

export const DiscrepancyInvestigationPanel: React.FC<DiscrepancyInvestigationPanelProps> = ({
  discrepancies,
  candidateId,
  onUpdateStatus,
}) => {
  const [selectedStatus, setSelectedStatus] = useState<Record<string, DiscrepancyStatus>>({});
  const [notes, setNotes] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState<Record<string, boolean>>({});

  const handleStatusSubmit = async (discrepancyId: string) => {
    const status = selectedStatus[discrepancyId] || 'ACKNOWLEDGED';
    const note = notes[discrepancyId];
    setIsSubmitting((prev) => ({ ...prev, [discrepancyId]: true }));
    try {
      await onUpdateStatus(discrepancyId, status, note);
      setNotes((prev) => ({ ...prev, [discrepancyId]: '' }));
    } finally {
      setIsSubmitting((prev) => ({ ...prev, [discrepancyId]: false }));
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity.toUpperCase()) {
      case 'HIGH':
      case 'UNRESOLVED':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-red-600/20 text-red-400 border border-red-600/30">
            {severity}
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-amber-500/20 text-amber-300 border border-amber-500/30">
            {severity}
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-blue-500/20 text-blue-300 border border-blue-500/30">
            {severity}
          </span>
        );
    }
  };

  const getStatusBadge = (status: DiscrepancyStatus) => {
    switch (status) {
      case 'RESOLVED':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1">
            <CheckCircle2 className="w-2.5 h-2.5" />
            RESOLVED
          </span>
        );
      case 'ACKNOWLEDGED':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-blue-500/10 text-blue-400 border border-blue-500/30 flex items-center gap-1">
            <Eye className="w-2.5 h-2.5" />
            ACKNOWLEDGED
          </span>
        );
      case 'UNRESOLVED':
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-red-500/10 text-red-400 border border-red-500/30 flex items-center gap-1">
            <AlertTriangle className="w-2.5 h-2.5" />
            UNRESOLVED
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-xs font-mono text-[9px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1">
            <Clock className="w-2.5 h-2.5" />
            OPEN
          </span>
        );
    }
  };

  return (
    <div className="space-y-4 bg-[#0d0d0f] border border-white/10 rounded-sm p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
        <div>
          <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
            <span className="w-2 h-2 bg-red-600 rounded-full"></span>
            CROSS-MODAL DISCREPANCIES & TENSIONS
          </div>
          <div className="text-[10px] font-mono text-white/40 mt-0.5">
            Technical contradictions are surfaced for human investigation • Automated reconciliation prohibited
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono text-white/60">
          <span className="bg-white/5 border border-white/10 px-2.5 py-1 rounded-sm">
            Active: <strong className="text-white">{discrepancies.length}</strong>
          </span>
        </div>
      </div>

      {/* Discrepancies List */}
      <div className="space-y-3 pt-1">
        {discrepancies.length === 0 ? (
          <div className="p-6 text-center text-xs font-mono text-emerald-400 bg-emerald-500/5 border border-emerald-500/20 rounded-sm flex items-center justify-center gap-2">
            <ShieldCheck className="w-4 h-4" />
            <span>Zero cross-modal discrepancies detected across active evidence streams.</span>
          </div>
        ) : (
          discrepancies.map((disc) => {
            const currentStatus = disc.status;
            const targetStatus = selectedStatus[disc.discrepancy_id || (disc as any).discrepancyId] || currentStatus;
            const discId = disc.discrepancy_id || (disc as any).discrepancyId;

            return (
              <div
                key={discId}
                className="bg-[#0a0a0b] border border-white/10 rounded-sm p-4 space-y-3 font-mono text-xs"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-white tracking-wide">
                      {disc.evidence_a || (disc as any).evidenceA} vs {disc.evidence_b || (disc as any).evidenceB}
                    </span>
                    <span className="text-[10px] text-white/40">[{disc.discrepancy_type || (disc as any).discrepancyType}]</span>
                    {getSeverityBadge(disc.severity)}
                  </div>
                  <div>{getStatusBadge(disc.status)}</div>
                </div>

                <div className="text-xs text-white/80 leading-relaxed bg-[#08080a] border border-white/5 p-3 rounded-xs">
                  {disc.explanation}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-[11px] text-white/60 bg-[#08080a] border border-white/5 p-3 rounded-xs">
                  <div>
                    <span className="text-white/40">Observed Magnitude:</span>{' '}
                    <strong className="text-white">{disc.magnitude}</strong>
                  </div>
                  <div>
                    <span className="text-white/40">Sensor Uncertainty / Expected:</span>{' '}
                    <strong className="text-white">{disc.uncertainty}</strong>
                  </div>
                </div>

                {/* Status Update & Human Notes Form */}
                <div className="bg-[#121216] border border-white/10 p-3 rounded-xs space-y-2.5">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-amber-400">
                    Steward Discrepancy Assessment
                  </div>

                  <div className="flex flex-wrap items-center gap-2">
                    {(['OPEN', 'ACKNOWLEDGED', 'RESOLVED', 'UNRESOLVED'] as const).map((st) => (
                      <button
                        key={st}
                        type="button"
                        onClick={() =>
                          setSelectedStatus((prev) => ({ ...prev, [discId]: st }))
                        }
                        className={`px-2.5 py-1 text-[10px] uppercase font-bold rounded-xs border transition-colors cursor-pointer ${
                          targetStatus === st
                            ? 'bg-amber-500/20 text-amber-300 border-amber-500/50'
                            : 'bg-white/5 hover:bg-white/10 text-white/60 border-white/10'
                        }`}
                      >
                        {st}
                      </button>
                    ))}
                  </div>

                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={notes[discId] || ''}
                      onChange={(e) =>
                        setNotes((prev) => ({ ...prev, [discId]: e.target.value }))
                      }
                      placeholder="Record steward assessment rationale regarding this contradiction..."
                      className="flex-1 bg-[#09090b] border border-white/10 focus:border-amber-500 text-xs px-3 py-1.5 rounded-xs text-white placeholder:text-white/30 outline-none"
                    />
                    <button
                      type="button"
                      disabled={isSubmitting[discId]}
                      onClick={() => handleStatusSubmit(discId)}
                      className="px-4 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-[11px] font-bold uppercase tracking-wider rounded-xs transition-colors cursor-pointer flex items-center gap-1.5 disabled:opacity-50"
                    >
                      <span>{isSubmitting[discId] ? 'Saving...' : 'Update Status'}</span>
                      <Send className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
