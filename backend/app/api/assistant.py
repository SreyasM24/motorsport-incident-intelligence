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

    elif any(k in query_lower for k in ["regulation", "rule", "code", "guideline", "article", "overtaking", "track limits", "penalty"]):
        import re
        from app.knowledge.service import KnowledgeRetrievalService
        from app.knowledge.models import RetrievalMethod

        knowledge_svc = KnowledgeRetrievalService.get_instance()
        search_res = knowledge_svc.search_regulations(
            query=payload.query,
            season=2024,
            method=RetrievalMethod.HYBRID,
            limit=3,
        )

        # Check if the query contains nonsense/unsupported concepts with zero lexical grounding
        stop_tokens = {"regulation", "regulations", "rule", "rules", "regarding", "what", "which", "the", "in", "of", "and", "is", "a", "for", "to", "apply", "applies"}
        substantive_tokens = [
            t for t in re.findall(r"\w+", query_lower)
            if t not in stop_tokens
        ]
        has_substantive_overlap = False
        if search_res.citations and substantive_tokens:
            for cit in search_res.citations:
                c_text = f"{cit.heading} {cit.verbatim_text}".lower()
                if any(st in c_text for st in substantive_tokens):
                    has_substantive_overlap = True
                    break

        if not search_res.citations or (substantive_tokens and not has_substantive_overlap):
            text = (
                "INSUFFICIENT_DOCUMENTARY_EVIDENCE: No canonical regulatory provisions or driving standard "
                f"guidelines in the knowledge base match the query: '{payload.query}'.\n\n"
                "CRITICAL NON-ADJUDICATIVE NOTICE: The system does not speculate or make unsupported assertions. "
                "All regulatory review requires grounded documentary citations."
            )
            chips = [EvidenceChip(label="Status: INSUFFICIENT_EVIDENCE", type="regulation")]
            links = []
        else:
            lines = [
                f"Citation-grounded regulatory references for incident {incident_ref}:\n"
            ]
            chips = []
            links = []

            for idx, c in enumerate(search_res.citations, start=1):
                chunk = c.chunk
                lines.append(
                    f"{idx}. [{chunk.document_id}] {chunk.article_number} ({chunk.title or 'Standard'})\n"
                    f"   \"{chunk.text[:220]}...\"\n"
                    f"   Relevance: {c.relevance_score:.2f} | Method: {c.retrieval_method.value} | Status: {c.provenance_status.value}\n"
                )
                chips.append(
                    EvidenceChip(
                        label=f"{chunk.document_id} {chunk.article_number}",
                        type="regulation",
                    )
                )
                links.append(
                    EvidenceLink(
                        label=f"View {chunk.article_number}",
                        target_view=f"/evidence/documents/{chunk.document_id}",
                        incident_id=incident_ref,
                    )
                )

            if search_res.source_conflicts:
                lines.append("\nSOURCE_CONFLICT DETECTED:")
                for conflict in search_res.source_conflicts:
                    lines.append(
                        f"• Conflicting texts across [{conflict.document_id_a}] and [{conflict.document_id_b}] "
                        f"for {conflict.article_number}: {conflict.conflict_description}. "
                        "Automated resolution is prohibited; deferred to human stewards."
                    )
                chips.append(EvidenceChip(label="FLAG: SOURCE_CONFLICT", type="regulation"))

            lines.append(f"\n{search_res.non_adjudication_statement}")
            text = "\n".join(lines)

        follow_ups = ["Why was this incident flagged?", "What changed in the telemetry?", "What evidence is missing?"]

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
