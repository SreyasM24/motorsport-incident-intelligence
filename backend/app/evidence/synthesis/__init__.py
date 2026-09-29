"""Multi-Modal Evidence Synthesis, Discrepancy Analysis & Steward Dossier Module."""

from app.evidence.synthesis.contracts import (
    ConsistencyStatus,
    CrossModalDiscrepancy,
    DescriptiveRegulationLink,
    DiscrepancySeverity,
    DossierExportPayload,
    EvidenceConsensus,
    EvidenceItem,
    EvidenceQualityRecord,
    EvidenceStatus,
    EvidenceType,
    NormalizedTimelineEvent,
    StewardEvidenceDossier,
)
from app.evidence.synthesis.lineage import LineageTracker
from app.evidence.synthesis.consistency import ConsistencyEngine
from app.evidence.synthesis.synthesizer import (
    StewardDossierSynthesizer,
    get_steward_dossier_synthesizer,
)

__all__ = [
    "ConsistencyEngine",
    "ConsistencyStatus",
    "CrossModalDiscrepancy",
    "DescriptiveRegulationLink",
    "DiscrepancySeverity",
    "DossierExportPayload",
    "EvidenceConsensus",
    "EvidenceItem",
    "EvidenceQualityRecord",
    "EvidenceStatus",
    "EvidenceType",
    "LineageTracker",
    "NormalizedTimelineEvent",
    "StewardDossierSynthesizer",
    "StewardEvidenceDossier",
    "get_steward_dossier_synthesizer",
]
