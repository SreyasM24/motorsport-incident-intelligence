# Steward Case Workspace: Evidence Triage & Decision-Ready Review

## 1. Overview & Core Philosophy

The **Steward Case Workspace** is an evidence-first investigation environment designed specifically for Formula 1 and motorsport race stewards. It transforms raw multi-modal streams (25Hz CAN-bus telemetry, reference baselines, corner geometry, computer vision detections, and historical records) into an inspectable, discrepancy-aware dossier.

### Fundamental Jurisprudential Guardrails
1. **Human Decision Authority:** The system strictly does **NOT** automate guilt, apportion driver fault, or recommend sporting penalties. Adjudication remains the exclusive statutory responsibility of human race stewards.
2. **Epistemic Integrity:** All evidence items are classified into explicit epistemic categories:
   - `OBSERVED`: Direct physical sensor data (raw ECU CAN-bus, timing transponder).
   - `DERIVED`: Deterministic mathematical derivations (closing speed, lateral clearance, apex overlap).
   - `MODEL_DERIVED`: Statistical or neural hypotheses (bounding box tracks, kinematic anomaly confidence).
   - `DOCUMENTARY`: Official regulatory or race control documentary reference.
   - `UNAVAILABLE`: Unobserved, unlinked, or commercially restricted data.
3. **Investigation UX Prioritization:** Evidence items are ordered deterministically for human review:
   $$\text{OBSERVED (1)} \longrightarrow \text{DERIVED (2)} \longrightarrow \text{MODEL\_DERIVED (3)} \longrightarrow \text{DOCUMENTARY (4)} \longrightarrow \text{UNAVAILABLE (5)}$$
   *This hierarchy is strictly an investigation UX ordering, never an assertion of proof or fault probability.*
4. **Non-Mutating Reviewer Metadata:** Human steward acknowledgements, investigation notes, and open questions are stored in isolated audit tables. Source telemetry and sensor data remain permanently immutable.

---

## 2. Workspace Canonical Architecture

```
                                      +---------------------------------------------+
                                      |            Human Steward Panel              |
                                      +---------------------------------------------+
                                                            |
                                               Interactive Investigation
                                                            v
+-------------------------------------------------------------------------------------------------------------------+
|                                            STEWARD CASE WORKSPACE                                                 |
|                                                                                                                   |
|  +--------------------+   +-----------------------+   +-----------------------+   +----------------------------+  |
|  |    Case Header     |   |   Incident Timeline   |   |    Evidence Triage    |   | Cross-Modal Discrepancies  |  |
|  | - Status Badge     |   | - Chronological T-2s  |   | - OBSERVED            |   | - Telemetry vs Video       |  |
|  | - Session / Drivers|   | - Uncertainty Bounds  |   | - DERIVED             |   | - RC vs Telemetry          |  |
|  | - Lap / Corner     |   | - Provenance Anchors  |   | - MODEL_DERIVED       |   | - Status: OPEN/ACK/RES     |  |
|  +--------------------+   +-----------------------+   | - DOCUMENTARY         |   +----------------------------+  |
|                                                       | - UNAVAILABLE         |                                   |
|  +--------------------+   +-----------------------+   +-----------------------+   +----------------------------+  |
|  | Hist. Comparables  |   |  Ground Regulations   |                               |   Unresolved Questions     |  |
|  | (Prompt 23 Engine) |   |  (Prompt 21 RAG)      |   +-----------------------+   | - Open / Deferred / Res    |  |
|  | - Side-by-Side     |   | - Citation Grounded   |   | Reviewer Evidence Ack |   | - Linked Evidence IDs      |  |
|  | - Zero Precedent   |   | - Source Conflicts    |   | - CONSIDERED/INSUFF   |   +----------------------------+  |
|  +--------------------+   +-----------------------+   | - Non-Mutating Audit  |                                   |
|                                                       +-----------------------+   +----------------------------+  |
|  +------------------------------------------------+                               |    Immutable Audit Trail   |  |
|  |             AI Steward Assistant               |                               | - Who, When, What, Why     |  |
|  | Grounded in Workspace • Refuses Guilt / Verdict|                               +----------------------------+  |
|  +------------------------------------------------+                                                               |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 3. Evidence Triage & Epistemic Taxonomy

Every piece of evidence in the workspace exposes deterministic triage metadata:

| Attribute | Description | Example |
|---|---|---|
| `evidence_id` | Unique deterministic identifier | `EV-REF-MONZA-01-TEL-MIN-GAP` |
| `evidence_type` | Subsystem stream classification | `TELEMETRY`, `OVERTAKE_GEOMETRY`, `VISUAL` |
| `epistemic_type` | Observational certainty level | `OBSERVED`, `DERIVED`, `MODEL_DERIVED`, `DOCUMENTARY`, `UNAVAILABLE` |
| `availability` | Rigorous availability rating | `FULL`, `PARTIAL`, `LIMITED`, `UNAVAILABLE` |
| `triage_priority` | UX investigation hierarchy (1–5) | `1` (Observed) through `5` (Unavailable) |
| `provenance` | Upstream sensor or calculation origin | Central Euclidean Difference on 25Hz Cartesian Coordinates |
| `limitations` | Explicit physical or sensor caveats | Center-of-mass vector without continuous yaw angle |
| `parent_evidence_ids` | Direct lineage tracking | `["EV-REF-MONZA-01-TEL-RAW"]` |

### Missing Data Handling
Missing data is never converted into a numerical zero. Unlinked broadcast video (protected under FOM commercial copyright) is explicitly labeled `UNAVAILABLE` with clear provenance reasons and zero negative inferences against any competitor.

---

## 4. Chronological Incident Timeline & Uncertainty Bounds

The workspace reconstructs a unified timeline around the candidate incident window ($T - 2.0\text{ s}$ to $T + 1.5\text{ s}$):
- $T - 2.0\text{ s}$: Initial approach established on telemetry.
- $T - 1.2\text{ s}$: Braking initiated deeper than reference baseline ($\pm 1.0\text{ m}$ uncertainty).
- $T - 0.7\text{ s}$: Relative lateral spacing decreases below threshold ($\pm 0.20\text{ m}$ uncertainty).
- $T + 0.0\text{ s}$: Candidate peak interaction milestone ($\pm 2.0\text{ km/h}$ CAN-bus accuracy).
- $T + 0.4\text{ s}$: Trajectory divergence / counter-steering compensation.
- $T + 1.0\text{ s}$: Corner exit state and track limits recovery.

---

## 5. Cross-Modal Discrepancy Investigation

When two or more evidence channels exhibit tension, the system flags a `CrossModalDiscrepancy`:
- **Evidence Streams:** e.g., FastF1 Telemetry vs. Video Broadcast Timecode.
- **Metric:** Timestamp offset, spatial clearance delta, or track position disagreement.
- **Magnitude & Uncertainty:** e.g., $0.28\text{ s}$ divergence ($\pm 0.04\text{ s}$ uncertainty).
- **Human Steward Status:** `OPEN`, `ACKNOWLEDGED`, `RESOLVED`, `UNRESOLVED`.

> [!IMPORTANT]
> The platform surfaces contradictions to the human stewards and strictly prohibits automated resolution or algorithmic papering-over of discrepancies.

---

## 6. Reviewer Actions & Immutable Audit Trail

### Granular Evidence Acknowledgements
Stewards can acknowledge individual evidence items:
- `CONSIDERED`: Evidence examined and weighed in deliberations.
- `NOT_RELEVANT`: Not germane to the specific overtaking phase.
- `INSUFFICIENT`: Sensor resolution or camera coverage inconclusive.
- `CONTRADICTORY`: Conficts with another stream; marked for cross-examination.
- `REQUIRES_FOLLOW_UP`: Requires inquiry with driver, team delegate, or telemetry engineer.

### Unresolved Investigation Questions
Stewards can open structured technical questions to track factual gaps:
- Question: *"Camera coverage does not establish rear-wheel overlap at apex."*
- Affected Evidence IDs: `["EV-TEL-RAW", "EV-CV-TRACK-01"]`
- Status: `OPEN` $\longrightarrow$ `RESOLVED` (with steward findings) or `DEFERRED`.

### Immutable Audit Trail
Every status transition records:
- `previous_state` $\longrightarrow$ `new_state`
- `reviewer_id`
- `timestamp` (UTC)
- `review_notes` and `review_rationale`
- Reopening rationale (mandatory when reopening `REVIEWED` or `DISMISSED` cases)

---

## 7. Performance & Latency

- **Cold Workspace Latency:** $\sim 5\text{–}30\text{ s}$ (includes full FastF1 CAN-bus session loading, resampled Cartesian projection, and baseline variance derivation).
- **Warm Workspace Latency:** **$< 1\text{ ms}$** (in-memory cached master dossier serving canonical read model).
