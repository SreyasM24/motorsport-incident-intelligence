"""Dossier Synthesis Performance Profiler.

Empirically measures the latency breakdown of every stage in dossier generation:
1. Database access
2. Candidate dossier retrieval / telemetry reconstruction
3. CV analysis
4. Synthesis (lineage tracking, consistency checks)
5. JSON serialization
"""

import sys
import os
import time
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database.connection import SessionLocal
from app.models import Incident
from app.evidence.reconstruction_service import get_reconstruction_engine
from app.evidence.cv.service import get_cv_service
from app.evidence.synthesis.synthesizer import get_steward_dossier_synthesizer
from app.services.candidate_persistence_service import CandidatePersistenceService


def profile_candidate(cand_id: str = "REF-MONZA-02") -> dict:
    results = {}
    total_start = time.perf_counter()

    # 1. Database access
    t0 = time.perf_counter()
    with SessionLocal() as db:
        inc = db.query(Incident).filter(Incident.candidate_id == cand_id).first()
        reviews = CandidatePersistenceService.get_incident_reviews(db, inc.id) if inc else []
        review_record = reviews[0].__dict__ if reviews else None
    results["db_access_ms"] = (time.perf_counter() - t0) * 1000.0

    # 2. Candidate Dossier Reconstruction (telemetry, geometry, ML, baseline, regs)
    engine = get_reconstruction_engine()
    t0 = time.perf_counter()
    dossier = engine.get_candidate_dossier(cand_id)
    results["reconstruction_ms"] = (time.perf_counter() - t0) * 1000.0

    if not dossier:
        print(f"Error: Candidate {cand_id} not found!")
        return results

    # 3. CV analysis
    cv_service = get_cv_service()
    t0 = time.perf_counter()
    cv_analysis = cv_service.process_candidate_incident(candidate=dossier.candidate)
    results["cv_analysis_ms"] = (time.perf_counter() - t0) * 1000.0

    # 4. Multi-modal synthesis (consistency engine, lineage tracker)
    synthesizer = get_steward_dossier_synthesizer()
    t0 = time.perf_counter()
    steward_dossier = synthesizer.synthesize_steward_dossier(
        dossier=dossier,
        cv_analysis=cv_analysis,
        review_record=review_record,
    )
    results["synthesis_ms"] = (time.perf_counter() - t0) * 1000.0

    # 5. Serialization
    t0 = time.perf_counter()
    dossier_dict = steward_dossier.model_dump(mode="json")
    json_bytes = json.dumps(dossier_dict).encode("utf-8")
    results["serialization_ms"] = (time.perf_counter() - t0) * 1000.0
    results["payload_bytes"] = len(json_bytes)

    results["total_pipeline_ms"] = (time.perf_counter() - total_start) * 1000.0

    print("=== PROFILING BREAKDOWN FOR", cand_id, "===")
    for k, v in results.items():
        if k.endswith("_ms"):
            print(f"  {k:22s}: {v:10.2f} ms")
        else:
            print(f"  {k:22s}: {v}")
    return results


if __name__ == "__main__":
    profile_candidate("REF-MONZA-02")
