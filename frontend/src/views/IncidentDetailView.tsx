import React, { useState, useEffect } from 'react';
import { TelemetryChart } from '../components/TelemetryChart';
import { VideoPlayer } from '../components/VideoPlayer';
import { EvidencePanel } from '../components/EvidencePanel';
import { RegulationPanel } from '../components/RegulationPanel';
import { EvidenceRegulationFlow } from '../components/EvidenceRegulationFlow';
import { UncertaintyCaveats } from '../components/UncertaintyCaveats';
import { IncidentTimeline } from '../components/IncidentTimeline';
import { ReferenceBaselinePanel } from '../components/ReferenceBaselinePanel';
import { OvertakeGeometryPanel } from '../components/OvertakeGeometryPanel';
import { MLEvidencePanel } from '../components/MLEvidencePanel';
import { StewardDossierPanel } from '../components/StewardDossierPanel';
import { HistoricalComparablePanel } from '../components/HistoricalComparablePanel';
import { DriverModal } from '../components/DriverModal';
import { 
  getIncident, 
  getTelemetry, 
  getDriver,
  updateIncidentStatus,
  getIncidentReviews,
  submitIncidentReview,
  fetchStewardDossier,
  fetchHistoricalComparisons,
  askAssistant,
} from '../lib/api';
import { 
  Incident, 
  TelemetryPoint, 
  Driver,
  AssistantMessage,
  ReviewRecord,
  IncidentStatus,
  StewardEvidenceDossier,
  HistoricalComparisonResponse,
} from '../lib/types';
import { 
  ArrowLeft, 
  Bot, 
  Send, 
  Sparkles, 
  ShieldCheck,
  Activity,
  Radio,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RotateCcw,
  UserCheck,
  FileCheck
} from 'lucide-react';

interface IncidentDetailViewProps {
  incidentId: string;
  onBack: () => void;
  onNavigate: (view: string, id?: string) => void;
}

export const IncidentDetailView: React.FC<IncidentDetailViewProps> = ({
  incidentId,
  onBack,
  onNavigate,
}) => {
  const [incident, setIncident] = useState<Incident | null>(null);
  const [telemetry, setTelemetry] = useState<TelemetryPoint[]>([]);
  const [activeDriver, setActiveDriver] = useState<Driver | null>(null);
  const [selectedTimestamp, setSelectedTimestamp] = useState<string>('13:42:18.4');
  const [stewardDossier, setStewardDossier] = useState<StewardEvidenceDossier | null>(null);

  // Human Steward Review Workflow State
  const [reviews, setReviews] = useState<ReviewRecord[]>([]);
  const [reviewerId, setReviewerId] = useState<string>('steward-panel');
  const [reviewNotes, setReviewNotes] = useState<string>('');
  const [reviewRationale, setReviewRationale] = useState<string>('');
  const [reopenReason, setReopenReason] = useState<string>('');
  const [showReopenInput, setShowReopenInput] = useState<boolean>(false);
  const [evidenceConsidered, setEvidenceConsidered] = useState<string[]>([
    'FastF1 ECU Telemetry (25Hz)',
    'Synchronized Video Broadcast',
    'FIA Formula One Sporting Regulations'
  ]);
  const [evidenceMissing, setEvidenceMissing] = useState<string[]>([]);
  const [isSubmittingReview, setIsSubmittingReview] = useState<boolean>(false);
  const [reviewActionError, setReviewActionError] = useState<string | null>(null);
  const [historicalComparisons, setHistoricalComparisons] = useState<HistoricalComparisonResponse | null>(null);

  // Embedded AI Steward Assistant State
  const [assistantInput, setAssistantInput] = useState('');
  const [assistantMessages, setAssistantMessages] = useState<AssistantMessage[]>([
    {
      id: 'msg-init-detail',
      sender: 'assistant',
      timestamp: '13:42:25',
      text: "AI Steward Assistant active for Incident #024. Telemetry streams (FastF1 25Hz), broadcast timecodes, and FIA regulatory articles are indexed. Select an evidentiary query below or ask a specific question.",
      evidenceChips: [
        { label: 'TELEMETRY: FastF1 ECU 25Hz', type: 'telemetry' },
        { label: 'VIDEO: World Feed T4 Synced', type: 'timeline' },
        { label: 'REGULATION: FIA Sporting Code Art 33.4', type: 'regulation' },
      ],
      suggestedFollowUps: [
        'Why was this incident flagged?',
        'What changed in the telemetry?',
        'Which regulations are relevant?',
        'What evidence supports this?',
        'What evidence is missing?',
      ],
    },
  ]);
  const [isTyping, setIsTyping] = useState(false);

  useEffect(() => {
    refreshIncidentData();
  }, [incidentId]);

  const refreshIncidentData = () => {
    getIncident(incidentId).then((data) => {
      if (data) {
        setIncident(data);
      }
    });
    getTelemetry(incidentId).then(setTelemetry);
    getIncidentReviews(incidentId).then(setReviews);
    fetchStewardDossier(incidentId)
      .then(setStewardDossier)
      .catch(() => {
        // Fallback or unlinked
      });
    fetchHistoricalComparisons(incidentId)
      .then(setHistoricalComparisons)
      .catch(() => {
        // Fallback
      });
  };

  const handleBeginReview = async () => {
    setReviewActionError(null);
    setIsSubmittingReview(true);
    try {
      const updated = await updateIncidentStatus(incidentId, {
        status: 'UNDER_REVIEW',
        reviewer_id: reviewerId,
        review_notes: 'Human steward initiated formal review panel proceedings.',
      });
      setIncident(updated);
      await getIncidentReviews(incidentId).then(setReviews);
    } catch (e: any) {
      setReviewActionError(e.message || 'Failed to begin review');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleSubmitFormalReview = async (targetStatus: 'REVIEWED' | 'DISMISSED') => {
    setReviewActionError(null);
    if (!reviewRationale.trim() && targetStatus === 'REVIEWED') {
      setReviewActionError('Review rationale / sporting reasoning is required to finalize verdict.');
      return;
    }
    setIsSubmittingReview(true);
    try {
      await submitIncidentReview(incidentId, {
        status: targetStatus,
        reviewer_id: reviewerId,
        review_notes: reviewNotes.trim() || undefined,
        review_rationale: reviewRationale.trim() || (targetStatus === 'DISMISSED' ? 'Candidate dismissed as regular racing incident / negligible contact.' : undefined),
        evidence_considered: evidenceConsidered,
        evidence_missing: evidenceMissing.length > 0 ? evidenceMissing : undefined,
      });
      refreshIncidentData();
      setReviewNotes('');
      setReviewRationale('');
    } catch (e: any) {
      setReviewActionError(e.message || 'Failed to submit review');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  const handleReopenReview = async () => {
    setReviewActionError(null);
    if (!reopenReason.trim()) {
      setReviewActionError('An explicit reason is strictly required by stewards to reopen a closed incident.');
      return;
    }
    setIsSubmittingReview(true);
    try {
      const updated = await updateIncidentStatus(incidentId, {
        status: 'UNDER_REVIEW',
        reviewer_id: reviewerId,
        reopen_reason: reopenReason.trim(),
      });
      setIncident(updated);
      await getIncidentReviews(incidentId).then(setReviews);
      setShowReopenInput(false);
      setReopenReason('');
    } catch (e: any) {
      setReviewActionError(e.message || 'Failed to reopen review');
    } finally {
      setIsSubmittingReview(false);
    }
  };

  if (!incident) {
    return (
      <div className="p-12 text-center font-mono text-white/40">
        Loading Incident Telemetry Record...
      </div>
    );
  }

  const handleOpenDriverModal = (driverCode: string) => {
    getDriver(driverCode).then((driver) => {
      if (driver) setActiveDriver(driver);
    });
  };

  const handleAssistantSend = async (queryText?: string) => {
    const query = queryText || assistantInput;
    if (!query.trim()) return;

    const userMsg: AssistantMessage = {
      id: `msg-${Date.now()}`,
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
    };

    setAssistantMessages((prev) => [...prev, userMsg]);
    if (!queryText) setAssistantInput('');
    setIsTyping(true);

    try {
      const botReply = await askAssistant(query, incidentId);
      setAssistantMessages((prev) => [...prev, botReply]);
    } catch (e: any) {
      setAssistantMessages((prev) => [
        ...prev,
        {
          id: `msg-${Date.now() + 1}`,
          sender: 'assistant',
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
          text: `Assistant query service error: ${e.message || 'Service unreachable'}.`,
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Top Back Navigation Bar */}
      <div className="flex flex-wrap items-center justify-between gap-4 text-xs font-mono text-white/40">
        <button
          onClick={onBack}
          className="flex items-center gap-2 hover:text-white transition-colors cursor-pointer bg-white/5 border border-white/10 px-3 py-1.5 rounded-sm"
        >
          <ArrowLeft className="w-4 h-4" />
          <span className="uppercase tracking-wider">Back to Incidents</span>
        </button>

        <div className="flex items-center gap-3">
          <span className="text-white/20">|</span>
          <span>FastF1 Session Sync: <strong className="text-emerald-400 font-semibold">LOCKED (25Hz)</strong></span>
        </div>
      </div>

      {/* ==================================================
          1. INCIDENT HEADER (Section 5 Exact Specification)
          - INCIDENT #024
          - Driver A → Driver B
          - Lap
          - Turn
          - Timestamp
          - Incident Type
          - Confidence
          - Status
          No automated guilt/fault/penalty decisions.
      ================================================== */}
      <div className="bg-[#0a0a0b] border border-white/10 rounded-sm p-6 sm:p-8">
        <div className="flex flex-col lg:flex-row justify-between items-start gap-6">
          <div className="space-y-3">
            <div className="text-[11px] text-red-600 font-bold tracking-[0.25em] uppercase font-mono">
              INCIDENT #{incident.id.replace('INC-', '')}
            </div>

            {/* Matchup: Driver A → Driver B */}
            <div className="flex items-center gap-3">
              <span className="text-2xl sm:text-4xl font-bold font-mono text-white">
                {incident.driverA}
              </span>
              <span className="text-xl sm:text-2xl font-mono text-white/40 font-light">
                →
              </span>
              <span className="text-2xl sm:text-4xl font-bold font-mono text-white">
                {incident.driverB}
              </span>
            </div>

            {/* Incident Type */}
            <div className="text-lg sm:text-xl font-light text-white uppercase font-tech tracking-wide">
              {incident.incidentType}
            </div>

            {/* Metadata Badges: Lap, Turn, Timestamp */}
            <div className="flex flex-wrap items-center gap-3 text-xs font-mono text-white/70 pt-1">
              <div className="bg-white/5 border border-white/10 px-3 py-1.5 rounded-sm">
                <span className="text-white/40 mr-1.5">LAP</span>
                <strong className="text-white font-semibold">{incident.lap}</strong>
              </div>
              <div className="bg-white/5 border border-white/10 px-3 py-1.5 rounded-sm">
                <span className="text-white/40 mr-1.5">TURN</span>
                <strong className="text-white font-semibold">{incident.turn.toUpperCase()}</strong>
              </div>
              <div className="bg-white/5 border border-white/10 px-3 py-1.5 rounded-sm">
                <span className="text-white/40 mr-1.5">TIMESTAMP</span>
                <strong className="text-yellow-400 font-mono-num">{incident.timestamp}</strong>
              </div>
            </div>

            {/* Candidate Ingestion & Provenance Footprint */}
            <div className="flex flex-wrap items-center gap-2 pt-2 text-[10px] font-mono text-white/40">
              <span className="bg-white/5 border border-white/10 px-2 py-0.5 rounded-sm">
                CANDIDATE: <strong className="text-white/70">{incident.candidateId || incident.id}</strong>
              </span>
              <span className="bg-white/5 border border-white/10 px-2 py-0.5 rounded-sm">
                METHOD: <strong className="text-white/70">{incident.detectionMethod || "Kinematic Windowing"}</strong>
              </span>
              <span className="bg-white/5 border border-white/10 px-2 py-0.5 rounded-sm">
                PIPELINE: <strong className="text-white/70">{incident.preprocessingVersion || "FastF1 25Hz v1.4.1"}</strong>
              </span>
              {incident.canonicalFingerprint && (
                <span className="bg-white/5 border border-white/10 px-2 py-0.5 rounded-sm text-white/30 truncate max-w-xs" title={incident.canonicalFingerprint}>
                  FP: {incident.canonicalFingerprint}
                </span>
              )}
            </div>
          </div>

          {/* Right Metrics: Confidence & Dynamic Review Status */}
          <div className="flex flex-col items-start lg:items-end justify-between self-stretch lg:self-auto shrink-0 space-y-2">
            <div>
              <div className="text-[10px] text-white/40 uppercase tracking-widest font-mono lg:text-right">
                Correlation Confidence
              </div>
              <div className="text-4xl sm:text-5xl font-mono font-light text-white lg:text-right leading-none mt-1">
                {incident.confidence}<span className="text-xl opacity-30">%</span>
              </div>
            </div>

            <div className="pt-2">
              <span className={`px-3 py-1.5 rounded-sm uppercase font-bold text-xs font-mono border tracking-wider inline-flex items-center gap-1.5 ${
                incident.status === 'REQUIRES_REVIEW'
                  ? 'bg-red-600/10 text-red-500 border-red-600/30'
                  : incident.status === 'UNDER_REVIEW'
                  ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                  : incident.status === 'DISMISSED'
                  ? 'bg-white/5 text-white/50 border-white/20'
                  : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
              }`}>
                {incident.status === 'REQUIRES_REVIEW' && (
                  <span className="w-2 h-2 rounded-full bg-red-600 animate-pulse"></span>
                )}
                {incident.status === 'UNDER_REVIEW' && (
                  <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                )}
                {incident.status === 'REVIEWED' && (
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
                )}
                {incident.status === 'DISMISSED' && (
                  <span className="w-2 h-2 rounded-full bg-white/40"></span>
                )}
                {incident.status === 'REQUIRES_REVIEW' ? 'REQUIRES STEWARD REVIEW' : incident.status.replace(/_/g, ' ')}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* ==================================================
          2. VIDEO EVIDENCE (Section 6: Must start at 00:05 and loop from 00:05)
      ================================================== */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
            <span className="w-2 h-2 bg-red-600 rounded-full"></span>
            2. VIDEO EVIDENCE
          </div>
          <span className="text-[10px] font-mono text-white/40">
            Playback Range: 00:05 → End (Loop: 00:05)
          </span>
        </div>

        <VideoPlayer
          videoAvailable={incident.videoAvailable}
          videoUrl={incident.videoPath}
          videoEvidence={incident.videoEvidence}
          visualEvidence={incident.visualEvidence}
          cvEvidence={incident.cvEvidence}
          incidentId={incident.id}
          timeWindow={incident.timeWindow}
          currentTimestamp={selectedTimestamp}
          onTimeChange={(t) => setSelectedTimestamp(t)}
        />
      </section>

      {/* ==================================================
          3. INCIDENT TIMELINE
      ================================================== */}
      <section className="space-y-3">
        <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
          <span className="w-2 h-2 bg-red-600 rounded-full"></span>
          3. INCIDENT TIMELINE
        </div>

        <IncidentTimeline
          mode="incident-detail"
          milestones={incident.timeline}
          selectedTimestamp={selectedTimestamp}
          onSelectMilestone={(t) => setSelectedTimestamp(t)}
        />
      </section>

      {/* ==================================================
          4. TELEMETRY EVIDENCE
      ================================================== */}
      <section className="space-y-3">
        <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
          <span className="w-2 h-2 bg-red-600 rounded-full"></span>
          4. TELEMETRY EVIDENCE
        </div>

        <TelemetryChart
          data={telemetry}
          driverA={incident.driverA}
          driverB={incident.driverB}
          currentTime={selectedTimestamp}
          onTimeSelect={(t) => setSelectedTimestamp(t)}
        />
      </section>

      {/* ==================================================
          4B. REFERENCE-LAP BASELINE & EVIDENCE QUANTIFICATION
      ================================================== */}
      {incident.baselineEvidence && (
        <section className="space-y-3">
          <ReferenceBaselinePanel
            baseline={incident.baselineEvidence}
            driverA={incident.driverA}
            driverB={incident.driverB}
          />
        </section>
      )}

      {/* ==================================================
          4C. CORNERING OVERTAKE GEOMETRY & APEX OVERLAP
      ================================================== */}
      {incident.overtakeGeometry && (
        <section className="space-y-3">
          <OvertakeGeometryPanel
            overtakeGeometry={incident.overtakeGeometry}
            driverA={incident.driverA}
            driverB={incident.driverB}
          />
        </section>
      )}

      {/* ==================================================
          4D. MACHINE LEARNING CANDIDATE EVALUATION
      ================================================== */}
      {incident.mlEvidence && (
        <section className="space-y-3">
          <MLEvidencePanel
            mlEvidence={incident.mlEvidence}
            driverA={incident.driverA}
            driverB={incident.driverB}
          />
        </section>
      )}

      {/* ==================================================
          4E. MASTER STEWARD EVIDENCE DOSSIER & DISCREPANCY ANALYSIS (Prompt 16)
      ================================================== */}
      {stewardDossier && (
        <section className="space-y-3">
          <StewardDossierPanel dossier={stewardDossier} />
        </section>
      )}

      {/* ==================================================
          4F. EXPLAINABLE HISTORICAL COMPARABLE CASES & SIDE-BY-SIDE ANALYSIS (Prompt 23)
      ================================================== */}
      {(stewardDossier?.historicalComparableEvidence || historicalComparisons) && (
        <section className="space-y-3">
          <HistoricalComparablePanel
            comparisonData={stewardDossier?.historicalComparableEvidence || historicalComparisons}
            incidentId={incident.id}
          />
        </section>
      )}

      {/* ==================================================
          5. EVIDENCE ASSESSMENT
      ================================================== */}
      <section className="space-y-3">
        <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
          <span className="w-2 h-2 bg-red-600 rounded-full"></span>
          5. EVIDENCE ASSESSMENT
        </div>

        <EvidencePanel evidenceList={incident.evidenceAssessment} />
      </section>

      {/* ==================================================
          6. RELEVANT REGULATIONS
      ================================================== */}
      <section className="space-y-4">
        <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
          <span className="w-2 h-2 bg-red-600 rounded-full"></span>
          6. RELEVANT REGULATIONS
        </div>

        <RegulationPanel regulations={incident.relevantRegulations} />

        <div className="mt-4">
          <EvidenceRegulationFlow connections={incident.evidenceConnections} />
        </div>
      </section>

      {/* ==================================================
          7. UNCERTAINTY & CAVEATS
      ================================================== */}
      <section className="space-y-3">
        <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech flex items-center gap-2">
          <span className="w-2 h-2 bg-red-600 rounded-full"></span>
          7. UNCERTAINTY & CAVEATS
        </div>

        <UncertaintyCaveats uncertainties={incident.uncertainties} />
      </section>

      {/* ==================================================
          8. AI STEWARD ASSISTANT (Embedded Incident Assistant)
      ================================================== */}
      <section className="space-y-4 bg-[#0d0d0f] border border-white/10 rounded-sm p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-sm bg-red-600 flex items-center justify-center text-white">
              <Bot className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech">
                8. AI STEWARD ASSISTANT
              </div>
              <div className="text-[10px] font-mono text-white/40">
                Evidentiary question answering for Incident #{incident.id.replace('INC-', '')}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 text-[10px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2.5 py-1 rounded-sm">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>AI-Assisted Evidence • Human Stewards Decide</span>
          </div>
        </div>

        {/* Suggested Quick Prompt Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[10px] font-mono text-white/40 uppercase tracking-wider mr-1">
            Inquire:
          </span>
          {[
            'Why was this incident flagged?',
            'What changed in the telemetry?',
            'Which regulations are relevant?',
            'What evidence supports this?',
            'What evidence is missing?',
          ].map((prompt, idx) => (
            <button
              key={idx}
              onClick={() => handleAssistantSend(prompt)}
              className="text-[11px] font-mono bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white/80 hover:text-white px-3 py-1.5 rounded-sm transition-colors cursor-pointer"
            >
              {prompt}
            </button>
          ))}
        </div>

        {/* Messages Stream */}
        <div className="space-y-4 bg-[#0a0a0b] border border-white/5 rounded-sm p-4 max-h-96 overflow-y-auto font-mono text-xs">
          {assistantMessages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col gap-1.5 ${
                msg.sender === 'user' ? 'items-end' : 'items-start'
              }`}
            >
              <div className="text-[9px] text-white/30 flex items-center gap-2">
                <span className="uppercase font-bold">
                  {msg.sender === 'user' ? 'Steward Inquiry' : 'AI Assistant'}
                </span>
                <span>•</span>
                <span>{msg.timestamp}</span>
              </div>

              <div
                className={`p-4 rounded-sm max-w-3xl leading-relaxed whitespace-pre-line ${
                  msg.sender === 'user'
                    ? 'bg-red-600/20 border border-red-600/30 text-white'
                    : 'bg-white/5 border border-white/10 text-white/90'
                }`}
              >
                {msg.text}

                {/* Evidence Chips */}
                {msg.evidenceChips && msg.evidenceChips.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-white/10">
                    {msg.evidenceChips.map((chip, cIdx) => (
                      <span
                        key={cIdx}
                        className="text-[9px] font-mono px-2 py-0.5 rounded-sm bg-white/5 border border-white/10 text-white/70"
                      >
                        {chip.label}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isTyping && (
            <div className="flex items-center gap-2 text-white/40 text-xs py-2">
              <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></span>
              <span>Analyzing telemetry anomalies and regulations...</span>
            </div>
          )}
        </div>

        {/* Input Field */}
        <div className="flex gap-2">
          <input
            type="text"
            value={assistantInput}
            onChange={(e) => setAssistantInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleAssistantSend();
            }}
            placeholder="Ask about telemetry spikes, right to room, overlap at apex, or evidence gaps..."
            className="flex-1 bg-[#0a0a0b] border border-white/10 focus:border-red-600 rounded-sm px-3.5 py-2.5 text-xs text-white placeholder:text-white/30 outline-none font-mono transition-colors"
          />
          <button
            onClick={() => handleAssistantSend()}
            className="px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-sm transition-colors flex items-center gap-1.5 cursor-pointer"
          >
            <span>Ask</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </section>

      {/* ==================================================
          9. STEWARD REVIEW WORKFLOW & AUDIT TRAIL
      ================================================== */}
      <section className="space-y-4 bg-[#0d0d0f] border border-white/10 rounded-sm p-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-white/10 pb-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-sm bg-red-600 flex items-center justify-center text-white">
              <UserCheck className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-bold text-white tracking-[0.2em] uppercase font-tech">
                9. STEWARD REVIEW WORKFLOW & AUDIT TRAIL
              </div>
              <div className="text-[10px] font-mono text-white/40">
                Human-in-the-loop incident evaluation • Non-punitive decision support
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2 text-[10px] font-mono text-white/60">
            <span className="bg-white/5 border border-white/10 px-2.5 py-1 rounded-sm">
              Status: <strong className="text-white">{incident.status}</strong>
            </span>
            <span className="bg-white/5 border border-white/10 px-2.5 py-1 rounded-sm">
              Audit Records: <strong className="text-white">{reviews.length}</strong>
            </span>
          </div>
        </div>

        {/* Error Feedback */}
        {reviewActionError && (
          <div className="p-3 bg-red-600/10 border border-red-600/30 text-red-400 text-xs font-mono rounded-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 shrink-0 text-red-500" />
            <span>{reviewActionError}</span>
          </div>
        )}

        {/* Action Panel Based on Current Status */}
        <div className="bg-[#0a0a0b] border border-white/5 rounded-sm p-4 space-y-4 font-mono">
          {incident.status === 'REQUIRES_REVIEW' && (
            <div className="space-y-3">
              <div className="text-xs text-white/80 leading-relaxed">
                This candidate was flagged by the telemetry kinematic reconstruction engine.
                It is currently queued for human review. To begin analysis, enter the panel adjudication phase below.
              </div>
              <div className="flex items-center gap-3 pt-1">
                <button
                  onClick={handleBeginReview}
                  disabled={isSubmittingReview}
                  className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-sm transition-colors cursor-pointer flex items-center gap-2 disabled:opacity-50"
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span>{isSubmittingReview ? 'Updating...' : 'Begin Formal Review'}</span>
                </button>
                <span className="text-[11px] text-white/40">
                  Transitions candidate to UNDER_REVIEW
                </span>
              </div>
            </div>
          )}

          {incident.status === 'UNDER_REVIEW' && (
            <div className="space-y-4 text-xs">
              <div className="text-[11px] text-amber-400 font-bold uppercase tracking-wider flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
                <span>Active Steward Evaluation Form</span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Reviewer Identifier */}
                <div>
                  <label className="block text-[10px] text-white/40 uppercase tracking-wider mb-1">
                    Steward Identifier / Panel Name
                  </label>
                  <input
                    type="text"
                    value={reviewerId}
                    onChange={(e) => setReviewerId(e.target.value)}
                    placeholder="e.g. steward-panel-monza"
                    className="w-full bg-[#121214] border border-white/10 focus:border-red-600 rounded-sm px-3 py-2 text-xs text-white outline-none font-mono"
                  />
                </div>

                {/* Evidence Considered Checkboxes */}
                <div>
                  <label className="block text-[10px] text-white/40 uppercase tracking-wider mb-1">
                    Evidence Considered
                  </label>
                  <div className="space-y-1 bg-[#121214] border border-white/10 rounded-sm p-2 text-[11px]">
                    {[
                      'FastF1 ECU Telemetry (25Hz)',
                      'Synchronized Video Broadcast',
                      'FIA Formula One Sporting Regulations',
                      'Race Control Incident Milestones',
                    ].map((item) => (
                      <label key={item} className="flex items-center gap-2 text-white/70 cursor-pointer hover:text-white">
                        <input
                          type="checkbox"
                          checked={evidenceConsidered.includes(item)}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setEvidenceConsidered([...evidenceConsidered, item]);
                            } else {
                              setEvidenceConsidered(evidenceConsidered.filter((x) => x !== item));
                            }
                          }}
                          className="accent-red-600 rounded-sm"
                        />
                        <span>{item}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>

              {/* Reviewer Observations */}
              <div>
                <label className="block text-[10px] text-white/40 uppercase tracking-wider mb-1">
                  Steward Observational Notes
                </label>
                <textarea
                  rows={2}
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  placeholder="Record empirical findings (e.g. Car A established 80% overlap at apex; steering angle correction visible on telemetry trace)..."
                  className="w-full bg-[#121214] border border-white/10 focus:border-red-600 rounded-sm p-2.5 text-xs text-white outline-none font-mono placeholder:text-white/30"
                />
              </div>

              {/* Regulatory Rationale */}
              <div>
                <label className="block text-[10px] text-white/40 uppercase tracking-wider mb-1">
                  Sporting & Regulatory Rationale (Required for Reviewed)
                </label>
                <textarea
                  rows={2}
                  value={reviewRationale}
                  onChange={(e) => setReviewRationale(e.target.value)}
                  placeholder="State justification under FIA Sporting Regulations (e.g. Article 33.4 satisfied; deemed racing incident with mutual right to racing room)..."
                  className="w-full bg-[#121214] border border-white/10 focus:border-red-600 rounded-sm p-2.5 text-xs text-white outline-none font-mono placeholder:text-white/30"
                />
              </div>

              {/* Form Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <button
                  onClick={() => handleSubmitFormalReview('REVIEWED')}
                  disabled={isSubmittingReview}
                  className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-mono font-bold uppercase tracking-wider rounded-sm transition-colors cursor-pointer flex items-center gap-2 disabled:opacity-50"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  <span>{isSubmittingReview ? 'Submitting...' : 'Mark as Reviewed'}</span>
                </button>

                <button
                  onClick={() => handleSubmitFormalReview('DISMISSED')}
                  disabled={isSubmittingReview}
                  className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white/80 hover:text-white text-xs font-mono font-bold uppercase tracking-wider rounded-sm transition-colors cursor-pointer flex items-center gap-2 disabled:opacity-50"
                >
                  <span>{isSubmittingReview ? 'Submitting...' : 'Dismiss Candidate'}</span>
                </button>

                <span className="text-[11px] text-white/40">
                  Completes human steward review workflow
                </span>
              </div>
            </div>
          )}

          {(incident.status === 'REVIEWED' || incident.status === 'DISMISSED') && (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-xs">
                {incident.status === 'REVIEWED' ? (
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-white/40"></span>
                )}
                <span className="text-white/90">
                  This incident is closed with terminal status: <strong className="text-white uppercase">{incident.status}</strong>.
                </span>
              </div>

              {!showReopenInput ? (
                <div className="pt-1">
                  <button
                    onClick={() => setShowReopenInput(true)}
                    className="px-3.5 py-1.5 bg-white/5 hover:bg-white/10 border border-white/10 hover:border-white/20 text-white/80 hover:text-white text-xs font-mono rounded-sm transition-colors cursor-pointer flex items-center gap-2"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                    <span>Reopen Review</span>
                  </button>
                </div>
              ) : (
                <div className="bg-[#121214] border border-amber-500/30 rounded-sm p-3 space-y-2 mt-2">
                  <div className="text-[11px] text-amber-400 font-bold uppercase">
                    Mandatory Reopen Justification
                  </div>
                  <input
                    type="text"
                    value={reopenReason}
                    onChange={(e) => setReopenReason(e.target.value)}
                    placeholder="Enter reason (e.g. New onboard video evidence submitted by competitor)..."
                    className="w-full bg-[#0a0a0b] border border-white/10 focus:border-amber-500 rounded-sm px-3 py-2 text-xs text-white outline-none font-mono"
                  />
                  <div className="flex items-center gap-2 pt-1">
                    <button
                      onClick={handleReopenReview}
                      disabled={isSubmittingReview}
                      className="px-3 py-1.5 bg-amber-600 hover:bg-amber-500 text-white text-xs font-bold uppercase rounded-sm transition-colors cursor-pointer disabled:opacity-50"
                    >
                      {isSubmittingReview ? 'Reopening...' : 'Confirm Reopen'}
                    </button>
                    <button
                      onClick={() => {
                        setShowReopenInput(false);
                        setReopenReason('');
                      }}
                      className="px-3 py-1.5 bg-white/5 text-white/60 hover:text-white text-xs rounded-sm transition-colors cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Audit Log Stream */}
        <div className="space-y-3 pt-2">
          <div className="text-[11px] font-bold text-white/60 uppercase tracking-wider font-tech flex items-center gap-2">
            <FileText className="w-3.5 h-3.5 text-red-500" />
            <span>Chronological Audit Trail ({reviews.length} Entries)</span>
          </div>

          {reviews.length === 0 ? (
            <div className="p-4 bg-[#0a0a0b] border border-white/5 rounded-sm text-center text-white/40 text-xs font-mono">
              No audit records recorded yet.
            </div>
          ) : (
            <div className="space-y-2 font-mono text-xs">
              {reviews.map((rec, idx) => (
                <div
                  key={rec.id || idx}
                  className="p-3 bg-[#0a0a0b] border border-white/5 rounded-sm space-y-1.5"
                >
                  <div className="flex flex-wrap items-center justify-between gap-2 text-[10px]">
                    <div className="flex items-center gap-2">
                      <span
                        className={`px-2 py-0.5 rounded-sm uppercase font-bold border ${
                          rec.status === 'REQUIRES_REVIEW'
                            ? 'bg-red-600/10 text-red-500 border-red-600/30'
                            : rec.status === 'UNDER_REVIEW'
                            ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
                            : rec.status === 'DISMISSED'
                            ? 'bg-white/5 text-white/50 border-white/20'
                            : 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30'
                        }`}
                      >
                        {rec.status}
                      </span>
                      <span className="text-white/60">
                        Reviewer: <strong className="text-white">{rec.reviewerId}</strong>
                      </span>
                    </div>

                    <span className="text-white/30">
                      {rec.createdAt ? new Date(rec.createdAt).toLocaleString() : 'Timestamp Recorded'}
                    </span>
                  </div>

                  {rec.reviewNotes && (
                    <div className="text-white/80 text-[11px] pt-1">
                      <span className="text-white/40 uppercase mr-1">Notes:</span>
                      {rec.reviewNotes}
                    </div>
                  )}

                  {rec.reviewRationale && (
                    <div className="text-white/80 text-[11px]">
                      <span className="text-white/40 uppercase mr-1">Rationale:</span>
                      {rec.reviewRationale}
                    </div>
                  )}

                  {rec.evidenceConsidered && (
                    <div className="text-[10px] text-white/50 pt-1">
                      <span className="text-white/30 uppercase mr-1">Evidence Considered:</span>
                      {rec.evidenceConsidered}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Driver Modal Popup */}
      <DriverModal
        driver={activeDriver}
        onClose={() => setActiveDriver(null)}
        onViewIncidents={() => onNavigate('incidents')}
      />
    </div>
  );
};
