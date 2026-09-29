import React from 'react';
import { BaselineEvidence, SignalStatus } from '../lib/types';
import { 
  GitCompare, 
  ShieldCheck, 
  HelpCircle, 
  CheckCircle2, 
  AlertTriangle,
  ArrowRight
} from 'lucide-react';

interface ReferenceBaselinePanelProps {
  baseline?: BaselineEvidence;
  driverA: string;
  driverB: string;
}

export const ReferenceBaselinePanel: React.FC<ReferenceBaselinePanelProps> = ({
  baseline,
  driverA,
  driverB,
}) => {
  if (!baseline) {
    return (
      <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 text-center">
        <div className="flex items-center justify-center gap-2 text-white/40 font-mono text-xs">
          <HelpCircle className="w-4 h-4" />
          <span>REFERENCE-LAP BASELINE NOT COMPUTED FOR THIS INCIDENT</span>
        </div>
      </div>
    );
  }

  const isAvailable = baseline.status === 'AVAILABLE';

  const renderSignalBadge = (label: string, status: SignalStatus) => {
    let colorClasses = 'bg-white/5 text-white/50 border-white/10';
    if (status === 'OBSERVED') {
      colorClasses = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    } else if (status === 'DERIVED') {
      colorClasses = 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20';
    } else if (status === 'UNAVAILABLE') {
      colorClasses = 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    }

    return (
      <span
        key={label}
        className={`px-2 py-0.5 rounded-sm border text-[10px] font-mono uppercase inline-flex items-center gap-1 ${colorClasses}`}
      >
        <span>{label}:</span>
        <strong>{status}</strong>
      </span>
    );
  };

  return (
    <div className="bg-[#0d0d0f] border border-white/10 rounded-sm p-6 space-y-6">
      {/* Header & Status */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-sm bg-red-600/20 border border-red-600/40 flex items-center justify-center text-red-500">
            <GitCompare className="w-4 h-4" />
          </div>
          <div>
            <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech">
              4B. REFERENCE-LAP BASELINE & EVIDENCE QUANTIFICATION
            </div>
            <div className="text-[10px] font-mono text-white/40 mt-0.5">
              Multi-Lap Median Baseline Alignment • SI Grid Distance Domain (2.0m)
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`px-3 py-1 rounded-sm uppercase font-mono text-[11px] font-bold border inline-flex items-center gap-1.5 ${
              isAvailable
                ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                : 'bg-amber-500/10 text-amber-400 border-amber-500/30'
            }`}
          >
            {isAvailable ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                BASELINE QUANTIFIED
              </>
            ) : (
              <>
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                {baseline.status.replace(/_/g, ' ')}
              </>
            )}
          </span>
        </div>
      </div>

      {/* Steward Jurisprudential Notice */}
      <div className="bg-white/5 border-l-2 border-red-600 p-3.5 rounded-r-sm text-xs font-mono text-white/70 space-y-1">
        <div className="flex items-center gap-2 text-white font-semibold text-[11px] uppercase tracking-wider">
          <ShieldCheck className="w-3.5 h-3.5 text-red-500" />
          <span>NEUTRAL STEWARD REFERENCE GUIDANCE</span>
        </div>
        <p className="text-[11px] leading-relaxed text-white/60">
          {baseline.stewardGuidance}
        </p>
      </div>

      {/* Signal Provenance Catalog (Observed vs Derived vs Unavailable) */}
      <div className="space-y-2">
        <div className="text-[10px] font-mono uppercase tracking-widest text-white/40">
          Signal Channel Integrity & Provenance
        </div>
        <div className="flex flex-wrap gap-2">
          {renderSignalBadge('Speed', 'OBSERVED')}
          {renderSignalBadge('Throttle', 'OBSERVED')}
          {renderSignalBadge('Brake', 'OBSERVED')}
          {renderSignalBadge('Gear', 'OBSERVED')}
          {renderSignalBadge('Longitudinal Accel', 'DERIVED')}
          {renderSignalBadge('Trajectory Deviation', 'DERIVED')}
          {renderSignalBadge('Steering Angle', 'UNAVAILABLE')}
          {renderSignalBadge('Brake Pressure (bar)', 'UNAVAILABLE')}
          {renderSignalBadge('Curvilinear Lateral (d)', 'UNAVAILABLE')}
        </div>
      </div>

      {/* Per-Driver Quantified Comparison Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {[driverA, driverB].map((drvCode) => {
          const drvEv = baseline.drivers?.[drvCode];
          if (!drvEv) return null;

          const hasMetrics = drvEv.status === 'AVAILABLE' && drvEv.disruptionMetrics;
          const m = drvEv.disruptionMetrics;
          const t = drvEv.trajectoryMetrics;
          const prov = drvEv.provenance;

          return (
            <div
              key={drvCode}
              className="bg-[#0a0a0b] border border-white/10 rounded-sm p-4 space-y-4"
            >
              {/* Driver Header */}
              <div className="flex items-center justify-between border-b border-white/5 pb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xl font-bold text-white">
                    {drvCode}
                  </span>
                  <span className="text-[10px] font-mono text-white/40">
                    REFERENCE PROFILE
                  </span>
                </div>
                <span
                  className={`text-[10px] font-mono px-2 py-0.5 rounded-sm border ${
                    drvEv.status === 'AVAILABLE'
                      ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
                      : 'bg-white/5 text-white/40 border-white/10'
                  }`}
                >
                  {drvEv.status}
                </span>
              </div>

              {/* Provenance Details */}
              <div className="text-[10px] font-mono text-white/50 space-y-1">
                <div>
                  <span className="text-white/30">REFERENCE LAPS USED: </span>
                  <strong className="text-white/80">
                    {prov.referenceLapsUsed && prov.referenceLapsUsed.length > 0
                      ? `Laps [${prov.referenceLapsUsed.join(', ')}]`
                      : 'None available'}
                  </strong>
                  <span className="text-white/30 ml-2">
                    ({prov.totalLapsAnalyzed} total laps analyzed)
                  </span>
                </div>
                <div>
                  <span className="text-white/30">METHOD: </span>
                  <span className="text-white/70">{prov.aggregationMethod}</span>
                </div>
              </div>

              {hasMetrics && m ? (
                <>
                  {/* Trajectory Deviation Metrics */}
                  {t && (
                    <div className="bg-white/5 border border-white/5 rounded-sm p-3 space-y-2">
                      <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider flex items-center justify-between">
                        <span>2D Cartesian Trajectory Deviation</span>
                        <span className="text-cyan-400">DERIVED (SI METERS)</span>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-center">
                        <div className="bg-[#0d0d0f] p-2 rounded-sm">
                          <div className="text-[9px] font-mono text-white/40">MAX DEVIATION</div>
                          <div className="font-mono text-base font-bold text-white">
                            {t.maxTrajectoryDeviationM.toFixed(2)}m
                          </div>
                        </div>
                        <div className="bg-[#0d0d0f] p-2 rounded-sm">
                          <div className="text-[9px] font-mono text-white/40">APEX DEVIATION</div>
                          <div className="font-mono text-base font-bold text-yellow-400">
                            {t.deviationAtApexM !== undefined && t.deviationAtApexM !== null
                              ? `${t.deviationAtApexM.toFixed(2)}m`
                              : 'N/A'}
                          </div>
                        </div>
                        <div className="bg-[#0d0d0f] p-2 rounded-sm">
                          <div className="text-[9px] font-mono text-white/40">MEAN DEVIATION</div>
                          <div className="font-mono text-base font-bold text-white/70">
                            {t.meanTrajectoryDeviationM.toFixed(2)}m
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Input Disruption Metrics */}
                  <div className="bg-white/5 border border-white/5 rounded-sm p-3 space-y-2">
                    <div className="text-[10px] font-mono text-white/40 uppercase tracking-wider">
                      Control Input & Apex Kinematics vs Baseline
                    </div>
                    <div className="grid grid-cols-2 gap-2">
                      <div className="bg-[#0d0d0f] p-2 rounded-sm">
                        <div className="text-[9px] font-mono text-white/40">APEX SPEED DELTA</div>
                        <div className="font-mono text-sm font-bold text-white flex items-center gap-1">
                          <span>
                            {m.minCornerSpeedDeltaKmh !== undefined
                              ? `${m.minCornerSpeedDeltaKmh > 0 ? '+' : ''}${m.minCornerSpeedDeltaKmh.toFixed(1)} km/h`
                              : 'N/A'}
                          </span>
                          <span className="text-[10px] font-normal text-white/40">
                            ({m.speedAtApexIncidentKmh?.toFixed(0)} vs {m.speedAtApexBaselineKmh?.toFixed(0)})
                          </span>
                        </div>
                      </div>

                      <div className="bg-[#0d0d0f] p-2 rounded-sm">
                        <div className="text-[9px] font-mono text-white/40">BRAKING ONSET DELTA</div>
                        <div className="font-mono text-sm font-bold text-white">
                          {m.brakingOnsetDeltaM !== undefined
                            ? `${m.brakingOnsetDeltaM > 0 ? '+' : ''}${m.brakingOnsetDeltaM.toFixed(1)}m`
                            : 'N/A'}
                          {m.brakingOnsetDeltaSec !== undefined && (
                            <span className="text-[10px] font-normal text-white/40 ml-1">
                              ({m.brakingOnsetDeltaSec > 0 ? '+' : ''}{m.brakingOnsetDeltaSec.toFixed(2)}s)
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="bg-[#0d0d0f] p-2 rounded-sm">
                        <div className="text-[9px] font-mono text-white/40">THROTTLE REAPPL. DELAY</div>
                        <div className="font-mono text-sm font-bold text-white">
                          {m.throttleReapplicationDelayM !== undefined
                            ? `${m.throttleReapplicationDelayM > 0 ? '+' : ''}${m.throttleReapplicationDelayM.toFixed(1)}m`
                            : 'N/A'}
                          {m.throttleReapplicationDelaySec !== undefined && (
                            <span className="text-[10px] font-normal text-white/40 ml-1">
                              ({m.throttleReapplicationDelaySec > 0 ? '+' : ''}{m.throttleReapplicationDelaySec.toFixed(2)}s)
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="bg-[#0d0d0f] p-2 rounded-sm">
                        <div className="text-[9px] font-mono text-white/40">PEAK BRAKE DELTA</div>
                        <div className="font-mono text-sm font-bold text-white">
                          {m.peakBrakePctDelta !== undefined
                            ? `${m.peakBrakePctDelta > 0 ? '+' : ''}${m.peakBrakePctDelta.toFixed(1)}%`
                            : 'N/A'}
                        </div>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <div className="bg-white/5 border border-white/5 rounded-sm p-4 text-xs font-mono text-white/40 space-y-2">
                  <div className="flex items-center gap-1.5 text-amber-400 font-semibold">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>INSUFFICIENT CLEAN REFERENCE LAPS</span>
                  </div>
                  <p className="text-[11px] text-white/60">
                    Fewer than 2 valid, non-anomalous reference laps were found for {drvCode} in this session window.
                  </p>
                  {drvEv.notes && drvEv.notes.length > 0 && (
                    <ul className="list-disc list-inside text-[10px] text-white/40 space-y-0.5">
                      {drvEv.notes.map((note, idx) => (
                        <li key={idx}>{note}</li>
                      ))}
                    </ul>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary Footnote */}
      {baseline.summary && (
        <div className="text-[11px] font-mono text-white/50 border-t border-white/5 pt-3 flex items-start gap-2">
          <ArrowRight className="w-3.5 h-3.5 text-red-500 shrink-0 mt-0.5" />
          <span>{baseline.summary}</span>
        </div>
      )}
    </div>
  );
};
