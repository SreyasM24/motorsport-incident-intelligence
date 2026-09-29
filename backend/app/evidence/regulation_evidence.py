"""Deterministic FIA regulation referencing and evidence-rule linkages.

CRITICAL JURISPRUDENTIAL DOCTRINE:
    Regulatory references are attached as objective standards of evaluation for human stewards.
    They do NOT assert that an infringement or violation occurred.
    Neutral phrasing: "Potentially relevant regulatory provision."
"""

from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from app.evidence.candidate import CandidateEventType


class RegulationReference(BaseModel):
    """An official statutory regulation provision pertinent to the interaction profile."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    id: str
    series: str = "FIA Formula One World Championship"
    season: str = "2024"
    document: str = Field(..., description="E.g. 'FIA Formula One Sporting Regulations 2024'")
    article: str = Field(..., description="E.g. 'Article 33.4'")
    title: str = Field(..., description="Title of regulatory section")
    text_reference: str = Field(..., description="Verbatim statutory text excerpt")
    source_url: Optional[str] = "https://www.fia.com/regulation/category/110"
    relevance_reason: str = Field(..., description="Neutral explanation of why this rule is attached")
    relevance_level: str = Field(default="High", description="High, Medium, or Low")


class EvidenceRegulationLink(BaseModel):
    """3-way evidentiary link connecting empirical measurement to statutory rule and steward action."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    observed_evidence: str
    relevant_regulation: str
    steward_review_action: str


class RegulationEvidenceSummary(BaseModel):
    """Synthesized regulatory context section for an incident evidence dossier."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    status: str = "REGULATION_REFERENCES_ATTACHED"
    references: List[RegulationReference] = Field(default_factory=list)
    evidence_links: List[EvidenceRegulationLink] = Field(default_factory=list)
    stewardship_doctrine: str = Field(
        default="Regulatory provisions stipulate the legal framework for human steward review. "
        "The attachment of an article provides contextual relevance and does not assert an infringement."
    )


# Canonical Repository of Key FIA Formula One Sporting Provisions
FIA_REGULATION_REPOSITORY: List[RegulationReference] = [
    RegulationReference(
        id="REG-FIA-ISC-L4-2B",
        document="FIA International Sporting Code Appendix L",
        article="Chapter IV, Article 2(b)",
        title="Crowding and Track Edge Obligations",
        text_reference="Manoeuvres liable to hinder other drivers, such as deliberate crowding of a car beyond "
        "the edge of the track or any other abnormal change of direction, are strictly prohibited.",
        relevance_reason="Potentially relevant regulatory provision governing side-by-side positioning and crowding toward track boundaries.",
        relevance_level="High",
    ),
    RegulationReference(
        id="REG-FIA-ISC-L4-2D",
        document="FIA International Sporting Code Appendix L",
        article="Chapter IV, Article 2(d)",
        title="Causing a Collision",
        text_reference="Causing a collision, repetition of serious mistakes or the appearance of a lack of control "
        "over the car (such as leaving the track) will be reported to the Stewards and may result in the imposition of penalties.",
        relevance_reason="Potentially relevant regulatory standard regarding vehicle contact, loss of trajectory control, and collision liability.",
        relevance_level="High",
    ),
    RegulationReference(
        id="REG-FIA-SR-33-4",
        document="FIA Formula One Sporting Regulations 2024",
        article="Article 33.4",
        title="Erratic or Potentially Dangerous Driving",
        text_reference="At no time may a car be driven unnecessarily slowly, erratically or in a manner which could "
        "be deemed potentially dangerous to other drivers or any other person.",
        relevance_reason="Potentially relevant standard governing unexpected deceleration, severe braking differentials, and erratic trajectories.",
        relevance_level="Medium",
    ),
    RegulationReference(
        id="REG-FIA-SR-33-3",
        document="FIA Formula One Sporting Regulations 2024",
        article="Article 33.3",
        title="Track Limits and Leaving the Track",
        text_reference="Drivers must make every reasonable effort to use the track at all times and may not leave the track without a justifiable reason.",
        relevance_reason="Potentially relevant provision when trajectory deviation or off-track excursions are detected during an encounter.",
        relevance_level="Medium",
    ),
]


def match_relevant_regulations(
    event_type: CandidateEventType,
    minimum_gap: float,
    decel_delta_g: float,
) -> RegulationEvidenceSummary:
    """Deterministically select applicable regulation references based on empirical event characteristics."""
    selected_refs: List[RegulationReference] = []
    links: List[EvidenceRegulationLink] = []

    # If contact candidate or critical proximity (< 4.0m)
    if event_type == CandidateEventType.CONTACT_CANDIDATE or minimum_gap <= 4.0:
        ref_collision = next(r for r in FIA_REGULATION_REPOSITORY if r.article == "Chapter IV, Article 2(d)")
        ref_crowd = next(r for r in FIA_REGULATION_REPOSITORY if r.article == "Chapter IV, Article 2(b)")
        selected_refs.extend([ref_collision, ref_crowd])

        links.append(
            EvidenceRegulationLink(
                observed_evidence=f"Critical spatial proximity (minimum gap {minimum_gap:.2f}m) indicating wheel overlap.",
                relevant_regulation="FIA ISC Appendix L, Chapter IV, Article 2(d) (Causing a Collision)",
                steward_review_action="Examine camera footage to determine whether contact occurred and assess apex ownership under Driving Standards Guidelines.",
            )
        )
        links.append(
            EvidenceRegulationLink(
                observed_evidence="Trajectory convergence at corner entry / apex.",
                relevant_regulation="FIA ISC Appendix L, Chapter IV, Article 2(b) (Crowding off track)",
                steward_review_action="Verify whether outside car was afforded one car width of racing room at track boundary.",
            )
        )

    # If severe deceleration delta
    if decel_delta_g >= 2.0 or event_type == CandidateEventType.SUDDEN_DECELERATION_EVENT:
        ref_erratic = next(r for r in FIA_REGULATION_REPOSITORY if r.article == "Article 33.4")
        if ref_erratic not in selected_refs:
            selected_refs.append(ref_erratic)

        links.append(
            EvidenceRegulationLink(
                observed_evidence=f"Differential deceleration spike ({decel_delta_g:.1f}G) between interacting cars.",
                relevant_regulation="FIA F1 Sporting Regulations, Article 33.4 (Erratic / Dangerous Driving)",
                steward_review_action="Assess telemetry trace for unprompted lift-off or erratic braking maneuver.",
            )
        )

    # Fallback default if no specific match
    if not selected_refs:
        selected_refs.append(FIA_REGULATION_REPOSITORY[0])
        links.append(
            EvidenceRegulationLink(
                observed_evidence=f"Close wheel-to-wheel following ({minimum_gap:.1f}m gap).",
                relevant_regulation="FIA ISC Appendix L, Chapter IV, Article 2(b)",
                steward_review_action="Review standard overtaking clearance.",
            )
        )

    return RegulationEvidenceSummary(
        status="REGULATION_REFERENCES_ATTACHED",
        references=selected_refs,
        evidence_links=links,
    )
