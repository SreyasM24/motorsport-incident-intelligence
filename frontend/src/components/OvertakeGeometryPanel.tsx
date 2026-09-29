import React from 'react';
import { 
  OvertakeGeometryEvidence, 
  OverlapClassification, 
  ExitClearanceClassification,
  MeasurementConfidence 
} from '../lib/types';
import { 
  Maximize2, 
  ShieldCheck, 
  HelpCircle, 
  CheckCircle2, 
  AlertTriangle, 
  Compass, 
  Gauge, 
  Car,
  Layers,
  ArrowRight,
  Info
} from 'lucide-react';

interface OvertakeGeometryPanelProps {
  overtakeGeometry?: OvertakeGeometryEvidence;
  driverA: string;
  driverB: string;
}

export const OvertakeGeometryPanel: React.FC<OvertakeGeometryPanelProps> = ({
  overtakeGeometry,
  driverA,
  driverB,
}) => {
  if (!overtakeGeometry) {
    return (
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 text-center">
        <div className="flex items-center justify-center gap-2 text-white/40 font-mono text-xs">
          <HelpCircle className="w-4 h-4" />
          <span>CORNERING OVERTAKE GEOMETRY NOT COMPUTED FOR THIS INCIDENT</span>
        </div>
      </div>
    );
  }

  const {
    driverIncident,
    driverOther,
    turn,
    cornerPhases,
    apexSnapshot,
    exitClearance,
    phaseSnapshots,
    overlapClassification,
    overlapPercent,
    frontAxleOverlapPercent,
    fiaReference,
    dataQuality,
    summary,
    stewardGuidance
  } = overtakeGeometry;

  // Format overlap badge
  const getOverlapBadgeClasses = (classification: OverlapClassification) => {
    switch (classification) {
      case 'GREATER_THAN_50_PERCENT_OVERLAP':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'APPROXIMATELY_50_PERCENT_OVERLAP':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'PARTIAL_OVERLAP':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      case 'NO_MEASURABLE_OVERLAP':
        return 'bg-red-500/10 text-red-400 border-red-500/30';
      default:
        return 'bg-white/10 text-white/50 border-white/20';
    }
  };

  // Format exit clearance badge
  const getClearanceBadgeClasses = (classification: ExitClearanceClassification) => {
    switch (classification) {
      case 'CLEARANCE_ABOVE_REFERENCE':
        return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
      case 'CLEARANCE_NEAR_REFERENCE':
        return 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30';
      case 'CLEARANCE_BELOW_REFERENCE':
        return 'bg-amber-500/10 text-amber-400 border-amber-500/30';
      default:
        return 'bg-white/10 text-white/40 border-white/10';
    }
  };

  const formatClassificationLabel = (text: string) => {
    return text.replace(/_/g, ' ');
  };

  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 space-y-6">
      {/* 1. Header & High-Level Classification */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-sm bg-cyan-600/20 border border-cyan-600/40 flex items-center justify-center text-cyan-400">
            <Compass className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech">
              4C. CORNERING OVERTAKE GEOMETRY & APEX OVERLAP ANALYSIS
            </div>
            <div className="text-[10px] font-mono text-white/40 mt-0.5">
              Empirical Spatial Relationship • {turn} • {driverIncident} vs {driverOther}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <span
            className={`px-3 py-1 rounded-sm uppercase font-mono text-[11px] font-bold border inline-flex items-center gap-1.5 ${getOverlapBadgeClasses(
              overlapClassification
            )}`}
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            {formatClassificationLabel(overlapClassification)}
          </span>
        </div>
      </div>

      {/* 2. Steward Jurisprudential Notice */}
      <div className="bg-white/5 border-l-2 border-cyan-500 p-3.5 rounded-r-sm text-xs font-mono text-white/70 space-y-1">
        <div className="flex items-center gap-2 text-white font-semibold text-[11px] uppercase tracking-wider">
          <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
          <span>MEASURABLE GEOMETRIC EVIDENCE ONLY — STEWARD GUIDELINES ALIGNMENT</span>
        </div>
        <p className="leading-relaxed text-[11px] text-white/60">
          {stewardGuidance || (
            "This module quantifies objective physical positions, overlap percentages, and spatial room afforded relative to " +
            "engineering reference dimensions (5.63m car length, 2.00m car width) and FIA Driving Standards Guidelines. " +
            "It does NOT assign guilt, fault, or penalties."
          )}
        </p>
      </div>

      {/* 3. Core Geometric Snapshot Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Card 1: Apex Longitudinal Overlap */}
        <div className="bg-white/[0.02] border border-white/10 rounded-sm p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-white/5 pb-2">
            <span className="text-[10px] font-mono text-white/50 uppercase tracking-wider flex items-center gap-1.5">
              <Car className="w-3 h-3 text-cyan-400" />
              Apex Longitudinal Overlap
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-white/60">
              Ref 5.63m
            </span>
          </div>

          <div className="space-y-1">
            <div className="text-2xl font-bold font-mono text-white tracking-tight">
              {overlapPercent !== null && overlapPercent !== undefined ? `${overlapPercent.toFixed(1)}%` : 'N/A'}
            </div>
            <div className="text-[11px] font-mono text-cyan-400 uppercase font-semibold">
              {formatClassificationLabel(overlapClassification)}
            </div>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-white/5 text-[10px] font-mono text-white/60">
            <div className="flex justify-between">
              <span>Longitudinal Delta (Δs):</span>
              <span className="text-white font-semibold">
                {apexSnapshot.longitudinalGapM > 0 ? `+${apexSnapshot.longitudinalGapM.toFixed(2)}m` : `${apexSnapshot.longitudinalGapM.toFixed(2)}m`}
              </span>
            </div>
            {apexSnapshot.frontAxleGapM !== null && apexSnapshot.frontAxleGapM !== undefined && (
              <div className="flex justify-between">
                <span>Front Axle Gap:</span>
                <span className="text-white font-semibold">{apexSnapshot.frontAxleGapM.toFixed(2)}m</span>
              </div>
            )}
            {apexSnapshot.mirrorReferenceOverlapPercent !== null && apexSnapshot.mirrorReferenceOverlapPercent !== undefined && (
              <div className="flex justify-between">
                <span>Mirror Ref Overlap:</span>
                <span className="text-white font-semibold">{apexSnapshot.mirrorReferenceOverlapPercent.toFixed(1)}%</span>
              </div>
            )}
            <div className="flex justify-between">
              <span>Position at Apex:</span>
              <span className="text-cyan-400 font-semibold">{apexSnapshot.relativePosition}</span>
            </div>
          </div>
        </div>

        {/* Card 2: Corner Exit Lateral Room */}
        <div className="bg-white/[0.02] border border-white/10 rounded-sm p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-white/5 pb-2">
            <span className="text-[10px] font-mono text-white/50 uppercase tracking-wider flex items-center gap-1.5">
              <Maximize2 className="w-3 h-3 text-cyan-400" />
              Exit Lateral Clearance
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-white/60">
              Ref 2.00m
            </span>
          </div>

          <div className="space-y-1">
            <div className="text-2xl font-bold font-mono text-white tracking-tight">
              {exitClearance.measuredClearanceM !== null && exitClearance.measuredClearanceM !== undefined
                ? `${exitClearance.measuredClearanceM.toFixed(2)}m`
                : 'N/A'}
            </div>
            <div className="text-[11px] font-mono text-white/80 uppercase font-semibold">
              <span
                className={`px-2 py-0.5 rounded border text-[10px] ${getClearanceBadgeClasses(
                  exitClearance.clearanceClassification
                )}`}
              >
                {formatClassificationLabel(exitClearance.clearanceClassification)}
              </span>
            </div>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-white/5 text-[10px] font-mono text-white/60">
            <div className="flex justify-between">
              <span>Car Width Baseline:</span>
              <span className="text-white font-semibold">2.00m</span>
            </div>
            {exitClearance.exitDistanceM !== null && exitClearance.exitDistanceM !== undefined && (
              <div className="flex justify-between">
                <span>Exit Location (s):</span>
                <span className="text-white font-semibold">{exitClearance.exitDistanceM.toFixed(1)}m</span>
              </div>
            )}
            <div className="flex justify-between">
              <span>Sensor Provenance:</span>
              <span className="text-white/60 font-semibold">{exitClearance.confidence}</span>
            </div>
            <div className="text-[9px] text-white/40 leading-normal pt-1">
              {exitClearance.note}
            </div>
          </div>
        </div>

        {/* Card 3: Corner Phase Landmarks */}
        <div className="bg-white/[0.02] border border-white/10 rounded-sm p-4 space-y-3">
          <div className="flex items-center justify-between border-b border-white/5 pb-2">
            <span className="text-[10px] font-mono text-white/50 uppercase tracking-wider flex items-center gap-1.5">
              <Gauge className="w-3 h-3 text-cyan-400" />
              Corner Phase Landmarks
            </span>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-white/5 text-white/60">
              Kinematics
            </span>
          </div>

          <div className="space-y-1">
            <div className="text-2xl font-bold font-mono text-white tracking-tight">
              {cornerPhases.apexSpeedKmh.toFixed(0)} <span className="text-xs font-normal text-white/50">km/h</span>
            </div>
            <div className="text-[11px] font-mono text-white/60">
              Min Corner Speed (Apex Landmark)
            </div>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-white/5 text-[10px] font-mono text-white/60">
            <div className="flex justify-between">
              <span>Entry Point (s):</span>
              <span className="text-white font-semibold">{cornerPhases.cornerEntryDistanceM.toFixed(1)}m</span>
            </div>
            <div className="flex justify-between">
              <span>Apex Point (s):</span>
              <span className="text-white font-semibold">{cornerPhases.apexDistanceM.toFixed(1)}m</span>
            </div>
            {cornerPhases.cornerExitDistanceM !== null && cornerPhases.cornerExitDistanceM !== undefined && (
              <div className="flex justify-between">
                <span>Exit Point (s):</span>
                <span className="text-white font-semibold">{cornerPhases.cornerExitDistanceM.toFixed(1)}m</span>
              </div>
            )}
            <div className="flex justify-between">
              <span>Exit Status:</span>
              <span className="text-cyan-400 font-semibold">{cornerPhases.exitDetectionStatus}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 4. Phase Progression Timeline Table */}
      {phaseSnapshots && phaseSnapshots.length > 0 && (
        <div className="space-y-3">
          <div className="text-xs font-bold text-white tracking-[0.15em] uppercase font-tech flex items-center gap-2">
            <Layers className="w-3.5 h-3.5 text-cyan-400" />
            CORNER MILESTONE PROGRESSION SNAPSHOTS
          </div>

          <div className="overflow-x-auto border border-white/10 rounded-sm">
            <table className="w-full text-left font-mono text-xs">
              <thead className="bg-white/5 text-white/60 text-[10px] uppercase border-b border-white/10">
                <tr>
                  <th className="py-2.5 px-3">Corner Phase</th>
                  <th className="py-2.5 px-3">Track Dist (m)</th>
                  <th className="py-2.5 px-3">Δs (m)</th>
                  <th className="py-2.5 px-3">{driverIncident} Spd</th>
                  <th className="py-2.5 px-3">{driverOther} Spd</th>
                  <th className="py-2.5 px-3">Relative Pos</th>
                  <th className="py-2.5 px-3">Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5 text-[11px]">
                {phaseSnapshots.map((snap, idx) => {
                  const isApex = snap.phaseName === 'APEX';
                  return (
                    <tr
                      key={idx}
                      className={isApex ? 'bg-cyan-950/20 font-semibold text-white' : 'hover:bg-white/[0.02] text-white/80'}
                    >
                      <td className="py-2.5 px-3 flex items-center gap-1.5">
                        {isApex && <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 inline-block" />}
                        <span className={isApex ? 'text-cyan-400' : ''}>{snap.phaseName}</span>
                      </td>
                      <td className="py-2.5 px-3 text-white/60">
                        {snap.distanceIncidentM.toFixed(1)}m
                      </td>
                      <td className="py-2.5 px-3 font-mono">
                        <span
                          className={
                            snap.deltaSM > 0.5
                              ? 'text-emerald-400'
                              : snap.deltaSM < -0.5
                              ? 'text-amber-400'
                              : 'text-cyan-400'
                          }
                        >
                          {snap.deltaSM > 0 ? `+${snap.deltaSM.toFixed(2)}` : snap.deltaSM.toFixed(2)}m
                        </span>
                      </td>
                      <td className="py-2.5 px-3">{snap.speedIncidentKmh.toFixed(0)} km/h</td>
                      <td className="py-2.5 px-3">{snap.speedOtherKmh.toFixed(0)} km/h</td>
                      <td className="py-2.5 px-3">
                        <span className="px-1.5 py-0.5 rounded bg-white/5 text-[10px] text-white/70">
                          {snap.relativePosition}
                        </span>
                      </td>
                      <td className="py-2.5 px-3 text-[10px] text-white/40">
                        {snap.confidence}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5. FIA Reference & Data Integrity Footer */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
        {/* FIA Guidelines Reference */}
        <div className="bg-white/[0.02] border border-white/5 rounded-sm p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-white/70 font-semibold text-[11px] uppercase tracking-wider font-tech">
            <Info className="w-3.5 h-3.5 text-cyan-400" />
            <span>FIA Normative Reference Standards</span>
          </div>
          <div className="text-[10px] font-mono text-white/60 space-y-1">
            <div>
              <span className="text-white/40">Rule Source:</span> {fiaReference.ruleSource} ({fiaReference.ruleVersionOrDate})
            </div>
            <div>
              <span className="text-white/40">Reference:</span> {fiaReference.ruleReference}
            </div>
            <div className="text-white/50 text-[9px] pt-1 leading-relaxed">
              {fiaReference.stewardDiscretionStatement}
            </div>
          </div>
        </div>

        {/* Data Quality & Limitations */}
        <div className="bg-white/[0.02] border border-white/5 rounded-sm p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-white/70 font-semibold text-[11px] uppercase tracking-wider font-tech">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span>Geometric Data Quality Indicators</span>
          </div>
          <div className="flex flex-wrap gap-1.5 text-[10px] font-mono">
            <span
              className={`px-2 py-0.5 rounded-sm border ${
                dataQuality.synchronizedTimestamps
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              }`}
            >
              Sync: {dataQuality.synchronizedTimestamps ? 'VALID' : 'UNSYNCHRONIZED'}
            </span>
            <span
              className={`px-2 py-0.5 rounded-sm border ${
                dataQuality.distanceMonotonic
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-amber-500/10 text-amber-400 border-amber-500/20'
              }`}
            >
              Track Dist: {dataQuality.distanceMonotonic ? 'MONOTONIC' : 'NON-MONOTONIC'}
            </span>
            <span
              className={`px-2 py-0.5 rounded-sm border ${
                !dataQuality.missingTelemetry
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                  : 'bg-red-500/10 text-red-400 border-red-500/20'
              }`}
            >
              Telemetry: {!dataQuality.missingTelemetry ? 'COMPLETE' : 'GAPS_PRESENT'}
            </span>
          </div>
          {dataQuality.limitations && dataQuality.limitations.length > 0 && (
            <div className="text-[9px] font-mono text-amber-400/80 pt-1">
              Note: {dataQuality.limitations.join('; ')}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
