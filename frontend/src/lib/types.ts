export type IncidentStatus = 
  | 'DETECTED'
  | 'ANALYZING'
  | 'REQUIRES_REVIEW'
  | 'UNDER_REVIEW'
  | 'REVIEWED'
  | 'DISMISSED';

export interface ReviewRecord {
  id: string;
  incidentId: string;
  status: IncidentStatus;
  reviewerId: string;
  reviewStartedAt?: string;
  reviewCompletedAt?: string;
  evidenceConsidered?: string;
  evidenceMissing?: string;
  observations?: string;
  reviewNotes?: string;
  reviewRationale?: string;
  regulatoryReferences?: string;
  createdAt?: string;
  updatedAt?: string;
}

export type IncidentSeverity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type EvidenceCategory = 
  | 'PROXIMITY'
  | 'RELATIVE_MOTION'
  | 'VEHICLE_RESPONSE'
  | 'TRAJECTORY'
  | 'BRAKING'
  | 'GEOMETRY';

export interface Driver {
  code: string;
  number: number;
  name: string;
  team: string;
  teamColor: string;
  secondaryColor?: string;
  country: string;
  stats: {
    lapsCompleted: number;
    avgSpeedKmh: number;
    maxSpeedKmh: number;
    incidentsInvolved: number;
    interactionsDetected: number;
  };
}

export interface TelemetryPoint {
  timeOffset: number; // e.g., 0.0, 0.1, 0.2 ...
  timestamp: string; // "13:42:18.4"
  // Driver A
  speedA: number; // km/h
  throttleA: number; // 0-100%
  brakeA: number; // 0-100%
  steerA: number; // degrees
  gearA: number;
  accelA: number; // m/s^2 or G
  // Driver B
  speedB: number;
  throttleB: number;
  brakeB: number;
  steerB: number;
  gearB: number;
  accelB: number;
  // Interaction Telemetry
  gapMeters: number;
  closingSpeedMs: number;
  lateralDistMeters: number;
}

export interface EvidenceItem {
  id: string;
  category: EvidenceCategory;
  title: string;
  observedValue: string;
  expectedContext: string;
  confidence: number; // 0 - 100
  source: string;
  description: string;
  verified: boolean;
}

export interface RelevantRegulation {
  id: string;
  document: string; // e.g. "FIA Sporting Regulations 2024"
  article: string; // e.g. "Article 33.4"
  title: string;
  regulationTextPlaceholder: string;
  whyRelevant: string;
  matchReason: string;
  relevance: 'High' | 'Medium' | 'Low';
  source: string;
  sourceUrl?: string;
}

export interface EvidenceRegulationConnection {
  observedEvidence: string;
  relevantRegulation: string;
  stewardReviewAction: string;
}

export interface IncidentTimelineMilestone {
  timestamp: string;
  label: string;
  description: string;
  iconType: 'approach' | 'proximity' | 'contact' | 'motion' | 'response' | 'exit';
  evidenceRef?: string;
}

export interface Incident {
  id: string; // e.g., "INC-024"
  session: string; // "Italian Grand Prix 2024 — Race"
  raceId: string;
  circuit: string; // "Monza"
  lap: number;
  turn: string; // "Turn 4" (Variante della Roggia)
  timestamp: string; // "13:42:18.4"
  timeWindow: {
    start: string; // "13:42:17.8"
    end: string; // "13:42:20.4"
  };
  driverA: string; // "VER"
  driverB: string; // "HAM"
  incidentType: string; // "Possible Contact / Vehicle Disturbance"
  confidence: number; // 87 (%)
  status: IncidentStatus;
  severity: IncidentSeverity;
  summary: string;
  detectionMethod: string;
  videoAvailable: boolean;
  videoPath?: string;
  telemetryAvailable: boolean;
  regulationsAvailable: boolean;
  sources: {
    telemetry: string; // e.g., "FastF1 ECU + GPS"
    video: string; // e.g., "World Feed T4 (Unlinked / Available)"
    regulations: string; // e.g., "FIA Sporting Code 2024"
  };
  evidenceAssessment: EvidenceItem[];
  relevantRegulations: RelevantRegulation[];
  evidenceConnections: EvidenceRegulationConnection[];
  timeline: IncidentTimelineMilestone[];
  uncertainties: string[];
  candidateId?: string;
  canonicalFingerprint?: string;
  preprocessingVersion?: string;
  dataQualitySummary?: Record<string, any>;
  minimumGapMeters?: number;
  peakClosingSpeedMs?: number;
  reviews?: ReviewRecord[];
  baselineEvidence?: BaselineEvidence;
  overtakeGeometry?: OvertakeGeometryEvidence;
  mlEvidence?: MLEvidence;
  videoEvidence?: VideoEvidenceSummary;
  visualEvidence?: VisualEvidenceSummary;
  cvEvidence?: CVIncidentAnalysisResponse;
}

export interface RaceSession {
  name: string;
  laps?: number;
  status: string;
}

export interface Race {
  id: string;
  name: string;
  circuit: string;
  country: string;
  season: string;
  round?: number;
  year: number;
  sessionType: string;
  date: string;
  driversCount: number;
  candidatesCount: number;
  confirmedCount: number;
  reviewCount: number;
  status: 'ANALYSIS READY' | 'LIVE ANALYSIS' | 'SCHEDULED' | 'ANALYSIS_READY';
  telemetryAvailable: boolean;
  videoAvailable: boolean;
  regulationSet: string;
  sessions?: RaceSession[];
}

export interface AssistantMessage {
  id: string;
  sender: 'user' | 'assistant';
  timestamp: string;
  text: string;
  evidenceLinks?: {
    label: string;
    targetView: string;
    incidentId?: string;
  }[];
  evidenceChips?: {
    label: string;
    type: 'telemetry' | 'timeline' | 'regulation' | 'response';
    targetId?: string;
  }[];
  suggestedFollowUps?: string[];
}

export type BaselineStatus = 'AVAILABLE' | 'INSUFFICIENT_REFERENCE_DATA' | 'ALIGNMENT_FAILED';
export type SignalStatus = 'OBSERVED' | 'DERIVED' | 'UNAVAILABLE';

export interface BaselineDisruptionMetrics {
  driverCode: string;
  brakingOnsetDeltaM?: number;
  brakingOnsetDeltaSec?: number;
  peakBrakePctDelta?: number;
  throttleLiftDeltaM?: number;
  throttleReapplicationDelayM?: number;
  throttleReapplicationDelaySec?: number;
  minCornerSpeedDeltaKmh?: number;
  speedAtApexIncidentKmh?: number;
  speedAtApexBaselineKmh?: number;
}

export interface TrajectoryDeviationMetrics {
  driverCode: string;
  status: SignalStatus;
  maxTrajectoryDeviationM: number;
  meanTrajectoryDeviationM: number;
  deviationAtApexM?: number;
  lateralTrackDeviationStatus: SignalStatus;
  note: string;
}

export interface ReferenceLapProvenance {
  driverCode: string;
  referenceLapsUsed: number[];
  totalLapsAnalyzed: number;
  excludedLapsReasons: Record<string, string>;
  aggregationMethod: string;
  resamplingResolutionM: number;
}

export interface BaselineProfilePoint {
  distanceM: number;
  speedBaselineKmh: number;
  speedIncidentKmh: number;
  speedDeltaKmh: number;
  speedIqrKmh: number;
  throttleBaselinePct: number;
  throttleIncidentPct: number;
  throttleDeltaPct: number;
  brakeBaselinePct: number;
  brakeIncidentPct: number;
  brakeDeltaPct: number;
  xBaselineM?: number;
  yBaselineM?: number;
  xIncidentM?: number;
  yIncidentM?: number;
  trajectoryDeviationM?: number;
}

export interface DriverBaselineEvidence {
  driverCode: string;
  status: BaselineStatus;
  provenance: ReferenceLapProvenance;
  disruptionMetrics?: BaselineDisruptionMetrics;
  trajectoryMetrics?: TrajectoryDeviationMetrics;
  profileSample: BaselineProfilePoint[];
  notes: string[];
}

export interface BaselineEvidence {
  status: BaselineStatus;
  drivers: Record<string, DriverBaselineEvidence>;
  summary: string;
  signalProvenance: Record<string, SignalStatus>;
  stewardGuidance: string;
}

// ==========================================
// CORNERING OVERTAKE GEOMETRY TYPES
// ==========================================

export type MeasurementConfidence = 
  | 'DIRECTLY_OBSERVED'
  | 'DERIVED_FROM_TELEMETRY'
  | 'DERIVED_FROM_POSITION'
  | 'PARTIALLY_OBSERVABLE'
  | 'UNAVAILABLE';

export type RelativeLongitudinalPosition = 
  | 'AHEAD'
  | 'BEHIND'
  | 'APPROXIMATELY_ALONGSIDE'
  | 'UNAVAILABLE';

export type OverlapClassification = 
  | 'NO_MEASURABLE_OVERLAP'
  | 'PARTIAL_OVERLAP'
  | 'APPROXIMATELY_50_PERCENT_OVERLAP'
  | 'GREATER_THAN_50_PERCENT_OVERLAP'
  | 'OVERLAP_ANALYSIS_LIMITED'
  | 'INSUFFICIENT_GEOMETRIC_DATA';

export type ExitClearanceClassification = 
  | 'CLEARANCE_ABOVE_REFERENCE'
  | 'CLEARANCE_NEAR_REFERENCE'
  | 'CLEARANCE_BELOW_REFERENCE'
  | 'CLEARANCE_UNAVAILABLE';

export interface CornerPhaseSnapshot {
  phaseName: string;
  distanceIncidentM: number;
  distanceOtherM: number;
  deltaSM: number;
  deltaTSec?: number;
  speedIncidentKmh: number;
  speedOtherKmh: number;
  speedDeltaKmh: number;
  lateralGapM?: number;
  euclideanGapM?: number;
  relativePosition: RelativeLongitudinalPosition;
  confidence: MeasurementConfidence;
}

export interface ApexOverlapSnapshot {
  incidentCarCode: string;
  incidentDistanceM: number;
  incidentSpeedKmh: number;
  incidentXM?: number;
  incidentYM?: number;
  otherCarCode: string;
  otherDistanceM: number;
  otherSpeedKmh: number;
  otherXM?: number;
  otherYM?: number;
  longitudinalGapM: number;
  lateralGapM?: number;
  euclideanGapM?: number;
  relativePosition: RelativeLongitudinalPosition;
  overlapPercent?: number;
  overlapClassification: OverlapClassification;
  frontAxleGapM?: number;
  mirrorReferenceOverlapPercent?: number;
  confidence: MeasurementConfidence;
}

export interface CornerPhases {
  cornerEntryDistanceM: number;
  cornerEntryTimeS: number;
  entryDetectionMethod: string;
  apexDistanceM: number;
  apexTimeS: number;
  apexSpeedKmh: number;
  apexDetectionMethod: string;
  cornerExitDistanceM?: number;
  cornerExitTimeS?: number;
  exitDetectionStatus: string;
  exitDetectionMethod?: string;
}

export interface ExitClearanceMetrics {
  exitDistanceM?: number;
  measuredClearanceM?: number;
  referenceWidthThresholdM: number;
  clearanceClassification: ExitClearanceClassification;
  confidence: MeasurementConfidence;
  note: string;
}

export interface FIAGuidelineReference {
  ruleSource: string;
  ruleReference: string;
  ruleVersionOrDate: string;
  measurementDefinition: string;
  threshold: string;
  thresholdType: string;
  stewardDiscretionStatement: string;
}

export interface OvertakeGeometryDataQuality {
  synchronizedTimestamps: boolean;
  distanceMonotonic: boolean;
  missingTelemetry: boolean;
  unrealisticPositionalJumps: boolean;
  vehicleDimensionAssumptionsUsed: boolean;
  limitations: string[];
}

export interface OvertakeGeometryEvidence {
  incidentId: string;
  driverIncident: string;
  driverOther: string;
  turn: string;
  cornerPhases: CornerPhases;
  apexSnapshot: ApexOverlapSnapshot;
  exitClearance: ExitClearanceMetrics;
  phaseSnapshots: CornerPhaseSnapshot[];
  overlapClassification: OverlapClassification;
  overlapPercent?: number;
  frontAxleOverlapRatio?: number;
  frontAxleOverlapPercent?: number;
  fiaReference: FIAGuidelineReference;
  dataQuality: OvertakeGeometryDataQuality;
  provenanceSummary: Record<string, MeasurementConfidence>;
  summary: string;
  stewardGuidance: string;
}

export interface FeatureContribution {
  featureName: string;
  featureValue: number;
  importanceWeight: number;
  directionalImpact: 'INCREASES_CANDIDATE_LIKELIHOOD' | 'DECREASES_CANDIDATE_LIKELIHOOD';
  description: string;
}

export interface MLModelMetadata {
  modelName: string;
  modelFamily: string;
  featureVersion: string;
  datasetVersion: string;
  trainingSampleCount: number;
  crossValidationStrategy: string;
  datasetScope: string;
  validationStatus: string;
}

export interface MLEvidence {
  incidentId: string;
  candidateProbability: number;
  predictedLabel: number;
  decisionThreshold: number;
  classification: string;
  uncertaintyBand: number[];
  topContributingFeatures: FeatureContribution[];
  modelMetadata: MLModelMetadata;
  limitations: string[];
  stewardGuidance: string;
}

export type VideoSyncStatus = 'VIDEO_SYNCHRONIZED' | 'VIDEO_AVAILABLE' | 'VIDEO_UNSYNCHRONIZED' | 'VIDEO_UNAVAILABLE';
export type VideoSourceType = 'BROADCAST' | 'ONBOARD' | 'TRACKSIDE' | 'USER_PROVIDED' | 'UNKNOWN';
export type SyncMethod = 'DIRECT_TIMESTAMP' | 'MANUAL_CALIBRATION' | 'EVENT_ANCHOR' | 'UNKNOWN';
export type SyncConfidence = 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE';

export interface VideoProvenanceRecord {
  source: string;
  sourceReference: string;
  acquisitionMethod: string;
  session: string;
  camera: string;
  timestampBasis: string;
  availability: string;
  metadataQuality: string;
}

export interface IncidentVideoWindow {
  incidentId: string;
  windowStatus: string;
  sessionStartTime: string;
  sessionPeakTime: string;
  sessionEndTime: string;
  videoStartTime?: string;
  videoPeakTime?: string;
  videoEndTime?: string;
  preRollSec: number;
  postRollSec: number;
  totalClipDurationSec: number;
  frameStart?: number;
  framePeak?: number;
  frameEnd?: number;
  estimatedErrorSec?: number;
  confidence: SyncConfidence;
}

export interface CameraAlignmentInfo {
  cameraId: string;
  cameraLabel: string;
  sourceType: string;
  syncStatus: VideoSyncStatus;
  syncMethod: SyncMethod;
  offsetSeconds?: number;
  estimatedErrorSeconds?: number;
  confidence: SyncConfidence;
  incidentWindow?: IncidentVideoWindow;
  provenance?: VideoProvenanceRecord;
}

export interface SynchronizationUncertainty {
  syncStatus: VideoSyncStatus;
  offsetSeconds?: number;
  estimatedErrorSeconds?: number;
  method: SyncMethod;
  confidence: SyncConfidence;
  calibrationPointCount: number;
  residualRmseSeconds?: number;
  limitations: string[];
}

export interface VideoEvidenceSummary {
  videoEvidenceStatus: VideoSyncStatus;
  sources: Array<{
    videoId: string;
    sourceType: string;
    sourceUrl?: string;
    sourceReference?: string;
    sessionId: string;
    cameraLabel: string;
    durationSec?: number;
    syncStatus: VideoSyncStatus;
    frameRate?: number;
    resolution?: string;
    provenance?: VideoProvenanceRecord;
  }>;
  statement: string;
  incidentWindow?: IncidentVideoWindow;
  multiCamera?: CameraAlignmentInfo[];
  uncertainty?: SynchronizationUncertainty;
  visualEvidence?: VisualEvidenceSummary;
  limitations?: string[];
}

// ==============================================================================
// VISUAL EVIDENCE & MULTI-MODAL ALIGNMENT (PROMPT 13)
// ==============================================================================

export type VisualObservationStatus = 'OBSERVED' | 'DERIVED' | 'UNAVAILABLE';
export type DriverAssociationStatus = 'CONFIRMED' | 'INFERRED' | 'UNAVAILABLE';
export type VisibilityState = 'IN_FRAME' | 'PARTIAL' | 'OCCLUDED' | 'OUT_OF_FRAME';
export type ApproachTrend = 'APPROACHING' | 'RECEDING' | 'STABLE' | 'UNKNOWN';
export type AlignmentStatus = 'ALIGNED' | 'PARTIALLY_ALIGNED' | 'MISALIGNED' | 'INSUFFICIENT_DATA';
export type VisualEvidenceQualityRating = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNUSABLE';

export interface VisualROI {
  roiId: string;
  cameraId: string;
  frameNumber?: number;
  xMin: number;
  yMin: number;
  xMax: number;
  yMax: number;
  pixelCoords?: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  coordinateSystem: string;
  label?: string;
  confidence: number;
  provenance?: VideoProvenanceRecord;
}

export interface VisualTrackObservation {
  trackId: string;
  driverNumber?: string;
  driverCode?: string;
  associationStatus: DriverAssociationStatus;
  centroidX: number;
  centroidY: number;
  bbox: VisualROI;
  visibility: VisibilityState;
  detectionConfidence: number;
  trackPersistenceFrames: number;
  provenance?: VideoProvenanceRecord;
}

export interface VisualFeatureEvidence {
  featureSetId: string;
  centroidDisplacementPx?: number;
  bboxWidthNorm: number;
  bboxHeightNorm: number;
  bboxOverlapIou: number;
  imagePlaneSeparationNorm?: number;
  approachRecedeTrend: ApproachTrend;
  trackPersistenceCount: number;
  occlusionDetected: boolean;
  occlusionRatio: number;
  confidenceScore: number;
  measurementBasis: string;
}

export interface VisualKeyframe {
  keyframeId: string;
  eventRelativeTimeSec: number;
  videoTimestamp: string;
  videoTimeSec: number;
  sessionTimestamp: string;
  sessionTimeSec: number;
  frameNumber?: number;
  cameraId: string;
  cameraLabel: string;
  observations: VisualTrackObservation[];
  rois: VisualROI[];
  features?: VisualFeatureEvidence;
  synchronizationErrorSec: number;
  alignmentStatus: AlignmentStatus;
  provenance?: VideoProvenanceRecord;
}

export interface CrossModalAlignment {
  telemetryEventTimeSec: number;
  visualEventTimeSec?: number;
  deltaSeconds?: number;
  synchronizationUncertaintySec: number;
  toleranceSec: number;
  alignmentStatus: AlignmentStatus;
  description: string;
}

export interface VisualEvidenceQuality {
  qualityRating: VisualEvidenceQualityRating;
  frameRateFps?: number;
  resolution?: string;
  occlusionFrequency: number;
  syncUncertaintySec: number;
  averageTrackPersistence: number;
  notes: string[];
}

export interface VisualEvidenceSummary {
  status: VisualObservationStatus;
  cameraId?: string;
  cameraLabel?: string;
  keyframes: VisualKeyframe[];
  trackObservations: VisualTrackObservation[];
  crossModalAlignment?: CrossModalAlignment;
  quality?: VisualEvidenceQuality;
  statement: string;
  limitations: string[];
}

// ==============================================================================
// COMPUTER VISION DETECTION, TRACKING & IDENTITY (PROMPT 14)
// ==============================================================================

export type CVProcessingStatus = 
  | 'AVAILABLE' 
  | 'MODEL_UNAVAILABLE' 
  | 'VIDEO_UNAVAILABLE' 
  | 'INSUFFICIENT_DATA' 
  | 'PROCESSING_ERROR';

export type ModelStatus = 
  | 'LOADED' 
  | 'MODEL_UNAVAILABLE' 
  | 'NOT_CONFIGURED';

export type TrackingQualityRating = 
  | 'HIGH' 
  | 'MEDIUM' 
  | 'LOW' 
  | 'INSUFFICIENT_DATA';

export type IdentityMethod = 
  | 'ONBOARD_CAMERA_FIXED' 
  | 'TELEMETRY_TRACK_ORDER' 
  | 'MANUAL_STEWARD_OVERRIDE' 
  | 'UNASSOCIATED';

export type CVEvaluationStatus = 
  | 'NOT_YET_AVAILABLE' 
  | 'SYNTHETIC_BENCHMARK_ONLY' 
  | 'REAL_WORLD_EVALUATED';

export interface BoundingBox {
  xMin: number;
  yMin: number;
  xMax: number;
  yMax: number;
  pixelCoords?: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
  coordinateSystem: string;
}

export interface Detection {
  detectionId: string;
  bbox: BoundingBox;
  className: string;
  classId: number;
  confidence: number;
  provenance?: VideoProvenanceRecord;
  sourceMetadata?: Record<string, any>;
}

export interface DetectionFrame {
  frameNumber: number;
  videoId: string;
  cameraId: string;
  videoTimestamp: string;
  videoTimeSec: number;
  sessionTimestamp?: string;
  sessionTimeSec?: number;
  synchronizationErrorSec: number;
  detections: Detection[];
  provenance?: VideoProvenanceRecord;
}

export interface TrackObservation {
  observationId: string;
  frameNumber: number;
  videoTimeSec: number;
  sessionTimeSec?: number;
  bbox: BoundingBox;
  centroidX: number;
  centroidY: number;
  confidence: number;
  visibility: VisibilityState;
  sourceDetectionId?: string;
  isInterpolated: boolean;
}

export interface VisualIdentityAssociation {
  trackId: string;
  candidateId: string;
  driverCode?: string;
  driverNumber?: string;
  associationStatus: DriverAssociationStatus;
  method: IdentityMethod;
  confidence: number;
  supportingEvidence: string[];
  limitations: string[];
  provenance?: VideoProvenanceRecord;
}

export interface TrackQuality {
  rating: TrackingQualityRating;
  observationCount: number;
  trackDurationSec: number;
  visibilityRatio: number;
  meanConfidence: number;
  minimumConfidence: number;
  maximumGapFrames: number;
  fragmentationCount: number;
  thresholdsApplied: Record<string, any>;
}

export interface Track {
  trackId: string;
  className: string;
  firstFrame: number;
  lastFrame: number;
  observations: TrackObservation[];
  observationCount: number;
  durationSec: number;
  isActive: boolean;
  quality: TrackQuality;
  identityAssociation?: VisualIdentityAssociation;
}

export interface TrackerResult {
  tracks: Track[];
  activeTracks: Track[];
  terminatedTracks: Track[];
  totalTracks: number;
  frameCount: number;
}

export interface TrackInteractionFeature {
  frameNumber: number;
  videoTimeSec: number;
  sessionTimeSec?: number;
  eventRelativeTimeSec: number;
  trackIdA: string;
  trackIdB: string;
  driverACode?: string;
  driverBCode?: string;
  centroidSeparationNorm: number;
  bboxOverlapIou: number;
  relativeApproachRateNormPerSec?: number;
  relativeDisplacementPx?: number;
  approachRecedeTrend: ApproachTrend;
  simultaneousVisibility: boolean;
  occlusionDetected: boolean;
  occlusionRatio: number;
  meanDetectionConfidence: number;
  temporalContinuity: boolean;
  measurementBasis: string;
}

export interface CVPerformanceMetrics {
  modelName: string;
  modelVersion: string;
  inferenceDevice: string;
  inputResolution: string;
  processedFrames: number;
  processingFps: number;
  totalProcessingTimeSec: number;
  sourceFps: number;
  droppedFrames: number;
}

export interface CVEvaluationReport {
  evaluationStatus: CVEvaluationStatus;
  benchmarkDataset?: string;
  precision?: number;
  recall?: number;
  map50?: number;
  idSwitches?: number;
  trackFragmentationRate?: number;
  statement: string;
}

export interface CVIncidentAnalysisResponse {
  candidateId: string;
  sessionId: string;
  processingStatus: CVProcessingStatus;
  modelStatus: ModelStatus;
  cameraId?: string;
  cameraLabel?: string;
  sampledFrameCount: number;
  droppedFrameCount: number;
  detectionsCount: number;
  tracksCount: number;
  detections: Detection[];
  tracks: Track[];
  identityAssociations: VisualIdentityAssociation[];
  interactionFeatures: TrackInteractionFeature[];
  alignmentStatus: AlignmentStatus;
  performance?: CVPerformanceMetrics;
  evaluation: CVEvaluationReport;
  statement: string;
  limitations: string[];
  provenance?: VideoProvenanceRecord;
}

export type StewardReadinessRating = 'SUFFICIENT' | 'PARTIALLY_SUFFICIENT' | 'INSUFFICIENT' | 'UNAVAILABLE';

export interface DetectionEvaluationMetrics {
  totalGroundTruth: number;
  totalPredictions: number;
  truePositives: number;
  falsePositives: number;
  falseNegatives: number;
  duplicateDetections: number;
  precision: number;
  recall: number;
  f1Score: number;
  iouThreshold: number;
  meanIou: number;
  medianIou: number;
  minIou: number;
  maxIou: number;
  ap50?: number;
  ap75?: number;
  breakdownBySize?: Record<string, { gtCount: number; tpCount: number; recall: number }>;
  breakdownByOcclusion?: Record<string, { gtCount: number; tpCount: number; recall: number }>;
}

export interface TrackingEvaluationMetrics {
  totalGtTracks: number;
  totalPredTracks: number;
  idSwitches: number;
  trackFragmentations: number;
  trackContinuityRatio: number;
  meanTrackDurationSec: number;
  missedObservations: number;
  detectionErrors: number;
  trackingErrors: number;
  mota?: number;
  motp?: number;
  statement: string;
}

export interface IdentityEvaluationMetrics {
  evaluationStatus: string;
  totalEvaluated: number;
  correctCount: number;
  incorrectCount: number;
  unknownCount: number;
  notAnnotatedCount: number;
  identityAccuracy?: number;
  unknownRate?: number;
  incorrectRate?: number;
  statement: string;
}

export interface CrossModalEvaluationMetrics {
  evaluationStatus: string;
  totalEventsEvaluated: number;
  meanAbsoluteDifferenceSec?: number;
  medianDifferenceSec?: number;
  maxDifferenceSec?: number;
  uncertaintyIntervalSec?: number;
  alignedCount: number;
  partiallyAlignedCount: number;
  misalignedCount: number;
  statement: string;
}

export interface IncidentVisualEvidenceSufficiency {
  candidateId: string;
  videoAvailable: boolean;
  synchronizationValid: boolean;
  vehiclesDetected: boolean;
  tracksContinuous: boolean;
  identitiesAvailable: boolean;
  visualInteractionFeaturesAvailable: boolean;
  telemetryAlignmentAvailable: boolean;
  stewardReadiness: StewardReadinessRating;
  evaluationSummary: string;
  limitations: string[];
}

export interface CVEvaluationSuiteResponse {
  realVideoStatus: string;
  evaluationStatus: string;
  datasetStateClassification: string;
  detectionMetrics?: DetectionEvaluationMetrics;
  trackingMetrics?: TrackingEvaluationMetrics;
  identityMetrics: IdentityEvaluationMetrics;
  crossModalMetrics: CrossModalEvaluationMetrics;
  failureCategories: Record<string, number>;
  modelBenchmarks: Record<string, any>;
  performance: Record<string, any>;
  provenanceSummary: string;
  stewardNotice: string;
}

// ==============================================================================
// STEWARD EVIDENCE DOSSIER & MULTI-MODAL SYNTHESIS (PROMPT 16)
// ==============================================================================

export enum EvidenceType {
  TELEMETRY = 'TELEMETRY',
  REFERENCE_BASELINE = 'REFERENCE_BASELINE',
  OVERTAKE_GEOMETRY = 'OVERTAKE_GEOMETRY',
  ML_INTERACTION = 'ML_INTERACTION',
  VIDEO_SYNCHRONIZATION = 'VIDEO_SYNCHRONIZATION',
  VISUAL = 'VISUAL',
  COMPUTER_VISION = 'COMPUTER_VISION',
  REGULATION = 'REGULATION',
}

export enum EvidenceStatus {
  OBSERVED = 'OBSERVED',
  DERIVED = 'DERIVED',
  MODEL_DERIVED = 'MODEL_DERIVED',
  DOCUMENTARY = 'DOCUMENTARY',
  UNAVAILABLE = 'UNAVAILABLE',
}

export enum ConsistencyStatus {
  CONSISTENT = 'CONSISTENT',
  PARTIALLY_CONSISTENT = 'PARTIALLY_CONSISTENT',
  CONFLICTING = 'CONFLICTING',
  INSUFFICIENT_DATA = 'INSUFFICIENT_DATA',
}

export enum DiscrepancySeverity {
  LOW = 'LOW',
  MEDIUM = 'MEDIUM',
  HIGH = 'HIGH',
  UNRESOLVED = 'UNRESOLVED',
}

export interface DossierEvidenceItem {
  evidenceId: string;
  evidenceType: EvidenceType;
  sourceLayer: string;
  status: EvidenceStatus;
  observation: string;
  value?: any;
  unit?: string;
  timestamp?: string;
  eventRelativeTimeSec?: number;
  confidenceOrQuality?: string;
  measurementBasis: string;
  provenance: string;
  limitations: string[];
  parentEvidenceIds: string[];
}

export interface EvidenceQualityRecord {
  streamName: string;
  status: EvidenceStatus;
  reliabilityScore: number;
  dataCompleteness: string;
  calibrationOrSyncMargin?: string;
  limitations: string[];
}

export interface CrossModalDiscrepancy {
  discrepancyId: string;
  evidenceStreamA: string;
  evidenceStreamB: string;
  metric: string;
  observedDifference: string;
  expectedTolerance: string;
  severity: DiscrepancySeverity;
  status: string;
  explanation: string;
  provenance: string;
}

export interface EvidenceConsensus {
  supportingEvidenceStreams: string[];
  conflictingEvidenceStreams: string[];
  unavailableEvidenceStreams: string[];
  independentObservationCount: number;
  totalEvidenceItems: number;
  consensusSummary: string;
  stewardInspectionGuidance: string;
}

export interface NormalizedTimelineEvent {
  timestamp: string;
  eventRelativeTimeSec: number;
  source: string;
  description: string;
  evidenceStatus: EvidenceStatus;
  provenance: string;
  evidenceRef?: string;
}

export interface DescriptiveRegulationLink {
  document: string;
  article: string;
  title: string;
  summary: string;
  relevantEvidenceIds: string[];
  temporalValidity: string;
  spatialValidity: string;
  provenanceSource: string;
  evaluationStatus: string;
}

export interface StewardEvidenceDossier {
  dossierId: string;
  candidateId: string;
  incidentId?: string;
  sessionId: string;
  eventType: string;
  lapNumber: number;
  turn: string;
  generatedAt: string;
  dossierVersion: string;
  analysisVersion: string;
  driverA: string;
  driverB: string;
  carNumberA?: string;
  carNumberB?: string;
  teamA?: string;
  teamB?: string;
  reviewStatus: string;
  reviewerId?: string;
  reviewNotes?: string;
  timeline: NormalizedTimelineEvent[];
  evidenceItems: DossierEvidenceItem[];
  streamQuality: EvidenceQualityRecord[];
  crossModalConsistency: ConsistencyStatus;
  consensus: EvidenceConsensus;
  discrepancies: CrossModalDiscrepancy[];
  regulations: DescriptiveRegulationLink[];
  limitations: string[];
  provenanceSummary: string;
  stewardDoctrine: string;
}

export interface DossierExportPayload {
  exportType: string;
  schemaVersion: string;
  exportedAt: string;
  dossier: StewardEvidenceDossier;
}

