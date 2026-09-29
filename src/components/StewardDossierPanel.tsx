import React, { useState } from 'react';
import {
  FileText,
  Download,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Activity,
  Clock,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  FileCheck,
  AlertCircle
} from 'lucide-react';
import {
  StewardEvidenceDossier,
  EvidenceStatus,
  ConsistencyStatus,
  DiscrepancySeverity,
  EvidenceType
} from '../lib/types';
import { exportStewardDossierJson } from '../lib/api';

interface StewardDossierPanelProps {
  dossier: StewardEvidenceDossier;
}

export const StewardDossierPanel: React.FC<StewardDossierPanelProps> = ({ dossier }) => {
  const [isExporting, setIsExporting] = useState(false);
  const [showRawItems, setShowRawItems] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  const handleExportJson = async () => {
    setIsExporting(true);
    try {
      const payload = await exportStewardDossierJson(dossier.candidateId);
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(payload, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `${dossier.dossierId}_export.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } catch {
      // Deterministic fallback export from client dossier
      const fallbackPayload = {
        exportType: 'JSON_STEWARD_DOSSIER',
        schemaVersion: '2.0',
        exportedAt: new Date().toISOString(),
        dossier,
      };
      const dataStr = 'data:text/json;charset=utf-8,' + encodeURIComponent(JSON.stringify(fallbackPayload, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute('href', dataStr);
      downloadAnchor.setAttribute('download', `${dossier.dossierId}_export.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
      setExportSuccess(true);
      setTimeout(() => setExportSuccess(false), 3000);
    } finally {
      setIsExporting(false);
    }
  };

  const getStatusBadge = (status: EvidenceStatus) => {
    switch (status) {
      case EvidenceStatus.OBSERVED:
        return <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-semibold">OBSERVED</span>;
      case EvidenceStatus.DERIVED:
        return <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-semibold">DERIVED</span>;
      case EvidenceStatus.MODEL_DERIVED:
        return <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-purple-500/10 text-purple-400 border border-purple-500/20 font-semibold">MODEL-DERIVED</span>;
      case EvidenceStatus.DOCUMENTARY:
        return <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-amber-500/10 text-amber-400 border border-amber-500/20 font-semibold">DOCUMENTARY</span>;
      case EvidenceStatus.UNAVAILABLE:
      default:
        return <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-zinc-500/10 text-zinc-400 border border-zinc-500/20 font-semibold">UNAVAILABLE</span>;
    }
  };

  const getConsistencyBadge = (status: ConsistencyStatus) => {
    switch (status) {
      case ConsistencyStatus.CONSISTENT:
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            <CheckCircle2 className="w-3.5 h-3.5" /> CONSISTENT
          </span>
        );
      case ConsistencyStatus.PARTIALLY_CONSISTENT:
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded bg-amber-500/10 text-amber-400 border border-amber-500/30">
            <AlertCircle className="w-3.5 h-3.5" /> PARTIALLY CONSISTENT
          </span>
        );
      case ConsistencyStatus.CONFLICTING:
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded bg-rose-500/10 text-rose-400 border border-rose-500/30">
            <AlertTriangle className="w-3.5 h-3.5" /> CONFLICTING TENSION
          </span>
        );
      case ConsistencyStatus.INSUFFICIENT_DATA:
      default:
        return (
          <span className="flex items-center gap-1.5 px-2.5 py-1 text-xs font-mono rounded bg-zinc-500/10 text-zinc-400 border border-zinc-500/30">
            INSUFFICIENT MULTI-MODAL DATA
          </span>
        );
    }
  };

  const getSeverityBadge = (severity: DiscrepancySeverity) => {
    switch (severity) {
      case DiscrepancySeverity.HIGH:
        return <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-rose-500/20 text-rose-300 border border-rose-500/30 font-bold">HIGH TENSION</span>;
      case DiscrepancySeverity.MEDIUM:
        return <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-amber-500/20 text-amber-300 border border-amber-500/30 font-bold">MEDIUM TENSION</span>;
      case DiscrepancySeverity.LOW:
        return <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 font-bold">LOW VARIANCE</span>;
      case DiscrepancySeverity.UNRESOLVED:
      default:
        return <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-zinc-500/20 text-zinc-300 border border-zinc-500/30 font-bold">UNRESOLVED</span>;
    }
  };

  return (
    <div className="space-y-6 bg-[#0a0a0c] border border-white/10 rounded-sm p-6 text-white font-sans">
      {/* 1. Header & Non-Adjudicative Steward Doctrine Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-5">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded bg-red-600 flex items-center justify-center text-white">
              <FileText className="w-4 h-4" />
            </div>
            <div>
              <div className="text-sm font-bold tracking-[0.2em] uppercase font-tech text-white">
                MASTER STEWARD EVIDENCE DOSSIER
              </div>
              <div className="text-xs font-mono text-white/50">
                Dossier ID: <span className="text-white/80">{dossier.dossierId}</span> • Version {dossier.dossierVersion} ({dossier.analysisVersion})
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportJson}
            disabled={isExporting}
            className="flex items-center gap-2 px-3.5 py-1.5 text-xs font-mono bg-white/5 hover:bg-white/10 border border-white/20 hover:border-white/40 text-white rounded transition-colors cursor-pointer disabled:opacity-50"
          >
            {exportSuccess ? <FileCheck className="w-4 h-4 text-emerald-400" /> : <Download className="w-4 h-4" />}
            <span>{isExporting ? 'EXPORTING...' : exportSuccess ? 'EXPORTED' : 'EXPORT JSON DOSSIER'}</span>
          </button>
        </div>
      </div>

      {/* Critical Non-Adjudicative Steward Doctrine Banner */}
      <div className="p-3 bg-red-950/20 border border-red-500/30 rounded text-xs font-mono text-red-200/90 flex items-start gap-2.5">
        <ShieldCheck className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
        <div>
          <strong className="text-red-300 uppercase tracking-wider block mb-0.5">Strict Non-Adjudicative Support Doctrine:</strong>
          {dossier.stewardDoctrine || 'This dossier provides empirical multi-modal evidence synthesis and technical discrepancy analysis for human stewards. It strictly does NOT decide guilt, apportion fault, issue penalties, or declare regulatory violations.'}
        </div>
      </div>

      {/* 2. Multi-Modal Consensus & Cross-Modal Alignment */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Consensus Card */}
        <div className="bg-[#121215] border border-white/10 rounded p-4 space-y-2">
          <div className="text-[11px] font-mono text-white/40 uppercase tracking-wider flex items-center justify-between">
            <span>Cross-Modal Consistency</span>
            {getConsistencyBadge(dossier.crossModalConsistency)}
          </div>
          <div className="text-xs text-white/80 leading-relaxed pt-1">
            {dossier.consensus.consensusSummary}
          </div>
        </div>

        {/* Independent Lineage Roots (Double-Counting Prevention) */}
        <div className="bg-[#121215] border border-white/10 rounded p-4 space-y-2">
          <div className="text-[11px] font-mono text-white/40 uppercase tracking-wider flex items-center justify-between">
            <span>Lineage & Roots</span>
            <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-bold">
              {dossier.consensus.independentObservationCount} INDEPENDENT ROOTS
            </span>
          </div>
          <div className="text-xs text-white/70 leading-relaxed pt-1">
            Synthesized across <strong className="text-white">{dossier.evidenceItems.length} evidence items</strong>. Multiple derived kinematic metrics sharing FastF1 raw sensor roots are aggregated into 1 independent root to prevent double-counting.
          </div>
        </div>

        {/* Stream Availability Summary */}
        <div className="bg-[#121215] border border-white/10 rounded p-4 space-y-2">
          <div className="text-[11px] font-mono text-white/40 uppercase tracking-wider">
            Streams Synthesis Breakdown
          </div>
          <div className="text-xs font-mono space-y-1 pt-1">
            <div className="flex justify-between text-emerald-400">
              <span>Supporting:</span>
              <span>{dossier.consensus.supportingEvidenceStreams.length}</span>
            </div>
            <div className="flex justify-between text-rose-400">
              <span>Conflicting/Tension:</span>
              <span>{dossier.consensus.conflictingEvidenceStreams.length}</span>
            </div>
            <div className="flex justify-between text-zinc-400">
              <span>Unavailable (Licensing):</span>
              <span>{dossier.consensus.unavailableEvidenceStreams.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. 8 Evidence Streams Quality & Semantics */}
      <div className="space-y-3">
        <div className="text-xs font-bold text-white tracking-[0.15em] uppercase font-tech flex items-center gap-2">
          <Layers className="w-3.5 h-3.5 text-red-500" />
          <span>EVALUATED EVIDENCE STREAMS (8 MODALITIES)</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {dossier.streamQuality.map((stream) => (
            <div key={stream.streamName} className="bg-[#121215] border border-white/10 rounded p-3 space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="font-semibold text-white/90 truncate mr-2">{stream.streamName}</span>
                {getStatusBadge(stream.status)}
              </div>
              <div className="text-[11px] text-white/60">
                Reliability: <span className="text-white/90 font-mono">{stream.reliabilityScore}%</span>
              </div>
              <div className="text-[10px] text-white/40 font-mono truncate" title={stream.dataCompleteness}>
                {stream.dataCompleteness}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 4. Cross-Modal Discrepancies Table */}
      {dossier.discrepancies.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs font-bold text-white tracking-[0.15em] uppercase font-tech flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" />
              <span>CROSS-MODAL DISCREPANCIES & TENSIONS ({dossier.discrepancies.length})</span>
            </div>
            <span className="text-[10px] font-mono text-white/40 font-normal">Technical alignment metrics • Not fault or guilt</span>
          </div>

          <div className="overflow-x-auto border border-white/10 rounded">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-white/5 border-b border-white/10 text-white/50 text-[10px] uppercase">
                <tr>
                  <th className="p-2.5">Discrepancy</th>
                  <th className="p-2.5">Streams Compared</th>
                  <th className="p-2.5">Metric</th>
                  <th className="p-2.5">Observed vs Expected</th>
                  <th className="p-2.5">Severity</th>
                  <th className="p-2.5">Technical Explanation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/80">
                {dossier.discrepancies.map((d) => (
                  <tr key={d.discrepancyId} className="hover:bg-white/[0.02]">
                    <td className="p-2.5 font-bold text-white">{d.discrepancyId}</td>
                    <td className="p-2.5 text-white/60">{d.evidenceStreamA} ↔ {d.evidenceStreamB}</td>
                    <td className="p-2.5 text-white/90">{d.metric}</td>
                    <td className="p-2.5">
                      <div className="text-white/90">{d.observedDifference}</div>
                      <div className="text-[10px] text-white/40">{d.expectedTolerance}</div>
                    </td>
                    <td className="p-2.5">{getSeverityBadge(d.severity)}</td>
                    <td className="p-2.5 text-[11px] text-white/70 max-w-xs">{d.explanation}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5. Unified Normalized Chronological Timeline */}
      {dossier.timeline.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs font-bold text-white tracking-[0.15em] uppercase font-tech flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-red-500" />
            <span>NORMALIZED CHRONOLOGICAL TIMELINE</span>
          </div>

          <div className="overflow-x-auto border border-white/10 rounded">
            <table className="w-full text-left text-xs font-mono">
              <thead className="bg-white/5 border-b border-white/10 text-white/50 text-[10px] uppercase">
                <tr>
                  <th className="p-2.5">Time (UTC)</th>
                  <th className="p-2.5">Rel. Time</th>
                  <th className="p-2.5">Source</th>
                  <th className="p-2.5">Status</th>
                  <th className="p-2.5">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-white/80">
                {dossier.timeline.map((evt, idx) => (
                  <tr key={idx} className="hover:bg-white/[0.02]">
                    <td className="p-2.5 text-white/60">{evt.timestamp}</td>
                    <td className="p-2.5 text-amber-400 font-bold">
                      {evt.eventRelativeTimeSec > 0 ? `+${evt.eventRelativeTimeSec}s` : `${evt.eventRelativeTimeSec}s`}
                    </td>
                    <td className="p-2.5 text-white/90">{evt.source}</td>
                    <td className="p-2.5">{getStatusBadge(evt.evidenceStatus)}</td>
                    <td className="p-2.5 text-[11px] text-white/80">{evt.description}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 6. Raw Granular Evidence Items Accordion */}
      <div className="border border-white/10 rounded bg-[#121215]">
        <button
          onClick={() => setShowRawItems(!showRawItems)}
          className="w-full p-3 flex items-center justify-between text-xs font-mono text-white/70 hover:text-white transition-colors cursor-pointer"
        >
          <span className="flex items-center gap-2">
            <Activity className="w-3.5 h-3.5 text-red-500" />
            <span>INSPECT ALL CANONICAL EVIDENCE ITEMS ({dossier.evidenceItems.length})</span>
          </span>
          {showRawItems ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>

        {showRawItems && (
          <div className="p-3 border-t border-white/10 space-y-2 max-h-96 overflow-y-auto">
            {dossier.evidenceItems.map((item) => (
              <div key={item.evidenceId} className="p-2.5 bg-black/40 border border-white/5 rounded text-xs font-mono space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-white">{item.evidenceId}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] text-white/40">{item.evidenceType}</span>
                    {getStatusBadge(item.status)}
                  </div>
                </div>
                <div className="text-white/80 text-[11px]">{item.observation}</div>
                <div className="text-white/40 text-[10px] flex flex-wrap gap-x-4">
                  <span>Basis: {item.measurementBasis}</span>
                  <span>Provenance: {item.provenance}</span>
                  {item.parentEvidenceIds.length > 0 && (
                    <span>Parents: {item.parentEvidenceIds.join(', ')}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 7. Limitations Summary */}
      <div className="p-3 bg-white/[0.02] border border-white/10 rounded space-y-1 text-xs text-white/50 font-mono">
        <div className="text-[10px] uppercase font-bold text-white/40">Dossier Integrity Limitations:</div>
        <ul className="list-disc pl-4 space-y-0.5 text-[11px]">
          {dossier.limitations.map((lim, i) => (
            <li key={i}>{lim}</li>
          ))}
        </ul>
      </div>
    </div>
  );
};
