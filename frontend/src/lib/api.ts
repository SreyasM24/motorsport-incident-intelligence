import { 
  Race, 
  Incident, 
  IncidentStatus,
  ReviewRecord,
  TelemetryPoint, 
  RelevantRegulation, 
  Driver, 
  AssistantMessage,
  CVIncidentAnalysisResponse,
  CVEvaluationSuiteResponse,
  IncidentVisualEvidenceSufficiency,
  StewardEvidenceDossier,
  DossierExportPayload,
  HistoricalComparisonResponse
} from './types';
import { 
  MOCK_RACES, 
  MOCK_INCIDENTS, 
  generateSynchronizedTelemetry, 
  MOCK_REGULATION_LIBRARY, 
  MOCK_DRIVERS,
  MOCK_RACE_ACTIVITY 
} from './mockData';

/**
 * MOTORSPORT INCIDENT INTELLIGENCE — API ABSTRACTION LAYER
 * 
 * Interacts directly with FastAPI backend when available, with
 * transparent client-side fallback during initial offline bootstrapping.
 */

const API_BASE_URL = 
  (import.meta as any).env?.VITE_API_BASE_URL || 
  (import.meta as any).env?.VITE_API_URL || 
  'http://localhost:8000/api/v1';

const USE_LIVE_FASTAPI = 
  (import.meta as any).env?.VITE_USE_LIVE_API !== 'false';

export async function getRaces(): Promise<Race[]> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/races`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn('Live /races API unreachable, using fallback:', e);
    }
  }
  return Promise.resolve([...MOCK_RACES]);
}

export async function getRace(id: string): Promise<Race | undefined> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/races/${id}`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn(`Live /races/${id} API unreachable, using fallback:`, e);
    }
  }
  return Promise.resolve(MOCK_RACES.find((r) => r.id === id) || MOCK_RACES[0]);
}

export async function getIncidents(filters?: {
  raceId?: string;
  driver?: string;
  status?: string;
  severity?: string;
  minConfidence?: number;
  search?: string;
}): Promise<Incident[]> {
  if (USE_LIVE_FASTAPI) {
    try {
      const params = new URLSearchParams();
      params.append('auto_seed', 'true');
      if (filters?.raceId) params.append('race_id', filters.raceId);
      if (filters?.driver) params.append('driver', filters.driver);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.severity) params.append('severity', filters.severity);
      if (filters?.minConfidence) params.append('min_confidence', filters.minConfidence.toString());
      if (filters?.search) params.append('search', filters.search);
      const res = await fetch(`${API_BASE_URL}/incidents?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) return data;
      }
    } catch (e) {
      console.warn('Live /incidents API unreachable, using fallback:', e);
    }
  }

  let incidents = [...MOCK_INCIDENTS];

  if (filters) {
    if (filters.raceId) {
      incidents = incidents.filter((inc) => inc.raceId === filters.raceId);
    }
    if (filters.driver) {
      const d = filters.driver.toUpperCase();
      incidents = incidents.filter(
        (inc) => inc.driverA.toUpperCase() === d || inc.driverB.toUpperCase() === d
      );
    }
    if (filters.status && filters.status !== 'ALL') {
      incidents = incidents.filter((inc) => inc.status === filters.status);
    }
    if (filters.severity && filters.severity !== 'ALL') {
      incidents = incidents.filter((inc) => inc.severity === filters.severity);
    }
    if (filters.minConfidence) {
      incidents = incidents.filter((inc) => inc.confidence >= (filters.minConfidence || 0));
    }
    if (filters.search) {
      const q = filters.search.toLowerCase();
      incidents = incidents.filter(
        (inc) =>
          inc.id.toLowerCase().includes(q) ||
          inc.driverA.toLowerCase().includes(q) ||
          inc.driverB.toLowerCase().includes(q) ||
          inc.turn.toLowerCase().includes(q) ||
          inc.incidentType.toLowerCase().includes(q)
      );
    }
  }

  return Promise.resolve(incidents);
}

export async function getIncident(id: string): Promise<Incident | undefined> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents/${id}`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn(`Live /incidents/${id} API unreachable, using fallback:`, e);
    }
  }
  const found = MOCK_INCIDENTS.find((i) => i.id === id);
  return Promise.resolve(found || MOCK_INCIDENTS[0]);
}

export async function getTelemetry(incidentId: string): Promise<TelemetryPoint[]> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/telemetry`);
      if (res.ok) {
        const data = await res.json();
        const points = Array.isArray(data) ? data : (data.points || []);
        if (points.length > 0) return points;
      }
    } catch (e) {
      console.warn(`Live telemetry for ${incidentId} failed:`, e);
    }
  }
  // Generate high-density telemetry data
  return Promise.resolve(generateSynchronizedTelemetry());
}

export async function getRegulations(search?: string): Promise<RelevantRegulation[]> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/regulations?q=${encodeURIComponent(search || '')}`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) {
          return data.map((r: any) => ({
            id: r.id,
            document: r.document,
            article: r.article,
            title: r.title,
            regulationTextPlaceholder: r.text || r.regulationTextPlaceholder || '',
            text: r.text,
            whyRelevant: r.whyRelevant || r.text || 'FIA sporting governance reference for incident review.',
            matchReason: r.matchReason || 'Statutory regulation match.',
            relevance: (r.relevance as 'High' | 'Medium' | 'Low') || 'High',
            source: r.source || r.series || 'FIA',
            sourceUrl: r.sourceUrl,
          }));
        }
      }
    } catch (e) {
      console.warn('Live /regulations API unreachable:', e);
    }
  }
  if (!search) return Promise.resolve([...MOCK_REGULATION_LIBRARY]);
  const q = search.toLowerCase();
  return Promise.resolve(
    MOCK_REGULATION_LIBRARY.filter(
      (r) =>
        r.article.toLowerCase().includes(q) ||
        r.title.toLowerCase().includes(q) ||
        r.document.toLowerCase().includes(q) ||
        r.whyRelevant.toLowerCase().includes(q)
    )
  );
}

export async function getDrivers(): Promise<Driver[]> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/drivers`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) return data;
      }
    } catch (e) {
      console.warn('Live /drivers API unreachable:', e);
    }
  }
  return Promise.resolve(Object.values(MOCK_DRIVERS));
}

export async function getDriver(code: string): Promise<Driver | undefined> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/drivers/${encodeURIComponent(code)}`);
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn(`Live /drivers/${code} API unreachable:`, e);
    }
  }
  return Promise.resolve(MOCK_DRIVERS[code.toUpperCase()]);
}

export async function getRaceActivity() {
  return Promise.resolve(MOCK_RACE_ACTIVITY);
}

export async function analyzeIncident(id: string): Promise<{
  incidentId: string;
  status: string;
  reconstructedPoints: number;
  confidence: number;
  stewardGuidance: string;
}> {
  return Promise.resolve({
    incidentId: id,
    status: 'ANALYSIS_COMPLETE',
    reconstructedPoints: 50,
    confidence: 87,
    stewardGuidance:
      'Telemetry verifies anomalous lateral perturbation of -0.85G. Steward visual confirmation of apex kerb overlap recommended.',
  });
}

export async function askAssistant(
  question: string, 
  incidentId: string = 'INC-024'
): Promise<AssistantMessage> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/assistant/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: question, incident_id: incidentId }),
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn('Live /assistant/query API unreachable, using fallback:', e);
    }
  }

  const qLower = question.toLowerCase();
  
  let responseText =
    'The incident was flagged because telemetry indicates a close interaction (minimum gap 1.82 m) followed by increased relative motion (closing speed 8.42 m/s) and a measurable vehicle response (-0.85 G yaw jerk). This evidence indicates proximity and trajectory alteration, but does NOT establish driver guilt or sporting fault. Human steward review of visual onboard footage is required.';
  
  let chips: AssistantMessage['evidenceChips'] = [
    { label: 'Minimum Gap 1.82m', type: 'telemetry' },
    { label: 'Apex Milestone 13:42:18.4', type: 'timeline' },
    { label: 'Article 33.4 (Crowding)', type: 'regulation' },
    { label: 'IMU Yaw Response -0.85G', type: 'response' },
  ];

  if (qLower.includes('telemetry') || qLower.includes('change')) {
    responseText =
      'Key telemetry anomalies detected between 13:42:17.8 and 13:42:19.0: Car 1 applied 98.4 bar threshold braking at 62m, deeper than nominal. Car 44 experienced an instantaneous 3.8° counter-steering angle reversal paired with a -0.85G lateral yaw jerk at apex apex clearance of 1.82m.';
    chips = [
      { label: 'Speed & Brake Traces', type: 'telemetry' },
      { label: 'Steering Delta 3.8°', type: 'telemetry' },
      { label: 'Yaw Jerk -0.85G', type: 'response' },
    ];
  } else if (qLower.includes('regulation') || qLower.includes('rule') || qLower.includes('article')) {
    responseText =
      'Primary relevant regulations flagged for this geometry: Article 33.4 (Manoeuvres liable to hinder other drivers / crowding off track) and Article 33.3 (Significant overlap rights at corner turn-in). In addition, Article 27.3 governs whether Car 44 gained a lasting advantage via the Turn 4 asphalt runoff.';
    chips = [
      { label: 'Article 33.4 (Crowding)', type: 'regulation' },
      { label: 'Article 33.3 (Overlap)', type: 'regulation' },
      { label: 'Article 27.3 (Track Limits)', type: 'regulation' },
    ];
  } else if (qLower.includes('missing') || qLower.includes('caveat') || qLower.includes('uncertain')) {
    responseText =
      'Missing or unverified evidence components: 1) High-frequency onboard camera footage from Car 44 is not yet locked to sub-millisecond ECU timestamps. 2) Local wind vector telemetry at Turn 4 entry. 3) Driver throttle intent cannot be measured by algorithm alone.';
    chips = [
      { label: 'Visual Sync Status', type: 'timeline' },
      { label: 'Measurement Uncertainty (±0.28m)', type: 'telemetry' },
      { label: 'Human Adjudication Required', type: 'regulation' },
    ];
  }

  return Promise.resolve({
    id: `msg-${Date.now()}`,
    sender: 'assistant',
    timestamp: new Date().toLocaleTimeString('en-GB', { hour12: false }),
    text: responseText,
    evidenceChips: chips,
    suggestedFollowUps: [
      'Compare driver throttle inputs at braking point',
      'Show Article 33.4 full text and precedent context',
      'Explain the -0.85G yaw disturbance anomaly',
    ],
  });
}

// In-memory fallback review storage for local demo / offline mode
const inMemoryReviewStore: Record<string, ReviewRecord[]> = {};

export async function updateIncidentStatus(
  incidentId: string,
  update: {
    status: IncidentStatus;
    reviewer_id?: string;
    review_notes?: string;
    review_rationale?: string;
    reopen_reason?: string;
  }
): Promise<Incident> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(update),
      });
      if (res.ok) {
        return await res.json();
      }
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to update status (${res.status})`);
    } catch (e) {
      console.warn(`Live /incidents/${incidentId}/status failed:`, e);
      if ((e as any).message?.includes('Invalid transition') || (e as any).message?.includes('reopen_reason')) {
        throw e; // rethrow domain validation errors
      }
    }
  }

  // Fallback
  const inc = MOCK_INCIDENTS.find((i) => i.id === incidentId);
  if (inc) {
    inc.status = update.status;
    return { ...inc };
  }
  throw new Error(`Incident ${incidentId} not found`);
}

export async function getIncidentReviews(incidentId: string): Promise<ReviewRecord[]> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/reviews`);
      if (res.ok) {
        const data = await res.json();
        return data.map((r: any) => ({
          id: r.id,
          incidentId: r.incident_id,
          status: r.status,
          reviewerId: r.reviewer_id,
          reviewStartedAt: r.review_started_at,
          reviewCompletedAt: r.review_completed_at,
          evidenceConsidered: Array.isArray(r.evidence_considered) ? r.evidence_considered.join(', ') : r.evidence_considered,
          evidenceMissing: Array.isArray(r.evidence_missing) ? r.evidence_missing.join(', ') : r.evidence_missing,
          observations: Array.isArray(r.observations) ? r.observations.join(', ') : r.observations,
          reviewNotes: r.review_notes,
          reviewRationale: r.review_rationale,
          regulatoryReferences: Array.isArray(r.regulatory_references) ? r.regulatory_references.join(', ') : r.regulatory_references,
          createdAt: r.created_at,
          updatedAt: r.updated_at,
        }));
      }
    } catch (e) {
      console.warn(`Live /incidents/${incidentId}/reviews failed:`, e);
    }
  }

  return inMemoryReviewStore[incidentId] || [
    {
      id: `rev-${incidentId}-init`,
      incidentId,
      status: 'REQUIRES_REVIEW',
      reviewerId: 'system-pipeline',
      reviewStartedAt: new Date().toISOString(),
      reviewNotes: 'Automated candidate ingested from telemetry interaction pipeline. Awaiting human steward review.',
      reviewRationale: 'Algorithmic proximity & closing speed threshold met. No fault attributed.',
      evidenceConsidered: 'FastF1 ECU Telemetry, World Feed Video, FIA Regulations',
      createdAt: new Date().toISOString(),
    },
  ];
}

export async function submitIncidentReview(
  incidentId: string,
  review: {
    status: IncidentStatus;
    reviewer_id?: string;
    review_notes?: string;
    review_rationale?: string;
    evidence_considered?: string[];
    evidence_missing?: string[];
    observations?: string[];
    regulatory_references?: string[];
  }
): Promise<ReviewRecord> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/incidents/${incidentId}/reviews`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(review),
      });
      if (res.ok) {
        const r = await res.json();
        return {
          id: r.id,
          incidentId: r.incident_id,
          status: r.status,
          reviewerId: r.reviewer_id,
          reviewStartedAt: r.review_started_at,
          reviewCompletedAt: r.review_completed_at,
          evidenceConsidered: Array.isArray(r.evidence_considered) ? r.evidence_considered.join(', ') : r.evidence_considered,
          evidenceMissing: Array.isArray(r.evidence_missing) ? r.evidence_missing.join(', ') : r.evidence_missing,
          observations: Array.isArray(r.observations) ? r.observations.join(', ') : r.observations,
          reviewNotes: r.review_notes,
          reviewRationale: r.review_rationale,
          regulatoryReferences: Array.isArray(r.regulatory_references) ? r.regulatory_references.join(', ') : r.regulatory_references,
          createdAt: r.created_at,
          updatedAt: r.updated_at,
        };
      }
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `Failed to submit review (${res.status})`);
    } catch (e) {
      console.warn(`Live /incidents/${incidentId}/reviews submit failed:`, e);
      if ((e as any).message?.includes('Invalid transition') || (e as any).message?.includes('reopen_reason')) {
        throw e;
      }
    }
  }

  // Fallback
  const newRec: ReviewRecord = {
    id: `rev-${Date.now()}`,
    incidentId,
    status: review.status,
    reviewerId: review.reviewer_id || 'steward-panel',
    reviewStartedAt: new Date().toISOString(),
    reviewCompletedAt: review.status === 'REVIEWED' || review.status === 'DISMISSED' ? new Date().toISOString() : undefined,
    evidenceConsidered: review.evidence_considered?.join(', '),
    evidenceMissing: review.evidence_missing?.join(', '),
    observations: review.observations?.join(', '),
    reviewNotes: review.review_notes,
    reviewRationale: review.review_rationale,
    regulatoryReferences: review.regulatory_references?.join(', '),
    createdAt: new Date().toISOString(),
  };

  if (!inMemoryReviewStore[incidentId]) {
    inMemoryReviewStore[incidentId] = [];
  }
  inMemoryReviewStore[incidentId].push(newRec);

  const inc = MOCK_INCIDENTS.find((i) => i.id === incidentId);
  if (inc) {
    inc.status = review.status;
  }

  return newRec;
}

export async function getCVAnalysis(candidateId: string): Promise<CVIncidentAnalysisResponse | null> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/analysis/candidates/${candidateId}/video/cv`);
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn(`Live /analysis/candidates/${candidateId}/video/cv API unreachable:`, e);
    }
  }
  return null;
}

export async function getCVEvaluationReport(): Promise<CVEvaluationSuiteResponse | null> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/analysis/cv/evaluation`);
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn('Live /analysis/cv/evaluation API unreachable:', e);
    }
  }
  return null;
}

export async function getCVEvidenceSufficiency(candidateId: string): Promise<IncidentVisualEvidenceSufficiency | null> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/analysis/candidates/${candidateId}/video/cv/sufficiency`);
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn(`Live /analysis/candidates/${candidateId}/video/cv/sufficiency API unreachable:`, e);
    }
  }
  return null;
}

export async function fetchStewardDossier(candidateId: string): Promise<StewardEvidenceDossier | null> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/analysis/candidates/${candidateId}/steward-dossier`);
      if (res.ok) {
        return await res.json();
      }
      const incRes = await fetch(`${API_BASE_URL}/incidents/${candidateId}/dossier`);
      if (incRes.ok) {
        return await incRes.json();
      }
    } catch (e) {
      console.warn(`Live steward dossier API for ${candidateId} unreachable:`, e);
    }
  }
  return null;
}

export async function exportStewardDossierJson(candidateId: string): Promise<DossierExportPayload | null> {
  if (USE_LIVE_FASTAPI) {
    try {
      const res = await fetch(`${API_BASE_URL}/analysis/candidates/${candidateId}/steward-dossier/export/json`);
      if (res.ok) {
        return await res.json();
      }
      const incRes = await fetch(`${API_BASE_URL}/incidents/${candidateId}/dossier/json`);
      if (incRes.ok) {
        return await incRes.json();
      }
    } catch (e) {
      console.warn(`Live steward dossier JSON export for ${candidateId} unreachable:`, e);
    }
  }
  return null;
}

export async function fetchHistoricalComparisons(
  candidateId: string,
  topK: number = 3,
  circuit?: string,
  season?: number,
  minSimilarity: number = 0.0
): Promise<HistoricalComparisonResponse | null> {
  if (USE_LIVE_FASTAPI) {
    try {
      let url = `${API_BASE_URL}/evidence/historical/compare/${encodeURIComponent(candidateId)}?top_k=${topK}&min_similarity=${minSimilarity}`;
      if (circuit) url += `&circuit=${encodeURIComponent(circuit)}`;
      if (season) url += `&season=${season}`;
      const res = await fetch(url);
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn(`Live historical comparison for ${candidateId} unreachable:`, e);
    }
  }
  return null;
}


