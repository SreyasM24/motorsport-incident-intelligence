"""Cornering Overtake Geometry & Apex Overlap Analysis domain models.

Re-exports schemas from app.schemas.overtake_geometry.
"""

from app.schemas.overtake_geometry import (
    ApexOverlapSnapshot,
    CornerPhases,
    CornerPhaseSnapshot,
    ExitClearanceClassification,
    ExitClearanceMetrics,
    FIAGuidelineReference,
    MeasurementConfidence,
    OverlapClassification,
    OvertakeGeometryDataQuality,
    OvertakeGeometryEvidence,
    RelativeLongitudinalPosition,
)

__all__ = [
    "ApexOverlapSnapshot",
    "CornerPhases",
    "CornerPhaseSnapshot",
    "ExitClearanceClassification",
    "ExitClearanceMetrics",
    "FIAGuidelineReference",
    "MeasurementConfidence",
    "OverlapClassification",
    "OvertakeGeometryDataQuality",
    "OvertakeGeometryEvidence",
    "RelativeLongitudinalPosition",
]
