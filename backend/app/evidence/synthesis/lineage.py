"""Evidence Lineage Tracker & Double-Counting Prevention Engine.

Models explicit parent-child lineage across evidence items to guarantee that
correlated, derived, or downstream model features are not mistakenly counted
as independent empirical observations.
"""

from typing import Dict, List, Optional, Set
from app.evidence.synthesis.contracts import EvidenceItem, EvidenceStatus


class LineageTracker:
    """Tracks evidence lineage graph and calculates true independent observation count."""

    @staticmethod
    def identify_lineage_roots(items: List[EvidenceItem]) -> List[str]:
        """Identify the root parent evidence IDs across all evidence items.

        A root evidence item is one that has no parent_evidence_ids (or has status OBSERVED/DOCUMENTARY).
        """
        item_map: Dict[str, EvidenceItem] = {item.evidence_id: item for item in items}
        roots: Set[str] = set()

        for item in items:
            if not item.parent_evidence_ids:
                roots.add(item.evidence_id)
            else:
                # Walk up to find ancestral roots
                ancestors = LineageTracker._find_ancestral_roots(item.evidence_id, item_map)
                roots.update(ancestors)

        return sorted(list(roots))

    @staticmethod
    def _find_ancestral_roots(item_id: str, item_map: Dict[str, EvidenceItem], visited: Optional[Set[str]] = None) -> Set[str]:
        """Recursively walk up parent references to find root origins."""
        if visited is None:
            visited = set()
        if item_id in visited:
            return set()
        visited.add(item_id)

        item = item_map.get(item_id)
        if not item or not item.parent_evidence_ids:
            return {item_id}

        roots = set()
        for p_id in item.parent_evidence_ids:
            if p_id in item_map:
                roots.update(LineageTracker._find_ancestral_roots(p_id, item_map, visited))
            else:
                # Parent is external or top-level origin
                roots.add(p_id)
        return roots

    @staticmethod
    def compute_independent_observation_count(items: List[EvidenceItem]) -> int:
        """Compute the count of genuinely independent empirical observations.

        Prevents double-counting: Multiple derived metrics (e.g. closing speed, minimum gap,
        deceleration delta) that share the same underlying telemetry stream count as 1 independent
        observation source, not 3.
        """
        if not items:
            return 0

        item_map: Dict[str, EvidenceItem] = {item.evidence_id: item for item in items}
        origin_roots: Set[str] = set()

        for item in items:
            if item.status == EvidenceStatus.UNAVAILABLE:
                continue

            # Trace back to true ancestral root origins
            roots = LineageTracker._find_ancestral_roots(item.evidence_id, item_map)
            origin_roots.update(roots)

        return len(origin_roots)
