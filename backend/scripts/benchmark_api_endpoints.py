"""API Endpoints Latency Benchmark.

Measures median, p95, and p99 latency across representative endpoints.
"""

import sys
import os
import time
import numpy as np
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

client = TestClient(app)

ENDPOINTS = [
    ("Health (Diagnostic)", "GET", "/api/v1/health", None),
    ("Health (Liveness)", "GET", "/api/v1/health/live", None),
    ("Health (Readiness)", "GET", "/api/v1/health/ready", None),
    ("Races List", "GET", "/api/v1/races", None),
    ("Incidents List", "GET", "/api/v1/incidents", None),
    ("Incident Detail", "GET", "/api/v1/incidents/INC-2024-MONZA-R-02", None),
    ("Telemetry Slice", "GET", "/api/v1/incidents/INC-2024-MONZA-R-02/telemetry", None),
    ("Steward Dossier (Warm)", "GET", "/api/v1/incidents/INC-2024-MONZA-R-02/dossier", None),
    ("Regulations Library", "GET", "/api/v1/regulations", None),
    ("CV Evaluation Suite", "GET", "/api/v1/analysis/cv/evaluation", None),
    ("Assistant Query", "POST", "/api/v1/assistant/query", {"query": "What are the rules regarding crowding at track edge?"}),
]


def run_benchmark(n_runs: int = 25):
    print("=== MEASURING REPRESENTATIVE ENDPOINT LATENCIES ===")
    print(f"{'Endpoint':25s} | {'Median (ms)':12s} | {'p95 (ms)':10s} | {'p99 (ms)':10s} | {'Status':6s}")
    print("-" * 75)

    # Prime warm cache for dossier
    client.get("/api/v1/incidents/INC-2024-MONZA-R-02/dossier")

    results = []

    for name, method, path, payload in ENDPOINTS:
        latencies = []
        status_codes = []

        runs = 3 if "Telemetry" in name else n_runs
        for _ in range(runs):
            t0 = time.perf_counter()
            if method == "GET":
                resp = client.get(path)
            else:
                resp = client.post(path, json=payload)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            latencies.append(elapsed_ms)
            status_codes.append(resp.status_code)


        median = float(np.median(latencies))
        p95 = float(np.percentile(latencies, 95))
        p99 = float(np.percentile(latencies, 99))
        status = status_codes[0]

        print(f"{name:25s} | {median:12.2f} | {p95:10.2f} | {p99:10.2f} | {status:<6d}")
        results.append({
            "name": name,
            "path": path,
            "method": method,
            "median_ms": median,
            "p95_ms": p95,
            "p99_ms": p99,
            "status_code": status,
        })

    return results


if __name__ == "__main__":
    run_benchmark()
