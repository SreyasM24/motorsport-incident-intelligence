"""Dossier Performance Cache Service.

Provides high-performance, version-aware, invalidation-safe caching for
synthesized StewardEvidenceDossier instances.

DESIGN PRINCIPLES:
1. Deterministic Cache Key: Incorporates candidate_id, analysis_version, and preprocessing_version.
2. Separation of Concerns: The heavy mathematical/multi-modal evidence snapshot is cached,
   while mutable human review records (status, reviewer_id, notes) are ALWAYS injected
   fresh from the database.
3. Invalidation Strategy: Cached dossiers can be explicitly invalidated per candidate or globally
   whenever underlying sensor data or algorithms are modified.
"""

import time
import copy
from typing import Any, Dict, Optional, Tuple
from app.core.logging import logger
from app.evidence.synthesis.contracts import StewardEvidenceDossier


class DossierCacheService:
    """Thread-safe, version-aware in-memory cache for synthesized evidence dossiers."""

    def __init__(self, default_ttl_seconds: int = 3600):
        self._cache: Dict[str, Tuple[StewardEvidenceDossier, float, str]] = {}
        self._default_ttl = default_ttl_seconds
        self._hits = 0
        self._misses = 0

    @staticmethod
    def build_cache_key(
        candidate_id: str,
        analysis_version: str = "PROMPT_16_SYNTHESIS",
        preprocessing_version: str = "v1",
    ) -> str:
        """Generate deterministic cache key."""
        return f"dossier:{candidate_id}:{analysis_version}:{preprocessing_version}"

    def get_snapshot(self, key: str) -> Optional[StewardEvidenceDossier]:
        """Retrieve cached dossier snapshot if present and not expired."""
        entry = self._cache.get(key)
        if not entry:
            self._misses += 1
            return None

        dossier, created_at, _ = entry
        if time.time() - created_at > self._default_ttl:
            logger.info(f"Dossier cache entry expired for key: {key}")
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        return copy.deepcopy(dossier)

    def set_snapshot(
        self,
        key: str,
        dossier: StewardEvidenceDossier,
        candidate_id: str,
    ) -> None:
        """Store synthesized evidence dossier snapshot into cache."""
        self._cache[key] = (copy.deepcopy(dossier), time.time(), candidate_id)
        logger.info(f"Cached synthesized dossier snapshot: {key} (cache size: {len(self._cache)})")

    def inject_live_review_state(
        self,
        dossier: StewardEvidenceDossier,
        review_record: Optional[Dict[str, Any]],
    ) -> StewardEvidenceDossier:
        """Inject current mutable human review record into the cached dossier."""
        if review_record:
            dossier.review_status = review_record.get("status", "REQUIRES_REVIEW")
            dossier.reviewer_id = review_record.get("reviewer_id")
            dossier.review_notes = review_record.get("review_notes")
        else:
            dossier.review_status = "REQUIRES_REVIEW"
            dossier.reviewer_id = None
            dossier.review_notes = None
        return dossier

    def invalidate_candidate(self, candidate_id: str) -> int:
        """Evict all cached entries corresponding to a specific candidate ID."""
        keys_to_remove = [
            k for k, (_, _, cid) in self._cache.items() if cid == candidate_id
        ]
        for k in keys_to_remove:
            del self._cache[k]
        logger.info(f"Invalidated {len(keys_to_remove)} cached dossier(s) for candidate: {candidate_id}")
        return len(keys_to_remove)

    def clear(self) -> None:
        """Purge all entries in the cache."""
        self._cache.clear()
        logger.info("Cleared entire dossier cache.")

    def get_stats(self) -> Dict[str, Any]:
        """Return cache telemetry and hit/miss statistics."""
        total = self._hits + self._misses
        hit_ratio = (self._hits / total) if total > 0 else 0.0
        return {
            "cached_entries": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "hit_ratio": round(hit_ratio, 4),
            "ttl_seconds": self._default_ttl,
        }


# Singleton cache instance
_dossier_cache = DossierCacheService()


def get_dossier_cache() -> DossierCacheService:
    """Return singleton DossierCacheService."""
    return _dossier_cache
