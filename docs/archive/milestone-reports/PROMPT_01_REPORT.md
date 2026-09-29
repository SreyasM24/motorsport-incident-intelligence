# PHASE 1 TECHNICAL AUDIT & BACKEND INTEGRATION CONTRACT
**Project:** Motorsport Incident Intelligence (MII)  
**System:** AI-Powered Evidence Intelligence for Motorsport (Decision Support for Human Stewards)  
**Report Document:** `docs/progress/PROMPT_01_REPORT.md`  
**Date:** September 2026  
**Auditor:** AI Engineering Assistant (Antigravity)

---

## 1. Frontend Framework

- **Core Library & Version:** React 19 (`react: ^19.0.1`, `react-dom: ^19.0.1`).
- **Build Tool & Bundler:** Vite 6 (`vite: ^6.2.3`, `@vitejs/plugin-react: ^5.0.4`).
- **Styling Architecture:** Tailwind CSS v4 (`tailwindcss: ^4.1.14`, `@tailwindcss/vite: ^4.1.14`).
- **Language & Type System:** TypeScript 5.8 (`typescript: ~5.8.2`, ES2022 target, `bundler` module resolution).
- **Visualization Library:** Recharts (`recharts: ^3.10.1`) utilizing responsive line, area, and bar charts for telemetry and incident activity distributions.
- **Icons & Motion:** Lucide React (`lucide-react: ^0.546.0`) and Motion (`motion: ^12.23.24`).
- **Routing Strategy:** Single-Page Application (SPA) with declarative view state switching managed in `src/App.tsx` (`currentView`: `'landing' | 'dashboard' | 'races' | 'incidents' | 'incident-detail' | 'regulations' | 'assistant'`).

---

## 2. Frontend Folder Structure

```
Motorsport-Incident-Intelligence/
├── .antigravity/                     # Antigravity agent & IDE workspace metadata
├── .vscode/                          # Editor configuration
├── public/                           # Static assets served at root
│   ├── assets/                       # Subfolder for video & static assets
│   ├── this-is-formula-one.mp4       # Primary 1080p Formula 1 video asset
│   └── This is Formula One...mp4     # Original uploaded video asset
├── src/                              # Application source tree
│   ├── components/                   # Modular UI & technical domain components
│   │   ├── DriverModal.tsx           # Driver bio, team colors & session telemetry stats
│   │   ├── EvidencePanel.tsx         # Categorized empirical evidence accordion
│   │   ├── EvidenceRegulationFlow.tsx# 3-step pipeline: Evidence ↔ Regulation ↔ Steward Action
│   │   ├── GlobalSearchModal.tsx     # Cmd+K global search across incidents, drivers, rules
│   │   ├── HeroVideoBackground.tsx   # Dual-video seamless 00:05 crossfading hero video engine
│   │   ├── IncidentTimeline.tsx      # Dual-mode timeline (race dashboard & incident milestones)
│   │   ├── RaceHeader.tsx            # Sticky top bar with UTC clock, session pill & search trigger
│   │   ├── RegulationPanel.tsx       # Sporting regulations accordion with match rationale
│   │   ├── Sidebar.tsx               # Persistent dark motorsport sidebar navigation
│   │   ├── SystemPipeline.tsx        # Ingest-to-adjudication pipeline visualization card
│   │   ├── TelemetryChart.tsx        # Multi-trace 25Hz synchronized telemetry chart (Speed, Pedals, Gap, G-force)
│   │   ├── UncertaintyCaveats.tsx    # Mandatory evidentiary limitations notice
│   │   └── VideoPlayer.tsx           # Frame-stepping, scrubber & 00:05-looping video player
│   ├── lib/                          # Data layer, contracts & mock data
│   │   ├── api.ts                    # API client abstraction with FastAPI toggle
│   │   ├── mockData.ts               # Offline mock datasets (races, incidents, telemetry, rules)
│   │   └── types.ts                  # Shared TypeScript interfaces for all domain entities
│   ├── views/                        # Full-screen operational views
│   │   ├── AssistantView.tsx         # Dedicated AI Steward Assistant conversational view
│   │   ├── DashboardView.tsx         # Race control dashboard with telemetry activity distribution
│   │   ├── IncidentDetailView.tsx    # 8-part linear evidentiary investigation workspace
│   │   ├── IncidentsView.tsx         # Incident Explorer filterable table
│   │   ├── LandingView.tsx           # Cinematic public portal & system architecture showcase
│   │   ├── RacesView.tsx             # F1 calendar & session archive repository
│   │   └── RegulationsView.tsx       # FIA sporting code & driving conduct search library
│   ├── App.tsx                       # Root view router & global state orchestrator
│   ├── index.css                     # Global styles, Tailwind v4 imports, custom font faces
│   └── main.tsx                      # DOM entry point mounting App to #root
├── .env                              # Local runtime environment variables
├── .env.example                      # Template documentation of required environment variables
├── .gitignore                        # Git exclusion rules
├── bun.lock                          # Dependency lockfile
├── index.html                        # HTML shell with fonts (Chakra Petch, JetBrains Mono, Plus Jakarta Sans)
├── metadata.json                     # AI Studio capability metadata
├── package.json                      # NPM dependencies and run scripts
├── tsconfig.json                     # TypeScript compilation configuration
└── vite.config.ts                    # Vite build configuration with Tailwind plugin
```

---

## 3. Pages Discovered

| View ID in `App.tsx` | View Component | File Location | Purpose & Core Content |
|---|---|---|---|
| `landing` | `LandingView` | `src/views/LandingView.tsx` | Full-viewport cinematic homepage with seamless background video (`this-is-formula-one.mp4`), brand philosophy (*"AI assists. Evidence supports. Humans decide."*), 7-step engine pipeline, and intelligence inputs summary. |
| `dashboard` | `DashboardView` | `src/views/DashboardView.tsx` | Race Control Session Overview (Italian GP 2024), 4 headline metrics (Drivers, Candidates, Requires Review, Reviewed), 53-lap incident activity bar chart, horizontal session timeline, pipeline status card, and top 5 priority incidents table. |
| `races` | `RacesView` | `src/views/RacesView.tsx` | Archive of championship seasons (2024, 2023) and Grands Prix, circuit details, session feeds (FP1, FP2, FP3, Quali, Race), with "VIEW SESSION" entry. |
| `incidents` | `IncidentsView` | `src/views/IncidentsView.tsx` | Incident Explorer with search, driver filter, status filter, confidence slider, and standardized table rendering incident records with a direct "VIEW" action. |
| `incident-detail` | `IncidentDetailView` | `src/views/IncidentDetailView.tsx` | Primary investigation workspace organized strictly into 8 linear evidence sections (Header, Video, Timeline, Telemetry, Evidence Assessment, Relevant Regulations, Uncertainty Caveats, AI Steward Assistant). |
| `regulations` | `RegulationsView` | `src/views/RegulationsView.tsx` | Searchable FIA Sporting Regulations & ISC Appendix L repository, categorized by Series, Season, Document, and Article with sample text disclosures. |
| `assistant` | `AssistantView` | `src/views/AssistantView.tsx` | Full-page AI Steward Assistant interface for natural-language evidentiary inquiries, structured evidence badges (`TELEMETRY`, `VIDEO`, `REGULATION`, `TRAJECTORY`, `RESPONSE`), and cross-links to incident details. |

---

## 4. Major Components

1. **`HeroVideoBackground` (`src/components/HeroVideoBackground.tsx`)**:
   - Implements an autonomous dual-video looping engine that strictly enforces `00:05 -> END -> crossfade -> 00:05`.
   - Never exposes the initial 00:00–00:04.999 intro frame.
   - Features radial dark vignette, subtle telemetry scanlines, and audio unmute/mute toggle.
2. **`VideoPlayer` (`src/components/VideoPlayer.tsx`)**:
   - Technical visual evidence player with frame-stepping (`-1F` / `+1F`), 0.25x–2.0x playback rates, scrubber, fullscreen, and incident time window HUD overlay (`13:42:17.8 — 13:42:20.4`).
   - Also enforces the 5-second offset rule and displays a fallback state if video is not yet linked.
3. **`TelemetryChart` (`src/components/TelemetryChart.tsx`)**:
   - 25Hz multi-channel synchronized graph (Speed, Throttle/Brake pedals, Interaction Gap & Closing Velocity, Steering Angle & Acceleration).
   - Driver toggle: Both Cars, Driver A only, Driver B only.
   - Channel filter: All, Speed, Pedals, Gap/Speed, Accel.
   - Hover scrubbing synched with incident timestamp.
4. **`EvidencePanel` (`src/components/EvidencePanel.tsx`)**:
   - Accordion displaying empirical observations across 5 categories: `PROXIMITY`, `RELATIVE_MOTION`, `VEHICLE_RESPONSE`, `TRAJECTORY`, `BRAKING`.
   - Renders observed values, baseline context, confidence score, and sensor source.
5. **`RegulationPanel` (`src/components/RegulationPanel.tsx`)**:
   - Collapsible FIA Sporting Code articles cross-referenced against incident telemetry.
   - Displays article number, title, match rationale, relevance rating (`High` / `Medium`), and excerpt text.
6. **`EvidenceRegulationFlow` (`src/components/EvidenceRegulationFlow.tsx`)**:
   - Visual 3-stage connector linking: `01 Observed Evidence` → `02 Relevant Regulation` → `03 Steward Review Inquiry`.
7. **`UncertaintyCaveats` (`src/components/UncertaintyCaveats.tsx`)**:
   - Mandatory transparent disclosure highlighting sensor noise (e.g. ±0.28m GPS kerb noise), video timecode sync status, and the doctrine that telemetry reflects mechanical physics, not human intent.
8. **`IncidentTimeline` (`src/components/IncidentTimeline.tsx`)**:
   - Supports two modes: `race-dashboard` (horizontal multi-lap interactive incident bar) and `incident-detail` (microsecond chronological milestones from approach to exit).
9. **`DriverModal` (`src/components/DriverModal.tsx`)**:
   - Context modal showing driver number, team color accent, country, laps completed, average speed, max speed, and incidents involved.
10. **`RaceHeader` (`src/components/RaceHeader.tsx`)**:
    - Sticky top navigation with real-time UTC clock, championship series identifier, active session name, analysis status badge, and global search trigger.
11. **`GlobalSearchModal` (`src/components/GlobalSearchModal.tsx`)**:
    - `Cmd+K` keyboard-accessible modal searching incidents, drivers, regulations, and races.
12. **`Sidebar` (`src/components/Sidebar.tsx`)**:
    - Persistent dark desktop sidebar and mobile overlay drawer with live telemetry status and active investigation shortcut.
13. **`SystemPipeline` (`src/components/SystemPipeline.tsx`)**:
    - Processing pipeline card displaying latencies across FastF1 ingest, telemetry processing, incident reconstruction, evidence analysis, regulation retrieval, and steward review.

---

## 5. Existing API Calls & Current Abstraction

The existing API abstraction lives in `src/lib/api.ts`. It provides an asynchronous interface designed as a drop-in adapter for FastAPI:

```typescript
const API_BASE_URL = 
  (import.meta as any).env?.VITE_API_BASE_URL || 
  (import.meta as any).env?.VITE_API_URL || 
  'http://localhost:8000/api/v1';
const USE_LIVE_FASTAPI = false; // Toggle to true once FastAPI service is active
```

### Current Function Signatures & Implementations:
1. **`getRaces()`**: Returns `Promise<Race[]>`. Fetches `${API_BASE_URL}/races` if live, otherwise returns `MOCK_RACES`.
2. **`getRace(id)`**: Returns `Promise<Race | undefined>`. Fetches `${API_BASE_URL}/races/${id}` if live, otherwise finds in `MOCK_RACES`.
3. **`getIncidents(filters)`**: Returns `Promise<Incident[]>`. Filters include `raceId`, `driver`, `status`, `severity`, `minConfidence`, `search`. Fetches `${API_BASE_URL}/incidents?{params}` if live, otherwise filters `MOCK_INCIDENTS` client-side.
4. **`getIncident(id)`**: Returns `Promise<Incident | undefined>`. Fetches `${API_BASE_URL}/incidents/${id}` if live, otherwise finds in `MOCK_INCIDENTS`.
5. **`getTelemetry(incidentId)`**: Returns `Promise<TelemetryPoint[]>`. Fetches `${API_BASE_URL}/incidents/${incidentId}/telemetry` if live, otherwise runs `generateSynchronizedTelemetry()`.
6. **`getRegulations(search)`**: Returns `Promise<RelevantRegulation[]>`. Fetches `${API_BASE_URL}/regulations?q={query}` if live, otherwise filters `MOCK_REGULATION_LIBRARY`.
7. **`getDrivers()`**: Returns `Promise<Driver[]>`. Currently resolves `Object.values(MOCK_DRIVERS)` directly without a live fetch branch.
8. **`getDriver(code)`**: Returns `Promise<Driver | undefined>`. Currently resolves `MOCK_DRIVERS[code]` directly without a live fetch branch.
9. **`getRaceActivity()`**: Returns `Promise<any[]>`. Currently resolves `MOCK_RACE_ACTIVITY` directly.
10. **`analyzeIncident(id)`**: Returns `Promise<{ incidentId, status, reconstructedPoints, confidence, stewardGuidance }>`. Currently returns a mock resolution.
11. **`askAssistant(question, incidentId)`**: Returns `Promise<AssistantMessage>`. Currently provides mock rule-based logic.

---

## 6. Existing Mock & Hardcoded Data Inventory

To ensure clean migration without blind deletion, every piece of mock/hardcoded data has been audited and categorized:

| Category | File Location | Specific Variables / Content | Current Purpose | What Must Replace It |
|---|---|---|---|---|
| **Mock Data Store** | `src/lib/mockData.ts` (Lines 10–139) | `MOCK_DRIVERS` (VER, HAM, NOR, PIA, LEC, SAI, RUS, PER) | Driver records, team hex codes, and mock season stats | Dynamic driver objects from `GET /api/v1/sessions/{session_id}/drivers` |
| **Mock Data Store** | `src/lib/mockData.ts` (Lines 141–232) | `MOCK_RACES` (ita-2024, gbr-2024, bel-2024, mon-2024, abu-2024) | List of championship rounds and candidate incident counters | Championship calendar from `GET /api/v1/races` backed by FastF1 schedule |
| **Mock Data Store** | `src/lib/mockData.ts` (Lines 234–593) | `MOCK_INCIDENTS` (INC-024, INC-001, INC-002, INC-003, INC-004, INC-005) | Incident candidates, evidence items, regulation connections, and timeline milestones | Real candidate incident reconstructions from `GET /api/v1/sessions/{session_id}/incidents` |
| **Mock Data Store** | `src/lib/mockData.ts` (Lines 596–723) | `generateSynchronizedTelemetry()` | 50 synthetic data points modeling Turn 4 chicane interaction | Cleaned 25Hz telemetry slices from `GET /api/v1/incidents/{incident_id}/telemetry` |
| **Mock Data Store** | `src/lib/mockData.ts` (Lines 725–786) | `MOCK_REGULATION_LIBRARY` (Art 33.4, 33.3, 27.3, App L IV, App H) | Static placeholder excerpts of FIA rules | Indexed vector/semantic search results from `GET /api/v1/regulations` |
| **Mock Data Store** | `src/lib/mockData.ts` (Lines 806–818) | `MOCK_RACE_ACTIVITY` (Laps 1 to 53 candidate distributions) | Bar chart density distribution across race laps | Aggregated session telemetry interaction histogram from `GET /api/v1/sessions/{session_id}/activity` |
| **Component Hardcoding** | `src/views/DashboardView.tsx` (Lines 45–91) | `timelineIncidents` array | 5 hardcoded incidents on dashboard timeline | Sourced from `GET /api/v1/sessions/{session_id}/incidents?timeline=true` |
| **Component Hardcoding** | `src/views/DashboardView.tsx` (Lines 108–116) | "Italian Grand Prix 2024", "Monza (5.793 km)", "53 Laps" | Static session hero banner | Sourced from active session model `GET /api/v1/sessions/{session_id}` |
| **Component Hardcoding** | `src/views/DashboardView.tsx` (Lines 143, 153, 163, 178) | Counts: 20 drivers, 1,298 candidates, 3 requires review, 12 reviewed | Summary metric cards | Sourced from `GET /api/v1/sessions/{session_id}/summary` |
| **Component Hardcoding** | `src/components/TelemetryChart.tsx` (Lines 138, 145, 177, 178) | Reference points (`13:42:18.4`, `13:42:18.1`), "Impact Prob: 12%", "Relative Motion: CRITICAL" | Hardcoded annotations on chart | Sourced from incident telemetry metadata payload |
| **Component Hardcoding** | `src/components/Sidebar.tsx` (Lines 95, 112–127) | "3 REVIEW" badge, "Active Investigation: INC-024 Lap 31 T4 VER/HAM" | Static active investigation card | Sourced from active session review queue |
| **Component Hardcoding** | `src/components/RaceHeader.tsx` (Line 66) | `currentRaceName="ITALIAN GRAND PRIX • RACE"` | Static top bar session title | Driven by global `activeSession` state |
| **Component Hardcoding** | `src/views/IncidentsView.tsx` (Lines 126–133) | Hardcoded `<option>` tags for VER, HAM, NOR, PIA, LEC, SAI, RUS, PER | Driver filter dropdown options | Populated dynamically from `getDrivers(sessionId)` |
| **Component Hardcoding** | `src/components/GlobalSearchModal.tsx` (Line 3) | Direct import of `MOCK_INCIDENTS`, `MOCK_DRIVERS`, `MOCK_RACES`, `MOCK_REGULATION_LIBRARY` | In-memory search dataset | Sourced via API client search endpoints |
| **Component Hardcoding** | `src/views/AssistantView.tsx` (Lines 74–180) | Local hardcoded replies inside `handleSend` | Scripted query responses | Handled by `POST /api/v1/assistant/query` |

---

## 7. Data That Must Become Backend-Driven

1. **Championship Schedule & Sessions**: Season years, rounds, official Grand Prix names, circuits, track lengths, session types (FP1, FP2, FP3, Qualifying, Sprint, Race), dates, and ingest status.
2. **Driver Roster & Telemetry Attributes**: Official numbers, 3-letter codes, full names, constructor teams, livery colors (primary/secondary hex codes), and session stats (completed laps, speeds, incident count).
3. **Candidate Incident Stream**: Incident unique ID, session ID, lap number, turn number/name, timestamp (UTC and session elapsed time), time window (`start` to `end`), involved drivers (Driver A / Driver B), classification type, algorithmic correlation confidence (0–100%), review status (`DETECTED`, `ANALYZING`, `REQUIRES_REVIEW`, `UNDER_REVIEW`, `REVIEWED`), and severity.
4. **High-Frequency Synchronized Telemetry**: 20Hz–25Hz time-aligned telemetry channels for interacting vehicle pairs:
   - Speed ($km/h$)
   - Throttle ($0–100\%$)
   - Brake pressure ($bar$ or $0–100\%$)
   - Steering wheel angle ($degrees$)
   - Gear indicator ($1–8$)
   - Lateral/Longitudinal acceleration ($G$)
   - Spatial Gap ($m$)
   - Closing Velocity ($m/s$)
   - Lateral clearance delta ($m$)
   - Annotation timestamps (braking point, apex overlap, vehicle perturbation)
5. **Empirical Evidence Assessments**: Quantified observations with units, baseline context comparison, confidence score, and verified sensor source.
6. **Regulatory Retrievals & Precedents**: Indexed FIA Sporting Regulations and International Sporting Code articles, relevancy ratings, match rationale, and official text excerpts.
7. **Three-Way Evidence-Rule Mappings**: Explicit links between observed telemetry, relevant sporting articles, and human steward review inquiries.
8. **Sensor Caveats & Uncertainty Bands**: Documented instrumentation limitations (optical occlusion, GPS noise margins, unsynchronized clocks).
9. **AI Steward Assistant Context & Inference**: Dynamic query processing providing factual evidence summaries without ever declaring guilt or penalties.

---

## 8. Proposed Backend Endpoints (FastAPI Specification)

```
========================================================================================================================
METHOD  PATH                                              PURPOSE
========================================================================================================================
GET     /api/v1/health                                    Service health, FastF1 cache & OpenF1 connectivity status
GET     /api/v1/races                                     List all Grand Prix events for a given championship season
GET     /api/v1/races/{race_id}                           Get detailed metadata for a specific Grand Prix event
GET     /api/v1/races/{race_id}/sessions                  List all sessions (FP, Quali, Sprint, Race) for a Grand Prix
GET     /api/v1/sessions/{session_id}                     Get session overview, track conditions & backend ingest status
GET     /api/v1/sessions/{session_id}/summary             Get high-level metrics (drivers, candidates, review counts)
GET     /api/v1/sessions/{session_id}/activity            Get lap-by-lap incident candidate distribution for bar chart
GET     /api/v1/sessions/{session_id}/drivers             Get active driver transponder roster & session telemetry stats
GET     /api/v1/sessions/{session_id}/drivers/{code}      Get individual driver profile and session performance stats
GET     /api/v1/sessions/{session_id}/incidents           List incident candidates with filtering (driver, status, minConf)
GET     /api/v1/incidents/{incident_id}                   Get full incident dossier (milestones, evidence, regulations)
GET     /api/v1/incidents/{incident_id}/telemetry         Get synchronized 25Hz multi-driver telemetry timeseries slice
GET     /api/v1/regulations                               Search indexed FIA Sporting Regulations & Driving Code
GET     /api/v1/regulations/{regulation_id}               Get full text & match history for a specific regulation article
POST    /api/v1/assistant/query                           Submit conversational inquiry for an incident or session
PATCH   /api/v1/incidents/{incident_id}/status            Update human steward review status (e.g. UNDER_REVIEW → REVIEWED)
========================================================================================================================
```

### Detailed Endpoint Specifications

#### 1. `GET /api/v1/races`
- **Purpose**: Retrieve championship race events.
- **Parameters**: `season` (optional query string, default `"2024"`).
- **Response**: `200 OK` → `List[RaceSummaryResponse]`.
- **Empty Behavior**: Returns `[]` if season has no ingested races.

#### 2. `GET /api/v1/sessions/{session_id}/summary`
- **Purpose**: Feeds the 4 metric cards on the Race Dashboard.
- **Parameters**: `session_id` (path, string, e.g. `"ita-2024-race"`).
- **Response**: `200 OK` → `SessionSummaryResponse`:
  ```json
  {
    "sessionId": "ita-2024-race",
    "raceName": "Italian Grand Prix 2024",
    "circuit": "Autodromo Nazionale Monza",
    "driversCount": 20,
    "candidatesCount": 1298,
    "requiresReviewCount": 3,
    "reviewedCount": 12,
    "telemetryStatus": "CONNECTED",
    "incidentAnalysisStatus": "AVAILABLE",
    "regulationsStatus": "CONNECTED",
    "videoStatus": "NOT_LINKED",
    "aiAnalysisStatus": "IN_DEVELOPMENT"
  }
  ```

#### 3. `GET /api/v1/sessions/{session_id}/activity`
- **Purpose**: Feeds the Recharts bar chart in `DashboardView`.
- **Parameters**: `session_id` (path, string).
- **Response**: `200 OK` → `List[RaceActivityPoint]`:
  ```json
  [
    { "lap": 1, "candidates": 42, "abnormal": 14, "highConfidence": 2 },
    { "lap": 31, "candidates": 58, "abnormal": 26, "highConfidence": 4 }
  ]
  ```

#### 4. `GET /api/v1/sessions/{session_id}/incidents`
- **Purpose**: Feeds the Incident Explorer table in `IncidentsView` and the dashboard priority candidates table.
- **Parameters**:
  - `status` (query, optional: `REQUIRES_REVIEW`, `UNDER_REVIEW`, `REVIEWED`, `DETECTED`, `ALL`)
  - `driver` (query, optional: e.g. `VER`, `HAM`)
  - `min_confidence` (query, optional: integer $0–100$)
  - `search` (query, optional: string)
  - `limit` (query, optional: integer, default $50$)
- **Response**: `200 OK` → `IncidentListResponse` (`items: List[IncidentSummary], total: int`).

#### 5. `GET /api/v1/incidents/{incident_id}`
- **Purpose**: Feeds `IncidentDetailView` (Sections 1, 2, 3, 5, 6, 7).
- **Parameters**: `incident_id` (path, string, e.g. `"INC-024"`).
- **Response**: `200 OK` → `IncidentDetailResponse`.
- **Error Response**: `404 Not Found` if incident ID does not exist.

#### 6. `GET /api/v1/incidents/{incident_id}/telemetry`
- **Purpose**: Feeds the synchronized multi-channel `TelemetryChart`.
- **Parameters**:
  - `incident_id` (path, string)
  - `hz` (query, optional, default `25`)
  - `pad_seconds` (query, optional, default `3.0`)
- **Response**: `200 OK` → `TelemetrySliceResponse`:
  ```json
  {
    "incidentId": "INC-024",
    "driverA": "VER",
    "driverB": "HAM",
    "referenceTimestamp": "13:42:18.4",
    "incidentWindow": { "start": "13:42:17.8", "end": "13:42:20.4" },
    "points": [ ... ]
  }
  ```

#### 7. `POST /api/v1/assistant/query`
- **Purpose**: Context-aware evidentiary Q&A for human stewards.
- **Request Body**:
  ```json
  {
    "query": "Why was this incident flagged?",
    "incidentId": "INC-024",
    "sessionId": "ita-2024-race"
  }
  ```
- **Response**: `200 OK` → `AssistantQueryResponse`:
  ```json
  {
    "id": "msg-1727440000",
    "sender": "assistant",
    "timestamp": "13:42:26",
    "text": "Incident #024 was flagged due to...",
    "evidenceChips": [
      { "label": "TELEMETRY: Min Gap 1.82m", "type": "telemetry" },
      { "label": "REGULATION: Article 33.4", "type": "regulation" }
    ],
    "suggestedFollowUps": [ "What changed in the telemetry?" ]
  }
  ```

---

## 9. Proposed Request & Response Schemas (Pydantic / TypeScript Types)

To guarantee type safety across the boundary, the FastAPI Pydantic models and frontend TypeScript types map 1:1:

### Telemetry Point Contract
```python
# backend/app/schemas/telemetry.py
from pydantic import BaseModel, Field

class TelemetryPointSchema(BaseModel):
    time_offset: float = Field(..., description="Seconds offset from start of window")
    timestamp: str = Field(..., description="Formatted UTC time, e.g. 13:42:18.4")
    # Driver A
    speed_a: float = Field(..., description="Vehicle speed in km/h")
    throttle_a: float = Field(..., ge=0, le=100, description="Throttle position 0-100%")
    brake_a: float = Field(..., ge=0, le=100, description="Brake pressure/pedal 0-100%")
    steer_a: float = Field(..., description="Steering wheel angle in degrees")
    gear_a: int = Field(..., ge=0, le=8, description="Current gear")
    accel_a: float = Field(..., description="Lateral/Longitudinal acceleration G")
    # Driver B
    speed_b: float
    throttle_b: float
    brake_b: float
    steer_b: float
    gear_b: int
    accel_b: float
    # Relative Motion Dynamics
    gap_meters: float = Field(..., description="Calculated 3D proximity distance in meters")
    closing_speed_ms: float = Field(..., description="Closing speed in m/s (1st derivative)")
    lateral_dist_meters: float = Field(..., description="Lateral separation in meters")
```

### TypeScript Telemetry Equivalent
```typescript
// src/lib/types.ts
export interface TelemetryPoint {
  timeOffset: number;
  timestamp: string;
  speedA: number;
  throttleA: number;
  brakeA: number;
  steerA: number;
  gearA: number;
  accelA: number;
  speedB: number;
  throttleB: number;
  brakeB: number;
  steerB: number;
  gearB: number;
  accelB: number;
  gapMeters: number;
  closingSpeedMs: number;
  lateralDistMeters: number;
}
```

### Incident Detail Contract
```python
# backend/app/schemas/incident.py
from typing import List, Optional
from pydantic import BaseModel
from app.schemas.evidence import EvidenceItemSchema
from app.schemas.regulation import RelevantRegulationSchema, EvidenceRegulationConnectionSchema

class IncidentTimeWindow(BaseModel):
    start: str
    end: str

class IncidentDetailResponse(BaseModel):
    id: str
    session_id: str
    circuit: str
    lap: int
    turn: str
    timestamp: str
    time_window: IncidentTimeWindow
    driver_a: str
    driver_b: str
    incident_type: str
    confidence: int
    status: str
    severity: str
    summary: str
    detection_method: str
    video_available: bool
    video_path: Optional[str] = None
    telemetry_available: bool
    regulations_available: bool
    evidence_assessment: List[EvidenceItemSchema]
    relevant_regulations: List[RelevantRegulationSchema]
    evidence_connections: List[EvidenceRegulationConnectionSchema]
    uncertainties: List[str]
```

---

## 10. Frontend / Backend Integration Points

The integration point between frontend and backend is cleanly isolated in **`src/lib/api.ts`**:

1. **Feature Flag (`USE_LIVE_FASTAPI`)**:
   Currently set to `false`. When switched to `true`, all view components will automatically route through real HTTP `fetch()` requests against `API_BASE_URL`.
2. **Path Parameter Normalization**:
   Backend paths will adopt snake_case in Python and camelCase in TypeScript using standard Pydantic alias generators (`alias_generator=to_camel`, `populate_by_name=True`), preventing any frontend transformation friction.
3. **Global Search Integration (`GlobalSearchModal`)**:
   Replace the in-memory filtering in `src/components/GlobalSearchModal.tsx` with a consolidated backend query `GET /api/v1/search?q={query}` returning categorized matches across incidents, drivers, and rules.
4. **AI Assistant Integration (`AssistantView` & `IncidentDetailView`)**:
   Connect the simulated timeouts in `AssistantView.tsx` and `IncidentDetailView.tsx` directly to `askAssistant()` which posts to `POST /api/v1/assistant/query`.
5. **Chart Reference Points**:
   Pass incident-specific annotation timestamps (`referenceTimestamp`, `incidentWindow`) down to `TelemetryChart` dynamically rather than hardcoding `13:42:18.4` in the JSX.

---

## 11. Environment Variables Required

| Variable | Environment | Default Value | Description |
|---|---|---|---|
| `VITE_API_BASE_URL` | Frontend (`.env`) | `http://localhost:8000/api/v1` | Base URL for FastAPI REST service. Accessed via `import.meta.env.VITE_API_BASE_URL`. |
| `FASTAPI_HOST` | Backend (`.env`) | `0.0.0.0` | Host interface for Uvicorn server. |
| `FASTAPI_PORT` | Backend (`.env`) | `8000` | Port for FastAPI service. |
| `FASTF1_CACHE_DIR` | Backend (`.env`) | `data/cache/fastf1` | Local filesystem directory for FastF1 SQLite/Parquet session caches. |
| `CORS_ORIGINS` | Backend (`.env`) | `http://localhost:3000,http://127.0.0.1:3000` | Allowed origins for CORS middleware. |

---

## 12. CORS Requirements

In development and production, the frontend and backend run on distinct ports/domains:
- **Frontend Origin**: `http://localhost:3000` (Vite dev server) and `http://127.0.0.1:3000`.
- **Backend Origin**: `http://localhost:8000` (FastAPI / Uvicorn).
- **Backend Middleware Specification**:
  ```python
  from fastapi.middleware.cors import CORSMiddleware

  app.add_middleware(
      CORSMiddleware,
      allow_origins=[
          "http://localhost:3000",
          "http://127.0.0.1:3000",
      ],
      allow_credentials=True,
      allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
      allow_headers=["*"],
  )
  ```
- **Security Rule**: Do not use wildcard `allow_origins=["*"]` in production.

---

## 13. Current Problems Discovered

1. **`RacesView.tsx` Missing Field Crash Vulnerability**:
   - In `RacesView.tsx` (line 117), the code executed `race.sessions.map(...)`, while `Race` in `types.ts` did not define `sessions` and `MOCK_RACES` did not contain a `sessions` array. In an unshielded browser render, visiting the Races page would trigger a fatal unhandled `TypeError: Cannot read properties of undefined (reading 'map')`.
   - *Fix applied*: Added safe fallback `(race.sessions && race.sessions.length > 0) ? race.sessions.map(...) : fallback` and enriched `types.ts` with `RaceSession` interface and optional `sessions?: RaceSession[]`.
2. **Missing `@types/react` in DevDependencies**:
   - `package.json` contains `react: ^19.0.1` and `react-dom: ^19.0.1`, but `@types/react` and `@types/react-dom` were omitted. Running `tsc --noEmit --strict` flagged missing JSX intrinsic element definitions. The default build passes via Vite's bundler, but strict type resolution requires these type definitions for bulletproof typing.
3. **Direct Component Coupling to `mockData.ts`**:
   - `GlobalSearchModal.tsx` directly imports `MOCK_INCIDENTS`, `MOCK_DRIVERS`, `MOCK_RACES`, and `MOCK_REGULATION_LIBRARY`. It bypasses the `api.ts` layer entirely.
4. **Hardcoded Chart Annotations in `TelemetryChart.tsx`**:
   - Reference lines (`13:42:18.4`) and metric banners ("Impact Prob: 12%", "Relative Motion: CRITICAL") are hardcoded in the component template rather than driven by dynamic incident props.
5. **Redundant Duplicate Chat Handlers**:
   - Both `AssistantView.tsx` and `IncidentDetailView.tsx` maintain independent, duplicate hardcoded string-matching routines for AI inquiries rather than delegating to a unified API client function.

---

## 14. Files Changed in This Phase

1. **`src/lib/types.ts`**:
   - Added `RaceSession` interface (`name: string; laps?: number; status: string`).
   - Added optional `round?: number` and `sessions?: RaceSession[]` to `Race` interface.
   - Preserved all other existing types without aesthetic or structural changes.
2. **`src/views/RacesView.tsx`**:
   - Added null-safe checking for `race.sessions` with clean fallback rendering so the page renders reliably regardless of whether sessions are populated.
   - Added fallback for `race.round ?? 1`.
3. **`src/lib/api.ts`**:
   - Updated `API_BASE_URL` to prioritize `import.meta.env.VITE_API_BASE_URL` over `VITE_API_URL` before falling back to `http://localhost:8000/api/v1`.
4. **`.env.example`**:
   - Added documentation for `VITE_API_BASE_URL="http://localhost:8000/api/v1"`.
5. **`docs/progress/PROMPT_01_REPORT.md`**:
   - Created this comprehensive technical audit and integration contract document.

---

## 15. Files Deliberately NOT Changed

The following core frontend files were thoroughly audited and deliberately left untouched in accordance with the strict requirement to preserve existing UI layout, typography, colors, animations, and components:

- `src/App.tsx` (Routing structure preserved)
- `src/main.tsx` (DOM mount point preserved)
- `src/index.css` (Tailwind styles and theme tokens preserved)
- `src/views/LandingView.tsx` (Cinematic video hero, engine pipeline, and philosophy cards preserved)
- `src/views/DashboardView.tsx` (Session layout, Recharts bar distribution, and priority table preserved)
- `src/views/IncidentsView.tsx` (Search filters, confidence slider, and incident table preserved)
- `src/views/IncidentDetailView.tsx` (8-part linear evidentiary investigation workspace preserved)
- `src/views/RegulationsView.tsx` (Regulation cards, excerpts, and search preserved)
- `src/views/AssistantView.tsx` (Chat interface, evidence chips, and suggestions preserved)
- `src/components/HeroVideoBackground.tsx` (Dual-video 00:05 crossfade engine preserved)
- `src/components/VideoPlayer.tsx` (Video playback controls, frame stepping, and scrubber preserved)
- `src/components/TelemetryChart.tsx` (Multi-channel synchronized charts preserved)
- `src/components/EvidencePanel.tsx` (Categorized evidence accordion preserved)
- `src/components/RegulationPanel.tsx` (Regulatory articles accordion preserved)
- `src/components/EvidenceRegulationFlow.tsx` (3-step pipeline flow preserved)
- `src/components/UncertaintyCaveats.tsx` (Evidentiary uncertainty notice preserved)
- `src/components/IncidentTimeline.tsx` (Timeline cards preserved)
- `src/components/DriverModal.tsx` (Driver profile modal preserved)
- `src/components/RaceHeader.tsx` (Header bar and UTC clock preserved)
- `src/components/Sidebar.tsx` (Dark motorsport sidebar navigation preserved)
- `src/components/GlobalSearchModal.tsx` (Cmd+K search modal UI preserved)
- `src/components/SystemPipeline.tsx` (Pipeline card preserved)
- `src/lib/mockData.ts` (Mock datasets preserved intact for offline capability)

---

## 16. Risks or Uncertainties

1. **FastF1 Data Latency & Rate Limits**:
   - FastF1 downloads official timing and telemetry data directly from F1 live timing and Ergast/Jolpica endpoints. Initial download for a full race session (e.g. 53 laps at 25Hz across 20 drivers) can take 15–30 seconds and require 80–150 MB of memory.
   - *Mitigation*: The backend must implement aggressive disk caching via FastF1's built-in SQLite/filesystem cache (`fastf1.Cache.enable_cache('data/cache/fastf1')`) so sessions are only downloaded once.
2. **Telemetry Sampling Rate Synchronization**:
   - Car telemetry channels (speed, throttle, brake) have different CAN-bus sampling frequencies (often 10Hz–50Hz) than transponder GPS coordinates (~4Hz).
   - *Mitigation*: FastF1 provides synchronized interpolation across distance or session time. The backend Data Normalization service must resample car pairs to a clean, unified 25Hz timestamp grid before computing relative motion.
3. **Telemetry Intent Limitation**:
   - As emphasized in the project doctrine, mechanical telemetry (throttle lift, steering counter-lock, master cylinder pressure) confirms physical behavior, but cannot prove mental intent or awareness of an adjacent vehicle.
   - *Mitigation*: The UI and backend schemas must never output verdicts of guilt or fault; only empirical metrics with stated uncertainty bands.

---

## 17. Recommended Implementation Order for Prompt 2

To build a robust, modular backend without risking frontend breakage, implement in this strict sequence:

1. **FastAPI Foundation & Core Configuration**:
   - Initialize `backend/` package structure (`app/core`, `app/api`, `app/schemas`, `app/services`).
   - Configure Uvicorn server, Pydantic settings, and strict CORS middleware targeting `http://localhost:3000`.
2. **FastF1 Cache & Ingest Service**:
   - Create `FastF1Service` with persistent disk caching.
   - Implement schedule, race, session, and driver metadata extraction.
   - Expose `GET /api/v1/races`, `GET /api/v1/sessions/{session_id}`, and `GET /api/v1/sessions/{session_id}/drivers`.
3. **Session Overview & Incident Activity Endpoints**:
   - Implement `GET /api/v1/sessions/{session_id}/summary` and `GET /api/v1/sessions/{session_id}/activity`.
   - Connect `DashboardView` to verify live race activity bar chart rendering.
4. **Telemetry Processing & Pair Association Service**:
   - Implement telemetry slice extraction for interacting driver pairs with distance, gap, closing speed, and acceleration derivation.
   - Expose `GET /api/v1/incidents/{incident_id}/telemetry`.
5. **Incident Reconstruction & Evidence Engine**:
   - Implement structured incident candidate model with evidence items, uncertainty caveats, and regulation linkages.
   - Expose `GET /api/v1/sessions/{session_id}/incidents` and `GET /api/v1/incidents/{incident_id}`.
6. **Regulation Retrieval Engine**:
   - Implement indexed regulation retrieval service exposing `GET /api/v1/regulations`.
7. **Frontend Toggle Validation**:
   - Flip `USE_LIVE_FASTAPI = true` in `src/lib/api.ts` and verify end-to-end telemetry and incident visualization with zero UI degradation.
