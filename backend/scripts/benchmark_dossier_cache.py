"""Empirical Benchmark for Dossier Synthesis & Caching.

Measures:
1. BEFORE caching (Cold Cache / Fresh Synthesis)
2. AFTER caching (Warm Cache Hit)
3. Correctness across review state mutation
4. Invalidation behavior
"""

import sys
import os
import time
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.services.dossier_cache_service import get_dossier_cache

client = TestClient(app)
cache = get_dossier_cache()


def benchmark_dossier():
    print("=== COMMENCING DOSSIER PERFORMANCE BENCHMARK ===")
    cache.clear()

    incident_id = "INC-2024-MONZA-R-02"

    # 1. Cold Cache: Full On-Demand Synthesis
    t0 = time.perf_counter()
    r1 = client.get(f"/api/v1/incidents/{incident_id}/dossier")
    cold_ms = (time.perf_counter() - t0) * 1000.0
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    print(f"Cold Cache (Full Synthesis) Latency: {cold_ms:10.2f} ms")

    # 2. Warm Cache Hit: Instant Retrieval
    warm_samples = []
    for _ in range(5):
        t0 = time.perf_counter()
        r2 = client.get(f"/api/v1/incidents/{incident_id}/dossier")
        warm_samples.append((time.perf_counter() - t0) * 1000.0)
        assert r2.status_code == 200

    median_warm = sorted(warm_samples)[len(warm_samples) // 2]
    print(f"Warm Cache Hit Median Latency      : {median_warm:10.2f} ms")
    speedup = cold_ms / median_warm if median_warm > 0 else 0
    print(f"Empirical Speedup Factor           : {speedup:10.1f}x")

    # 3. Correctness check: Mutate review status
    client.patch(
        f"/api/v1/incidents/{incident_id}/status",
        json={"status": "UNDER_REVIEW", "reviewer_id": "STEWARD-TEST"},
    )
    r3 = client.get(f"/api/v1/incidents/{incident_id}/dossier")
    assert r3.status_code == 200
    data = r3.json()
    review_val = data.get("reviewStatus") or data.get("review_status")
    reviewer_val = data.get("reviewerId") or data.get("reviewer_id")
    assert review_val == "UNDER_REVIEW", f"Expected UNDER_REVIEW, got {review_val}"
    assert reviewer_val == "STEWARD-TEST", f"Expected STEWARD-TEST, got {reviewer_val}"
    print("Review State Separation Validated : YES (Live review state reflected on warm cache)")


    # 4. Invalidation check
    cand_id = "REF-MONZA-02"
    evicted = cache.invalidate_candidate(cand_id)
    print(f"Invalidated candidate entries     : {evicted}")
    stats = cache.get_stats()
    print("Cache Telemetry Stats              :", stats)


if __name__ == "__main__":
    benchmark_dossier()
