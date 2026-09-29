import React from 'react';
import { MLEvidence, FeatureContribution } from '../lib/types';
import { 
  Bot, 
  ShieldCheck, 
  AlertTriangle, 
  CheckCircle2, 
  BarChart3, 
  Sliders, 
  Layers, 
  Info, 
  HelpCircle 
} from 'lucide-react';

interface MLEvidencePanelProps {
  mlEvidence?: MLEvidence;
  driverA: string;
  driverB: string;
}

export const MLEvidencePanel: React.FC<MLEvidencePanelProps> = ({
  mlEvidence,
  driverA,
  driverB,
}) => {
  if (!mlEvidence) {
    return (
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 text-center">
        <div className="flex items-center justify-center gap-2 text-white/40 font-mono text-xs">
          <HelpCircle className="w-4 h-4" />
          <span>MACHINE LEARNING EVALUATION NOT COMPUTED FOR THIS CANDIDATE</span>
        </div>
      </div>
    );
  }

  const {
    candidateProbability,
    predictedLabel,
    decisionThreshold,
    classification,
    uncertaintyBand,
    topContributingFeatures,
    modelMetadata,
    limitations,
    stewardGuidance,
  } = mlEvidence;

  const probPercent = Math.round(candidateProbability * 1000) / 10;
  const isHighCandidate = predictedLabel === 1;

  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-sm bg-purple-600/20 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Bot className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
              <span>4D. MACHINE LEARNING CANDIDATE EVALUATION</span>
            </div>
            <div className="text-[10px] font-mono text-white/40">
              {modelMetadata.modelName} • {modelMetadata.modelFamily} • Feature {modelMetadata.featureVersion}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-sm">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Decision-Support Only • Zero Guilt Assessment</span>
        </div>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Probability Card */}
        <div className="bg-[#121215] border border-white/5 p-4 rounded-sm">
          <div className="text-[10px] text-white/40 uppercase tracking-widest font-mono">
            Candidate Likelihood
          </div>
          <div className="text-2xl font-mono font-bold text-white mt-1 flex items-baseline gap-1">
            <span>{probPercent.toFixed(1)}%</span>
            <span className="text-xs font-normal text-white/40">prob</span>
          </div>
          <div className="text-[10px] font-mono text-white/50 mt-1">
            Band: [{Math.round(uncertaintyBand[0] * 100)}% - {Math.round(uncertaintyBand[1] * 100)}%]
          </div>
        </div>

        {/* Classification State */}
        <div className="bg-[#121215] border border-white/5 p-4 rounded-sm">
          <div className="text-[10px] text-white/40 uppercase tracking-widest font-mono">
            Interaction Pattern
          </div>
          <div className="mt-2">
            <span
              className={`px-2 py-0.5 rounded-sm uppercase font-bold text-xs font-mono border tracking-wider inline-flex items-center gap-1.5 ${
                isHighCandidate
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
              }`}
            >
              {isHighCandidate ? (
                <AlertTriangle className="w-3 h-3 text-amber-400" />
              ) : (
                <CheckCircle2 className="w-3 h-3 text-cyan-400" />
              )}
              <span>{isHighCandidate ? 'INCIDENT CANDIDATE' : 'NOMINAL RACING'}</span>
            </span>
          </div>
          <div className="text-[10px] font-mono text-white/50 mt-2">
            Threshold: {decisionThreshold.toFixed(2)}
          </div>
        </div>

        {/* Validation Cohort */}
        <div className="bg-[#121215] border border-white/5 p-4 rounded-sm">
          <div className="text-[10px] text-white/40 uppercase tracking-widest font-mono">
            Training Cohort
          </div>
          <div className="text-sm font-mono font-bold text-white mt-2">
            {modelMetadata.datasetScope}
          </div>
          <div className="text-[10px] font-mono text-white/50 mt-1">
            N = {modelMetadata.trainingSampleCount} interactions • GroupKFold
          </div>
        </div>

        {/* Status */}
        <div className="bg-[#121215] border border-white/5 p-4 rounded-sm">
          <div className="text-[10px] text-white/40 uppercase tracking-widest font-mono">
            Readiness Status
          </div>
          <div className="text-xs font-mono font-bold text-cyan-400 mt-2 truncate" title={modelMetadata.validationStatus}>
            {modelMetadata.validationStatus || 'PROTOTYPE_READINESS'}
          </div>
          <div className="text-[10px] font-mono text-white/50 mt-1">
            Non-binding steward decision-support
          </div>
        </div>
      </div>

      {/* Top Contributing Features */}
      {topContributingFeatures && topContributingFeatures.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs font-mono text-white/60 uppercase tracking-wider flex items-center gap-2">
            <Sliders className="w-3.5 h-3.5 text-purple-400" />
            <span>Top Key Factor Directional Weights</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {topContributingFeatures.map((item: FeatureContribution, idx: number) => {
              const isIncrease = item.directionalImpact === 'INCREASES_CANDIDATE_LIKELIHOOD';
              return (
                <div
                  key={idx}
                  className="bg-[#121215] border border-white/5 p-3 rounded-sm flex items-start justify-between gap-3"
                >
                  <div className="space-y-1">
                    <div className="text-xs font-mono text-white font-semibold flex items-center gap-2">
                      <span>{item.featureName}</span>
                      <span className="text-[10px] text-white/40 font-normal">
                        ({item.featureValue})
                      </span>
                    </div>
                    <div className="text-[11px] text-white/60 font-sans">
                      {item.description}
                    </div>
                  </div>

                  <div className="text-right shrink-0">
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-sm border inline-block ${
                        isIncrease
                          ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                          : 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30'
                      }`}
                    >
                      {item.importanceWeight > 0 ? `+${item.importanceWeight}` : item.importanceWeight}
                    </span>
                    <div className="text-[9px] font-mono text-white/40 mt-1">
                      {isIncrease ? 'Increases Likelihood' : 'Decreases Likelihood'}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Model Limitations & Safeguards */}
      <div className="bg-[#121215] border border-white/5 p-4 rounded-sm space-y-2">
        <div className="text-[10px] font-mono text-white/60 uppercase tracking-wider flex items-center gap-1.5">
          <Info className="w-3.5 h-3.5 text-white/40" />
          <span>Methodological Constraints & Data Volume Notice</span>
        </div>
        <ul className="text-[11px] font-mono text-white/60 space-y-1 list-disc list-inside">
          {limitations.map((lim, i) => (
            <li key={i}>{lim}</li>
          ))}
        </ul>
      </div>

      {/* Steward Guidance Banner */}
      <div className="bg-purple-950/20 border border-purple-500/20 p-4 rounded-sm flex items-start gap-3">
        <ShieldCheck className="w-4 h-4 text-purple-400 shrink-0 mt-0.5" />
        <div className="text-xs font-mono text-purple-200/80 leading-relaxed">
          <span className="font-bold uppercase tracking-wider text-purple-300 mr-2">
            Steward Guidance:
          </span>
          {stewardGuidance}
        </div>
      </div>
    </div>
  );
};
