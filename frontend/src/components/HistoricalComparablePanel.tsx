import React, { useState } from 'react';
import {
  History,
  ShieldAlert,
  ChevronDown,
  ChevronUp,
  FileText,
  ExternalLink,
  Layers,
  SlidersHorizontal,
  X,
  ArrowRight,
  Info,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import {
  HistoricalComparisonResponse,
  ComparableIncidentResult,
  RelevanceGrade,
  DataQualityRating,
  SideBySideComparison
} from '../lib/types';

interface HistoricalComparablePanelProps {
  comparisonData?: HistoricalComparisonResponse | null;
  incidentId: string;
}

export const HistoricalComparablePanel: React.FC<HistoricalComparablePanelProps> = ({
  comparisonData,
  incidentId
}) => {
  const [selectedCaseForModal, setSelectedCaseForModal] = useState<ComparableIncidentResult | null>(null);
  const [expandedDetails, setExpandedDetails] = useState<Record<string, boolean>>({});
  const [filterMinSimilarity, setFilterMinSimilarity] = useState<number>(0.0);

  if (!comparisonData || comparisonData.comparableCases.length === 0) {
    return (
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 text-white font-mono">
        <div className="flex items-center gap-2 text-xs font-bold text-white tracking-[0.2em] uppercase font-tech mb-2">
          <History className="w-4 h-4 text-red-500" />
          <span>4F. HISTORICAL COMPARABLE-CASE INTELLIGENCE</span>
        </div>
        <p className="text-xs text-white/50">
          No historical comparators available for incident #{incidentId.replace('INC-', '')}.
        </p>
      </div>
    );
  }

  const toggleExpand = (caseId: string) => {
    setExpandedDetails((prev) => ({
      ...prev,
      [caseId]: !prev[caseId]
    }));
  };

  const getRelevanceGradeBadge = (grade: RelevanceGrade) => {
    switch (grade) {
      case 'HIGHLY_COMPARABLE':
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 font-semibold inline-flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3" /> HIGHLY COMPARABLE
          </span>
        );
      case 'PARTIALLY_COMPARABLE':
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-amber-500/15 text-amber-400 border border-amber-500/30 font-semibold inline-flex items-center gap-1">
            <AlertCircle className="w-3 h-3" /> PARTIALLY COMPARABLE
          </span>
        );
      case 'NOT_COMPARABLE':
      default:
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-zinc-500/15 text-zinc-400 border border-zinc-500/30 font-semibold">
            NOT COMPARABLE
          </span>
        );
    }
  };

  const getDataQualityBadge = (quality: DataQualityRating) => {
    switch (quality) {
      case 'FULL':
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-blue-500/15 text-blue-400 border border-blue-500/30">
            DATA: FULL (TEL+VID)
          </span>
        );
      case 'PARTIAL':
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-cyan-500/15 text-cyan-400 border border-cyan-500/30">
            DATA: PARTIAL (TEL)
          </span>
        );
      case 'LIMITED':
      default:
        return (
          <span className="px-2 py-0.5 text-[10px] font-mono rounded bg-zinc-500/15 text-zinc-400 border border-zinc-500/30">
            DATA: LIMITED
          </span>
        );
    }
  };

  const filteredCases = comparisonData.comparableCases.filter(
    (c) => c.observableSimilarityScore >= filterMinSimilarity
  );

  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 text-white space-y-6">
      {/* 1. Header & Summary */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-sm bg-red-600/20 border border-red-600/40 flex items-center justify-center text-red-500">
              <History className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech">
                4F. EXPLAINABLE HISTORICAL COMPARABLE-CASE INTELLIGENCE
              </div>
              <div className="text-[10px] font-mono text-white/40">
                Observable Kinematic Match • Query: {comparisonData.queryCaseId} • Evaluated: {comparisonData.totalCasesEvaluated} benchmark cases
              </div>
            </div>
          </div>
        </div>

        {/* Filter controls */}
        <div className="flex items-center gap-3">
          <label className="text-[10px] font-mono text-white/50 flex items-center gap-1.5">
            <SlidersHorizontal className="w-3.5 h-3.5" />
            Min Similarity:
            <select
              value={filterMinSimilarity}
              onChange={(e) => setFilterMinSimilarity(parseFloat(e.target.value))}
              className="bg-black/40 border border-white/10 text-white text-[10px] px-2 py-1 rounded outline-none font-mono"
            >
              <option value={0.0}>All (0%)</option>
              <option value={0.5}>&ge; 50% (Partially Comparable)</option>
              <option value={0.75}>&ge; 75% (Highly Comparable)</option>
            </select>
          </label>
        </div>
      </div>

      {/* 2. Critical Non-Adjudicative Epistemic Notice */}
      <div className="p-3.5 rounded-sm bg-amber-500/10 border border-amber-500/20 flex items-start gap-3 text-xs leading-relaxed">
        <ShieldAlert className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
        <div className="space-y-1">
          <div className="font-mono text-[11px] font-semibold text-amber-300 uppercase tracking-wide">
            Strict Non-Adjudicative Steward Decision Support Doctrine
          </div>
          <p className="text-white/80 font-mono text-[11px]">
            {comparisonData.nonAdjudicationStatement}
          </p>
        </div>
      </div>

      {/* 3. Comparable Cases List */}
      <div className="space-y-4">
        {filteredCases.map((cand) => {
          const isExpanded = !!expandedDetails[cand.caseId];
          const simPct = Math.round(cand.observableSimilarityScore * 100);

          return (
            <div
              key={cand.caseId}
              className="bg-[#0a0a0b] border border-white/10 rounded-sm p-4 hover:border-white/20 transition-colors space-y-4"
            >
              {/* Card Header */}
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono font-bold text-sm text-white">
                      {cand.caseId}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-white/70">
                      {cand.event} {cand.season}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/5 border border-white/10 text-white/70">
                      {cand.corner}
                    </span>
                    {getRelevanceGradeBadge(cand.relevanceGrade)}
                    {getDataQualityBadge(cand.dataQuality)}
                  </div>
                  <div className="text-xs font-mono text-white/60">
                    Participants: <strong className="text-white">{cand.drivers.join(' vs ')}</strong> • Circuit: {cand.circuit} ({cand.session})
                  </div>
                </div>

                {/* Similarity Score Metric */}
                <div className="flex items-center gap-4 shrink-0">
                  <div className="text-right">
                    <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider">
                      Kinematic Similarity
                    </div>
                    <div className="text-2xl font-mono font-light text-white leading-none">
                      {simPct}<span className="text-xs text-white/40">%</span>
                    </div>
                  </div>
                  <div className="w-24 bg-white/5 rounded-full h-2 overflow-hidden border border-white/10">
                    <div
                      className={`h-full rounded-full ${
                        simPct >= 78 ? 'bg-emerald-500' : simPct >= 50 ? 'bg-amber-500' : 'bg-zinc-500'
                      }`}
                      style={{ width: `${simPct}%` }}
                    />
                  </div>
                </div>
              </div>

              {/* Dimension Availability & Evidence Badges */}
              <div className="flex flex-wrap items-center gap-2 pt-1 border-t border-white/5 text-[10px] font-mono">
                <span className="text-white/40 uppercase mr-1">Evidence Streams:</span>
                <span className={`px-2 py-0.5 rounded border ${
                  cand.evidenceAvailability?.telemetry === 'AVAILABLE'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                }`}>
                  CAN-bus: {cand.evidenceAvailability?.telemetry || 'AVAILABLE'}
                </span>
                <span className={`px-2 py-0.5 rounded border ${
                  cand.evidenceAvailability?.video === 'AVAILABLE'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                }`}>
                  Video/CV: {cand.evidenceAvailability?.video || 'UNAVAILABLE'}
                </span>
                <span className={`px-2 py-0.5 rounded border ${
                  cand.evidenceAvailability?.regulation === 'AVAILABLE'
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                    : 'bg-zinc-500/10 text-zinc-400 border-zinc-500/20'
                }`}>
                  FIA Code: {cand.evidenceAvailability?.regulation || 'AVAILABLE'}
                </span>

                <div className="ml-auto flex items-center gap-2">
                  <button
                    onClick={() => setSelectedCaseForModal(cand)}
                    className="px-3 py-1 bg-red-600/20 hover:bg-red-600/30 text-red-400 border border-red-600/30 hover:border-red-600/50 rounded text-xs font-mono transition-colors flex items-center gap-1.5 cursor-pointer"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>View Side-by-Side</span>
                  </button>

                  <button
                    onClick={() => toggleExpand(cand.caseId)}
                    className="px-2.5 py-1 bg-white/5 hover:bg-white/10 text-white/70 hover:text-white border border-white/10 rounded text-xs font-mono transition-colors flex items-center gap-1 cursor-pointer"
                  >
                    <span>{isExpanded ? 'Less' : 'Explain'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Expandable Explanation Details */}
              {isExpanded && (
                <div className="pt-3 border-t border-white/10 space-y-3 font-mono text-xs">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* Why Comparable */}
                    <div className="p-3 bg-emerald-500/5 border border-emerald-500/15 rounded space-y-1.5">
                      <div className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
                        <CheckCircle2 className="w-3 h-3" />
                        Why Comparable (Observable Matches)
                      </div>
                      <ul className="list-disc list-inside space-y-1 text-white/80 text-[11px]">
                        {cand.matchedFeatures && cand.matchedFeatures.length > 0 ? (
                          cand.matchedFeatures.map((m, idx) => <li key={idx}>{m}</li>)
                        ) : (
                          <li className="text-white/40">General corner profile match.</li>
                        )}
                      </ul>
                    </div>

                    {/* Key Differences */}
                    <div className="p-3 bg-zinc-500/5 border border-white/10 rounded space-y-1.5">
                      <div className="text-[11px] font-bold text-zinc-400 uppercase tracking-wider flex items-center gap-1">
                        <AlertCircle className="w-3 h-3" />
                        Key Differences
                      </div>
                      <ul className="list-disc list-inside space-y-1 text-white/70 text-[11px]">
                        {cand.unmatchedFeatures && cand.unmatchedFeatures.length > 0 ? (
                          cand.unmatchedFeatures.map((u, idx) => <li key={idx}>{u}</li>)
                        ) : (
                          <li className="text-white/40">No significant observable deviations.</li>
                        )}
                      </ul>
                    </div>
                  </div>

                  {/* Official FIA Document References */}
                  {cand.officialSources && cand.officialSources.length > 0 && (
                    <div className="p-3 bg-white/5 border border-white/10 rounded space-y-2">
                      <div className="text-[11px] font-bold text-white/80 uppercase tracking-wider flex items-center gap-1.5">
                        <FileText className="w-3.5 h-3.5 text-red-500" />
                        Canonical Documentary Reference (Non-Adjudicative Context)
                      </div>
                      {cand.officialSources.map((source, sIdx) => (
                        <div key={sIdx} className="text-[11px] text-white/70 space-y-1">
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-white">{source.documentTitle}</span>
                            <span className="text-white/40 font-mono">({source.documentIdentifier})</span>
                            <span className="px-1.5 py-0.5 rounded bg-white/10 text-white/60 text-[9px] uppercase">
                              {source.decisionType}
                            </span>
                          </div>
                          <p className="text-white/60 text-[10px] leading-relaxed">
                            Summary: "{source.decisionSummary}"
                          </p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* 4. Side-by-Side Modal / Drawer */}
      {selectedCaseForModal && selectedCaseForModal.sideBySide && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0f0f12] border border-white/20 rounded-md max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden font-mono">
            {/* Modal Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/40">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-sm bg-red-600/20 border border-red-600/40 flex items-center justify-center text-red-500">
                  <Layers className="w-4 h-4" />
                </div>
                <div>
                  <div className="text-xs font-bold text-white tracking-wider uppercase font-tech">
                    Side-by-Side Evidence Analysis
                  </div>
                  <div className="text-[10px] text-white/40">
                    Current Incident ({incidentId}) vs Historical Case ({selectedCaseForModal.caseId})
                  </div>
                </div>
              </div>
              <button
                onClick={() => setSelectedCaseForModal(null)}
                className="p-1.5 rounded-sm hover:bg-white/10 text-white/60 hover:text-white transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-4">
              <div className="p-3 rounded bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300 leading-relaxed">
                <strong>Measurement Uncertainty Notice:</strong> All physical metrics reflect sensor and GPS/CAN-bus
                precision boundaries. Differences within uncertainty bounds must not be treated as definitive distinctions.
              </div>

              {/* Comparison Table */}
              <div className="overflow-x-auto border border-white/10 rounded">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-white/5 border-b border-white/10 text-white/60 text-[10px] uppercase">
                    <tr>
                      <th className="py-2.5 px-3">Observable Metric</th>
                      <th className="py-2.5 px-3">Current Incident</th>
                      <th className="py-2.5 px-3">Historical Incident</th>
                      <th className="py-2.5 px-3">Difference</th>
                      <th className="py-2.5 px-3">Uncertainty</th>
                      <th className="py-2.5 px-3">Evidence Source</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5 text-white/80 text-[11px]">
                    {selectedCaseForModal.sideBySide.metrics.map((row, rIdx) => (
                      <tr key={rIdx} className="hover:bg-white/[0.02]">
                        <td className="py-2.5 px-3 font-semibold text-white">
                          {row.metric}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-emerald-400">
                          {row.currentValue}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-blue-400">
                          {row.historicalValue}
                        </td>
                        <td className="py-2.5 px-3 font-mono font-medium text-amber-300">
                          {row.difference}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-white/40 text-[10px]">
                          {row.uncertainty}
                        </td>
                        <td className="py-2.5 px-3 text-white/50 text-[10px]">
                          <span className="px-1.5 py-0.5 rounded bg-white/5 border border-white/10">
                            {row.sourceType}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-white/10 bg-black/40 flex items-center justify-between text-xs text-white/50 font-mono">
              <span>Historical similarity: {Math.round(selectedCaseForModal.observableSimilarityScore * 100)}%</span>
              <button
                onClick={() => setSelectedCaseForModal(null)}
                className="px-4 py-1.5 bg-white/10 hover:bg-white/20 text-white rounded text-xs font-mono transition-colors cursor-pointer"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
