"""Evidence provenance tracking and audit trail representation.

Provides verifiable source metadata for every empirical evidence dimension in a dossier.
"""

from datetime import datetime, timezone
from typing import Dict, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class EvidenceProvenanceRecord(BaseModel):
    """Traceable audit record for an empirical data stream or synthesized evidence item."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    channel: str = Field(..., description="Telemetry, RaceControl, Video, Regulations, Analysis")
    source: str = Field(..., description="FastF1, OpenF1, FIA Documents, Local Cache")
    source_id: str = Field(..., description="Specific session key, document id, or file hash")
    processing_version: str = Field(default="telemetry_preprocessing_v1")
    retrieval_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    methodology: str = Field(..., description="Processing algorithm, filter, or standard applied")


def build_default_provenance(
    session_id: str,
    detection_method: str = "MULTI_SIGNAL_RECONSTRUCTION_V1",
) -> Dict[str, EvidenceProvenanceRecord]:
    """Construct full provenance audit map for an incident dossier."""
    now_iso = datetime.now(timezone.utc).isoformat()

    return {
        "telemetry": EvidenceProvenanceRecord(
            channel="Telemetry",
            source="FastF1 CAN-Bus + GPS Feed",
            source_id=session_id,
            processing_version="telemetry_preprocessing_v1",
            retrieval_timestamp=now_iso,
            methodology="25 Hz uniform grid resampling with monotonic deduplication and SI coordinate scaling.",
        ),
        "race_control": EvidenceProvenanceRecord(
            channel="RaceControl",
            source="FIA Stewards Electronic Timing App Stream (OpenF1 / FastF1)",
            source_id=f"{session_id}_rcm",
            processing_version="rcm_parser_v1",
            retrieval_timestamp=now_iso,
            methodology="Temporal correlation of flagged incidents and track status bulletins.",
        ),
        "video": EvidenceProvenanceRecord(
            channel="Video",
            source="FIA / FOM Broadcast Metadata Registry",
            source_id="unlinked",
            processing_version="video_sync_v1",
            retrieval_timestamp=now_iso,
            methodology="Session UTC to video playback timestamp offset mapping without broadcast ingestion.",
        ),
        "regulations": EvidenceProvenanceRecord(
            channel="Regulations",
            source="FIA World Motor Sport Council Official Statutes",
            source_id="fia_2024_sporting_statutes",
            processing_version="statute_linkage_v1",
            retrieval_timestamp=now_iso,
            methodology="Deterministic rule association based on empirical kinematics and contact indicators.",
        ),
    }
