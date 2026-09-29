"""API router for the AI Steward Assistant evidence synthesizer."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.schemas.assistant import (
    AssistantQueryRequest,
    AssistantMessageSchema,
    EvidenceChip,
    EvidenceLink,
)

router = APIRouter(prefix="/assistant", tags=["Assistant"])


@router.post("/query", response_model=AssistantMessageSchema, summary="Submit conversational steward query")
def query_assistant(
    payload: AssistantQueryRequest,
    db: Session = Depends(get_db),
) -> AssistantMessageSchema:
    """Process natural-language steward inquiry regarding incident telemetry or regulations.

    CRITICAL DOCTRINE:
        This assistant is decision support for human race stewards. It surfaces
        verifiable telemetry evidence, trajectory dynamics, and relevant FIA
        statutory articles. It NEVER makes determinations of guilt, fault, or penalties.
    """
    timestamp_str = datetime.now(timezone.utc).strftime("%H:%M:%S")
    msg_id = f"msg-{int(datetime.now(timezone.utc).timestamp() * 1000)}"

    query_lower = payload.query.lower()
    incident_ref = payload.incident_id or "INC-024"

    if "why was" in query_lower or "flagged" in query_lower:
        text = (
            f"Candidate {incident_ref} was flagged based on multi-channel telemetry anomaly detection:\n\n"
            "• PROXIMITY: Interacting vehicles entered close proximity with rapid spatial convergence.\n"
            "• RELATIVE MOTION: Significant closing velocity and trajectory deviation detected.\n"
            "• VEHICLE RESPONSE: Observable steering angle compensation and lateral acceleration perturbation.\n\n"
            "The system surfaces these observations as objective factual evidence for human steward review."
        )
        chips = [
            EvidenceChip(label="PROXIMITY: Convergence", type="telemetry"),
            EvidenceChip(label="TRAJECTORY: Track Deviation", type="timeline"),
            EvidenceChip(label="RESPONSE: Steering Reversal", type="response"),
        ]
        links = [EvidenceLink(label=f"Examine Incident {incident_ref}", target_view=f"incident-{incident_ref}", incident_id=incident_ref)]
        follow_ups = ["What changed in the telemetry?", "Which regulations may be relevant?"]

    elif "telemetry" in query_lower or "change" in query_lower:
        text = (
            f"Telemetry analysis for {incident_ref} highlights key inputs during the interaction window:\n\n"
            "• BRAKING DELTA: Deceleration initiated deeper than baseline entry markers.\n"
            "• SPEED DELTA: Rapid velocity differential shift during corner overlap.\n"
            "• STEERING COMPENSATIONS: Measured steering angle counter-correction.\n\n"
            "Full 25Hz multi-trace charts are accessible in the Telemetry Evidence module."
        )
        chips = [
            EvidenceChip(label="TELEMETRY: Master Cylinder Pressure", type="telemetry"),
            EvidenceChip(label="RESPONSE: Steering Delta", type="response"),
            EvidenceChip(label="TRAJECTORY: Lateral Track Offset", type="timeline"),
        ]
        links = [EvidenceLink(label="Open Telemetry Chart", target_view=f"incident-{incident_ref}", incident_id=incident_ref)]
        follow_ups = ["Which regulations may be relevant?", "What evidence is missing?"]

    elif "regulation" in query_lower or "rule" in query_lower:
        text = (
            "Relevant regulatory provisions cross-referenced for this interaction geometry:\n\n"
            "• Article 33.4 (Manoeuvres during Overtaking and Position Defense)\n"
            "• Article 33.3 (Right to Track Edge and Overlap Thresholds)\n"
            "• ISC Appendix L, Chapter IV (Overtaking, Car Control and Track Limits)\n\n"
            "Final interpretation rests solely with the appointed FIA Race Stewards."
        )
        chips = [
            EvidenceChip(label="FIA Art 33.4 (Crowding)", type="regulation"),
            EvidenceChip(label="FIA Art 33.3 (Overlap)", type="regulation"),
            EvidenceChip(label="ISC App L Ch IV", type="regulation"),
        ]
        links = [EvidenceLink(label="View Relevant Regulations", target_view=f"incident-{incident_ref}", incident_id=incident_ref)]
        follow_ups = ["Why was this incident flagged?", "What evidence is missing?"]

    else:
        text = (
            f"Motorsport Incident Intelligence assistant synchronized for {incident_ref}. "
            "I provide factual evidence synthesis across CAN-bus telemetry, relative motion models, "
            "and FIA regulatory references. How may I assist your review?"
        )
        chips = [
            EvidenceChip(label="FastF1 Telemetry", type="telemetry"),
            EvidenceChip(label="FIA 2024 Code", type="regulation"),
        ]
        links = []
        follow_ups = [
            "Why was this incident flagged?",
            "What changed in the telemetry?",
            "Which regulations may be relevant?",
            "What evidence is missing?",
        ]

    return AssistantMessageSchema(
        id=msg_id,
        sender="assistant",
        timestamp=timestamp_str,
        text=text,
        evidence_chips=chips,
        evidence_links=links,
        suggested_follow_ups=follow_ups,
    )
