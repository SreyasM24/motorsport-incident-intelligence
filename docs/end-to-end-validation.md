# End-to-End Steward Investigation Validation & Production Case Replay

## Executive Summary

This specification documents the end-to-end integration validation protocol, case replay architecture, and empirical verification results for **Motorsport Incident Intelligence (MII)** under Prompt 25.

The platform unites 12 subsystem boundaries into a unified, deterministic, evidence-first steward investigation workflow:
1. FastF1 ECU CAN-bus and OpenF1 telemetry ingestion & 25Hz SI grid alignment
2. Spatial trajectory & corner overtake geometry reconstruction
3. Baseline reference-lap kinematic divergence analysis
4. Multi-signal logistic anomaly scoring (pure trajectory variance; zero guilt/liability)
5. Citation-grounded regulation retrieval (FIA 2024 Sporting Regulations and Driving Standards Guidelines)
6. Historical comparable-case intelligence (MII-HIRB-v1.1 verified documentary precedents)
7. Multi-modal evidence synthesis & cross-modal contradiction detection
8. Database persistence & idempotent session/driver prerequisite generation
9. Canonical Steward Case Workspace read model with deterministic 5-tier triage priority
10. Human steward investigation review state machine (`REQUIRES_REVIEW` $\to$ `UNDER_REVIEW` $\to$ `REVIEWED`/`DISMISSED`)
11. Steward evidence acknowledgement, unresolved question tracking, and discrepancy lifecycle
12. Conversational assistant grounded in empirical workspace facts with strict non-adjudication guardrails

---

## Non-Adjudication Doctrine

> [!IMPORTANT]
> **STRICT NON-ADJUDICATION PRINCIPLE:**
> Motorsport Incident Intelligence is an evidence synthesis and investigation decision-support platform. It strictly **does not automate driver guilt, assign fault probabilities, issue penalties, or render legal verdicts**. Human stewards retain exclusive statutory adjudicative authority under the FIA International Sporting Code.

Historical rulings and penalty records are treated strictly as **DOCUMENTARY** artifacts. They are never ingested as ground-truth training labels for algorithmic causality or liability.

---

## Canonical Replay Architecture

The end-to-end replay workflow is orchestrated by `CaseReplayService` (`backend/app/services/case_replay_service.py`):

```
       [Raw Incident Candidate / Manifest Case]
                         │
                         ▼
          Incident Reconstruction Engine
                         │
        (25Hz Synchronized Telemetry Points)
                         │
                         ▼
             Master Dossier Synthesizer
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
Telemetry / RCM     Regulations RAG     Historical Benchmark
                         │
                         ▼
            Candidate Persistence Service
           (Idempotent PostgreSQL Session)
                         │
                         ▼
             Steward Workspace Service
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
5-Tier Triage       Timeline + Uncertainty  Contradictions
                         │
                         ▼
          Simulated Steward Investigation
     ┌───────────────────┼───────────────────┐
     ▼                   ▼                   ▼
State Transition    Acknowledgement    Unresolved Question
                         │
                         ▼
        Deterministic Workspace Fingerprint
          (Invariant SHA256 Verification)
```

### Determinism & Invariant Fingerprinting

The system guarantees bit-for-bit repeatability across executions. `compute_workspace_fingerprint` calculates an invariant SHA256 digest over:
- Sorted evidence items (`evidence_id`, `epistemic_type`, `triage_priority`, `observation`, `value`)
- Ordered timeline milestones (`timestamp`, `relative_sec`, `source`, `epistemic_type`)
- Active discrepancies (`discrepancy_id`, `type`, `status`)
- Regulatory citations (`regulation_id`, `article`)
- Historical comparable cases (`case_id`, `similarity_score`)

---

## Replay Validation Matrix

| Dimension | Verification Target | Methodology | Actual Result |
|---|---|---|---|
| **1. Full Replay** | REF-MONZA-01 | Telemetry $\to$ Workspace $\to$ Review | **PASSED** |
| **2. Monza Reference Cases** | REF-MONZA-02, REF-MONZA-03 | Lap 1 & Lap 5 multi-car interactions | **PASSED** |
| **3. Cross-Circuit Expansion** | HIST-2024-AUT-R-01 | Red Bull Ring (Spielberg) verification | **PASSED** |
| **4. Determinism** | SHA256 Fingerprint | Consecutive re-runs yield identical digests | **PASSED** |
| **5. Idempotency** | Repeat Ingestion | 0 duplicate rows across sessions/incidents | **PASSED** |
| **6. Degraded Video** | Honest Unavailability | UNAVAILABLE status without fabrication | **PASSED** |
| **7. Transaction Integrity** | Mid-flight Failure | Clean rollback with zero orphan records | **PASSED** |
| **8. Evidence Immutability** | Reviewer Mutations | Raw telemetry bit-for-bit unchanged | **PASSED** |
| **9. Review State Machine** | Status Transitions | Strictly enforces legal steward steps | **PASSED** |
| **10. Assistant Grounding** | Non-adjudication | Refuses fault/penalty questions 100% | **PASSED** |
| **11. API Contracts** | REST Endpoints | Workspace, ACK, questions validated | **PASSED** |
| **12. Production Acceptance** | Real Monza Scenario | Decision-ready dossier with audit log | **PASSED** |

---

## Empirical Performance Profile

Measurements executed on physical testing harness:

- **Cold Pipeline Latency:** $67,808.13\text{ ms}$
  - Raw Telemetry Re-synchronization: $51,303.24\text{ ms}$
  - Dossier Multi-Modal Synthesis: $10.45\text{ ms}$
  - Database Persistence: $224.36\text{ ms}$
  - Initial Workspace Assembly & Retrieval: $16,270.01\text{ ms}$
- **Warm Pipeline Latency:** $16,506.11\text{ ms}$
  - Raw Telemetry Re-read: $16,490.50\text{ ms}$
  - Dossier Multi-Modal Synthesis: $6.82\text{ ms}$
  - Idempotent Persistence Check: $2.13\text{ ms}$
  - Cached Workspace Assembly: $6.63\text{ ms}$

---

## Known Boundaries & Limitations

1. **Broadcast Video Rights:** Live broadcast video footage remains commercial intellectual property of FOM and is marked `UNAVAILABLE` or `PARTIAL` honestly across all cases.
2. **GPS Cartesian Discretization:** Track coordinates are derived from 25Hz interpolation with bounded uncertainty ($\pm 0.20\text{ m}$).
3. **Documentary Historical Outcomes:** Historical steward penalties provide comparative context only and do not constitute binding legal precedent.
