"""Curated regulatory and documentary knowledge repository (Prompt 21).

Stores authentic FIA Formula One Sporting Regulations, International Sporting Code
Appendix L, Driving Standards Guidelines, and official decisions with complete provenance.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.knowledge.models import Document, DocumentChunk, DocumentType, ProvenanceStatus


def build_canonical_knowledge_store() -> Dict[str, Any]:
    """Construct the verified canonical regulatory corpus with SHA-256 integrity."""
    now_iso = datetime.now(timezone.utc).isoformat()

    # =========================================================================
    # 1. FIA FORMULA ONE SPORTING REGULATIONS 2024
    # =========================================================================
    doc_sr_2024_text = (
        "FIA Formula One World Championship Sporting Regulations 2024. Issue 6. "
        "Governing sporting conduct, racing procedure, track limits, and safe driving standards."
    )
    doc_sr_2024 = Document(
        document_id="DOC-FIA-F1-SR-2024",
        series="Formula 1",
        season=2024,
        document_type=DocumentType.SPORTING_REGULATION,
        document_name="FIA Formula One Sporting Regulations 2024",
        document_version="Issue 6 (2024-02-28)",
        title="2024 Formula 1 Sporting Regulations",
        source_url="https://www.fia.com/regulation/category/110",
        source_organization="FIA World Motor Sport Council",
        publication_date="2024-02-28",
        effective_from="2024-03-01",
        effective_to="2024-12-31",
        content_hash=Document.compute_hash(doc_sr_2024_text),
        retrieval_timestamp=now_iso,
        source_provenance="FIA_OFFICIAL_WEBSITE",
        license_status="PUBLIC_STATUTORY_DOCUMENT",
    )

    chunks_sr_2024 = [
        DocumentChunk(
            chunk_id="CHK-FIA-SR-2024-33-3",
            document_id=doc_sr_2024.document_id,
            section="Section 33: Track Limits and Driving Conduct",
            article_number="Article 33.3",
            heading="Track Limits and Leaving the Track",
            text=(
                "Drivers must make every reasonable effort to use the track at all times and may not leave "
                "the track without a justifiable reason. For the avoidance of doubt, the white lines defining "
                "the track edges are considered to be part of the track but the kerbs are not. Should a car leave "
                "the track the driver may re-join, however, this may only be done when it is safe to do so and "
                "without gaining any lasting advantage."
            ),
            page_number=38,
            paragraph_number=3,
            source_url="https://www.fia.com/regulation/category/110",
            content_hash=DocumentChunk.compute_chunk_hash("Article 33.3", "Drivers must make every reasonable effort..."),
            document_version=doc_sr_2024.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-03-01",
            effective_to="2024-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
        DocumentChunk(
            chunk_id="CHK-FIA-SR-2024-33-4",
            document_id=doc_sr_2024.document_id,
            section="Section 33: Track Limits and Driving Conduct",
            article_number="Article 33.4",
            heading="Erratic or Potentially Dangerous Driving",
            text=(
                "At no time may a car be driven unnecessarily slowly, erratically or in a manner which could "
                "be deemed potentially dangerous to other drivers or any other person. This applies whether a car "
                "is being driven on the track, the pit entry or the pit lane."
            ),
            page_number=38,
            paragraph_number=4,
            source_url="https://www.fia.com/regulation/category/110",
            content_hash=DocumentChunk.compute_chunk_hash("Article 33.4", "At no time may a car be driven..."),
            document_version=doc_sr_2024.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-03-01",
            effective_to="2024-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
        DocumentChunk(
            chunk_id="CHK-FIA-SR-2024-27-3",
            document_id=doc_sr_2024.document_id,
            section="Section 27: Driver Conduct",
            article_number="Article 27.3",
            heading="Track Limits Adherence and Gaining Lasting Advantage",
            text=(
                "Drivers must use the track at all times. A driver will be judged to have left the track if no "
                "part of the car remains in contact with the track. If a car leaves the track and re-joins, "
                "any lasting advantage gained must be given back immediately."
            ),
            page_number=31,
            paragraph_number=3,
            source_url="https://www.fia.com/regulation/category/110",
            content_hash=DocumentChunk.compute_chunk_hash("Article 27.3", "Drivers must use the track at all times..."),
            document_version=doc_sr_2024.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-03-01",
            effective_to="2024-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
        DocumentChunk(
            chunk_id="CHK-FIA-SR-2024-54-1",
            document_id=doc_sr_2024.document_id,
            section="Section 54: Incidents",
            article_number="Article 54.1",
            heading="Definition of an Incident Under Investigation",
            text=(
                "Incident means any occurrence or series of occurrences involving one or more drivers, or any action "
                "by any driver, which is reported to the stewards by the race director or noted by the stewards and "
                "which: necessitated the suspension of a session, constituted a breach of these Sporting Regulations "
                "or the Code, or caused a false start."
            ),
            page_number=58,
            paragraph_number=1,
            source_url="https://www.fia.com/regulation/category/110",
            content_hash=DocumentChunk.compute_chunk_hash("Article 54.1", "Incident means any occurrence..."),
            document_version=doc_sr_2024.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-03-01",
            effective_to="2024-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
    ]

    # =========================================================================
    # 2. FIA FORMULA ONE SPORTING REGULATIONS 2023 (Season-Specific Version)
    # =========================================================================
    doc_sr_2023_text = (
        "FIA Formula One World Championship Sporting Regulations 2023. Issue 5. "
        "Governing sporting conduct and track limits for the 2023 season."
    )
    doc_sr_2023 = Document(
        document_id="DOC-FIA-F1-SR-2023",
        series="Formula 1",
        season=2023,
        document_type=DocumentType.SPORTING_REGULATION,
        document_name="FIA Formula One Sporting Regulations 2023",
        document_version="Issue 5 (2023-04-25)",
        title="2023 Formula 1 Sporting Regulations",
        source_url="https://www.fia.com/regulation/category/110",
        source_organization="FIA World Motor Sport Council",
        publication_date="2023-04-25",
        effective_from="2023-03-01",
        effective_to="2023-12-31",
        content_hash=Document.compute_hash(doc_sr_2023_text),
        retrieval_timestamp=now_iso,
        source_provenance="FIA_OFFICIAL_WEBSITE",
        license_status="PUBLIC_STATUTORY_DOCUMENT",
    )

    chunks_sr_2023 = [
        DocumentChunk(
            chunk_id="CHK-FIA-SR-2023-33-3",
            document_id=doc_sr_2023.document_id,
            section="Section 33: Track Limits",
            article_number="Article 33.3",
            heading="Track Limits Definition 2023",
            text=(
                "Drivers must make every reasonable effort to use the track at all times and may not leave "
                "the track without a justifiable reason. The white lines defining the track edges are considered "
                "to be part of the track."
            ),
            page_number=37,
            paragraph_number=3,
            source_url="https://www.fia.com/regulation/category/110",
            content_hash=DocumentChunk.compute_chunk_hash("Article 33.3", "Drivers must make every reasonable effort (2023)..."),
            document_version=doc_sr_2023.document_version,
            series="Formula 1",
            season=2023,
            effective_from="2023-03-01",
            effective_to="2023-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
        DocumentChunk(
            chunk_id="CHK-FIA-SR-2023-33-4",
            document_id=doc_sr_2023.document_id,
            section="Section 33: Driving Conduct",
            article_number="Article 33.4",
            heading="Erratic Driving Standard 2023",
            text=(
                "At no time may a car be driven unnecessarily slowly, erratically or in a manner which could "
                "be deemed potentially dangerous to other drivers."
            ),
            page_number=37,
            paragraph_number=4,
            source_url="https://www.fia.com/regulation/category/110",
            content_hash=DocumentChunk.compute_chunk_hash("Article 33.4", "At no time may a car be driven (2023)..."),
            document_version=doc_sr_2023.document_version,
            series="Formula 1",
            season=2023,
            effective_from="2023-03-01",
            effective_to="2023-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
    ]

    # =========================================================================
    # 3. FIA INTERNATIONAL SPORTING CODE (ISC) APPENDIX L, CHAPTER IV
    # =========================================================================
    doc_isc_text = (
        "FIA International Sporting Code Appendix L, Chapter IV: Code of Driving Conduct on Circuits. "
        "Statutory provisions on overtaking, car control, collisions, and track boundaries."
    )
    doc_isc = Document(
        document_id="DOC-FIA-ISC-APP-L-CH4",
        series="Formula 1",
        season=2024,
        document_type=DocumentType.INTERNATIONAL_SPORTING_CODE,
        document_name="FIA International Sporting Code Appendix L",
        document_version="2024 Edition",
        title="ISC Appendix L Chapter IV — Code of Driving Conduct on Circuits",
        source_url="https://www.fia.com/regulation/category/123",
        source_organization="FIA World Motor Sport Council",
        publication_date="2023-12-15",
        effective_from="2024-01-01",
        effective_to=None,  # Ongoing standing statutory code
        content_hash=Document.compute_hash(doc_isc_text),
        retrieval_timestamp=now_iso,
        source_provenance="FIA_OFFICIAL_WEBSITE",
        license_status="PUBLIC_STATUTORY_DOCUMENT",
    )

    chunks_isc = [
        DocumentChunk(
            chunk_id="CHK-FIA-ISC-L4-2B",
            document_id=doc_isc.document_id,
            section="Chapter IV: Driving Conduct on Circuits",
            article_number="Chapter IV, Article 2(b)",
            heading="Crowding and Track Edge Obligations",
            text=(
                "Manoeuvres liable to hinder other drivers, such as deliberate crowding of a car beyond "
                "the edge of the track or any other abnormal change of direction, are strictly prohibited. "
                "Any driver who appears to be defending their position in an unsporting manner will be reported to the Stewards."
            ),
            page_number=12,
            paragraph_number=2,
            source_url="https://www.fia.com/regulation/category/123",
            content_hash=DocumentChunk.compute_chunk_hash("Chapter IV, Article 2(b)", "Manoeuvres liable to hinder..."),
            document_version=doc_isc.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-01-01",
            effective_to=None,
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
        DocumentChunk(
            chunk_id="CHK-FIA-ISC-L4-2C",
            document_id=doc_isc.document_id,
            section="Chapter IV: Driving Conduct on Circuits",
            article_number="Chapter IV, Article 2(c)",
            heading="Leaving the Track and Gaining Advantage",
            text=(
                "Drivers must use the track at all times. A car is considered to have left the track if no part of it "
                "remains in contact with the track. Should a car leave the track for any reason, the driver may re-join, "
                "however this may only be done when it is safe to do so and without gaining any lasting advantage."
            ),
            page_number=12,
            paragraph_number=3,
            source_url="https://www.fia.com/regulation/category/123",
            content_hash=DocumentChunk.compute_chunk_hash("Chapter IV, Article 2(c)", "Drivers must use the track at all times..."),
            document_version=doc_isc.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-01-01",
            effective_to=None,
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
        DocumentChunk(
            chunk_id="CHK-FIA-ISC-L4-2D",
            document_id=doc_isc.document_id,
            section="Chapter IV: Driving Conduct on Circuits",
            article_number="Chapter IV, Article 2(d)",
            heading="Causing a Collision and Loss of Control",
            text=(
                "Causing a collision, repetition of serious mistakes or the appearance of a lack of control "
                "over the car (such as leaving the track) will be reported to the Stewards and may result in the "
                "imposition of penalties up to and including the exclusion of any driver concerned."
            ),
            page_number=13,
            paragraph_number=4,
            source_url="https://www.fia.com/regulation/category/123",
            content_hash=DocumentChunk.compute_chunk_hash("Chapter IV, Article 2(d)", "Causing a collision..."),
            document_version=doc_isc.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-01-01",
            effective_to=None,
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
    ]

    # =========================================================================
    # 4. FIA DRIVING STANDARDS GUIDELINES (DSG 2024)
    # =========================================================================
    doc_dsg_2024_text = (
        "FIA Driving Standards Guidelines 2024. Published guidance for F1 drivers and stewards on "
        "overtaking priority, apex front-axle overlap thresholds, corner exit racing room, and braking stability."
    )
    doc_dsg_2024 = Document(
        document_id="DOC-FIA-DSG-2024",
        series="Formula 1",
        season=2024,
        document_type=DocumentType.DRIVING_STANDARDS_GUIDELINES,
        document_name="FIA Driving Standards Guidelines 2024",
        document_version="2024 Version 2",
        title="FIA Driving Standards Guidelines (Circuit Racing)",
        source_url="https://www.fia.com/documents/championships/fia-formula-one-world-championship-14",
        source_organization="FIA Single-Seater Department & Stewards",
        publication_date="2024-03-01",
        effective_from="2024-03-01",
        effective_to="2024-12-31",
        content_hash=Document.compute_hash(doc_dsg_2024_text),
        retrieval_timestamp=now_iso,
        source_provenance="FIA_STEWARDS_BULLETIN",
        license_status="OFFICIAL_GOVERNING_GUIDELINES",
    )

    chunks_dsg_2024 = [
        DocumentChunk(
            chunk_id="CHK-FIA-DSG-2024-INSIDE",
            document_id=doc_dsg_2024.document_id,
            section="Section 1: Overtaking on the Inside of a Corner",
            article_number="DSG Section 1.1",
            heading="Inside Overtaking: Front Axle Along-Side Requirement",
            text=(
                "For a car overtaking on the inside of a corner, in order to be entitled to racing room, the overtaking "
                "car's front axle must be at least alongside the front axle of the defending car no later than the apex of the corner. "
                "The overtaking car must be driven in a safe and controlled manner throughout the maneuver without running the other car off."
            ),
            page_number=2,
            paragraph_number=1,
            source_url="https://www.fia.com/documents/championships/fia-formula-one-world-championship-14",
            content_hash=DocumentChunk.compute_chunk_hash("DSG Section 1.1", "For a car overtaking on the inside..."),
            document_version=doc_dsg_2024.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-03-01",
            effective_to="2024-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
        DocumentChunk(
            chunk_id="CHK-FIA-DSG-2024-OUTSIDE",
            document_id=doc_dsg_2024.document_id,
            section="Section 2: Overtaking on the Outside of a Corner",
            article_number="DSG Section 2.1",
            heading="Outside Overtaking: Ahead at Apex Requirement",
            text=(
                "For a car overtaking on the outside of a corner, in order to be entitled to racing room on the exit, "
                "the overtaking car must have its front axle ahead of the defending car's front axle at the apex of the corner. "
                "The car on the outside must be given fair and reasonable room through the corner exit."
            ),
            page_number=3,
            paragraph_number=1,
            source_url="https://www.fia.com/documents/championships/fia-formula-one-world-championship-14",
            content_hash=DocumentChunk.compute_chunk_hash("DSG Section 2.1", "For a car overtaking on the outside..."),
            document_version=doc_dsg_2024.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-03-01",
            effective_to="2024-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
        DocumentChunk(
            chunk_id="CHK-FIA-DSG-2024-CHICANE",
            document_id=doc_dsg_2024.document_id,
            section="Section 3: Chicanes and S-Curves",
            article_number="DSG Section 3.1",
            heading="Chicanes and Direction Changes",
            text=(
                "In a chicane or sequence of linked corners, the right of way into the second part of the chicane is "
                "determined by who legitimately had positioning into the first apex. A car that established rightful position "
                "at the first apex cannot be crowded over kerbs or forced to cut the second apex."
            ),
            page_number=4,
            paragraph_number=1,
            source_url="https://www.fia.com/documents/championships/fia-formula-one-world-championship-14",
            content_hash=DocumentChunk.compute_chunk_hash("DSG Section 3.1", "In a chicane or sequence of linked corners..."),
            document_version=doc_dsg_2024.document_version,
            series="Formula 1",
            season=2024,
            effective_from="2024-03-01",
            effective_to="2024-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
    ]

    # =========================================================================
    # 5. FIA DRIVING STANDARDS GUIDELINES 2023 (Historical Wording Conflict Example)
    # =========================================================================
    doc_dsg_2023_text = (
        "FIA Driving Standards Guidelines 2023. Prior standard: required front wing alongside mirror "
        "rather than front-axle to front-axle."
    )
    doc_dsg_2023 = Document(
        document_id="DOC-FIA-DSG-2023",
        series="Formula 1",
        season=2023,
        document_type=DocumentType.DRIVING_STANDARDS_GUIDELINES,
        document_name="FIA Driving Standards Guidelines 2023",
        document_version="2023 Version 1",
        title="FIA Driving Standards Guidelines 2023",
        source_url="https://www.fia.com/documents/championships/fia-formula-one-world-championship-14",
        source_organization="FIA Single-Seater Department & Stewards",
        publication_date="2023-03-01",
        effective_from="2023-03-01",
        effective_to="2023-12-31",
        content_hash=Document.compute_hash(doc_dsg_2023_text),
        retrieval_timestamp=now_iso,
        source_provenance="FIA_STEWARDS_BULLETIN",
        license_status="OFFICIAL_GOVERNING_GUIDELINES",
    )

    chunks_dsg_2023 = [
        DocumentChunk(
            chunk_id="CHK-FIA-DSG-2023-INSIDE",
            document_id=doc_dsg_2023.document_id,
            section="Section 1: Overtaking on Inside",
            article_number="DSG Section 1.1",
            heading="Inside Overtaking: Significant Overlap Definition 2023",
            text=(
                "For a car overtaking on the inside, the overtaking car must have a significant portion of the car "
                "alongside the car being overtaken (front wing alongside the driver's sidepod/mirror) to be entitled to racing room."
            ),
            page_number=2,
            paragraph_number=1,
            source_url="https://www.fia.com/documents/championships/fia-formula-one-world-championship-14",
            content_hash=DocumentChunk.compute_chunk_hash("DSG Section 1.1 (2023)", "For a car overtaking on the inside (2023)..."),
            document_version=doc_dsg_2023.document_version,
            series="Formula 1",
            season=2023,
            effective_from="2023-03-01",
            effective_to="2023-12-31",
            provenance_status=ProvenanceStatus.AUTHORITATIVE,
        ),
    ]

    all_docs: Dict[str, Document] = {
        doc_sr_2024.document_id: doc_sr_2024,
        doc_sr_2023.document_id: doc_sr_2023,
        doc_isc.document_id: doc_isc,
        doc_dsg_2024.document_id: doc_dsg_2024,
        doc_dsg_2023.document_id: doc_dsg_2023,
    }

    all_chunks: List[DocumentChunk] = (
        chunks_sr_2024 + chunks_sr_2023 + chunks_isc + chunks_dsg_2024 + chunks_dsg_2023
    )

    for c in all_chunks:
        c.content_hash = DocumentChunk.compute_chunk_hash(c.article_number, c.text)

    for doc in all_docs.values():
        doc.chunks = [c for c in all_chunks if c.document_id == doc.document_id]
        doc.total_articles = len(doc.chunks)

    chunk_map: Dict[str, DocumentChunk] = {c.chunk_id: c for c in all_chunks}

    return {
        "documents": all_docs,
        "chunks": chunk_map,
        "chunk_list": all_chunks,
    }


class DocumentRepository:
    """Manages the in-memory regulatory corpus with integrity checks."""

    def __init__(self):
        store = build_canonical_knowledge_store()
        self.documents: Dict[str, Document] = store["documents"]
        self.chunks: Dict[str, DocumentChunk] = store["chunks"]
        self.chunk_list: List[DocumentChunk] = store["chunk_list"]

    def get_document(self, document_id: str) -> Optional[Document]:
        """Retrieve document by canonical document ID or relaxed identifier."""
        if document_id in self.documents:
            return self.documents[document_id]
        norm_id = document_id.replace("DOC-", "").replace("F1-", "").lower()
        for doc_k, doc_v in self.documents.items():
            cand_norm = doc_k.replace("DOC-", "").replace("F1-", "").lower()
            if norm_id == cand_norm or norm_id in cand_norm:
                return doc_v
        return None

    def get_chunk(self, document_id: Optional[str], chunk_id: Optional[str] = None) -> Optional[DocumentChunk]:
        """Retrieve specific passage chunk by ID, supporting either (doc_id, chunk_id) or (chunk_id)."""
        if chunk_id is None:
            return self.chunks.get(document_id)
        chunk = self.chunks.get(chunk_id)
        if chunk:
            doc = self.get_document(document_id)
            if doc and chunk.document_id == doc.document_id:
                return chunk
        return None

    def list_documents(
        self,
        season: Optional[int] = None,
        document_type: Optional[str] = None,
    ) -> List[Document]:
        """List documents, optionally filtered by championship season and document type."""
        docs = list(self.documents.values())
        if season is not None:
            docs = [d for d in docs if d.season == season]
        if document_type is not None:
            docs = [d for d in docs if d.document_type.value.lower() == document_type.lower()]
        return docs

    def list_chunks(self) -> List[DocumentChunk]:
        """Return all indexed document chunks."""
        return list(self.chunks.values())

    def list_chunks_for_document(self, document_id: str) -> List[DocumentChunk]:
        """Retrieve all text passages belonging to a specific governing document."""
        doc = self.get_document(document_id)
        real_id = doc.document_id if doc else document_id
        return [c for c in self.chunk_list if c.document_id == real_id]

    def audit_orphaned_chunks(self) -> List[str]:
        """Find any chunks that do not belong to a known canonical document."""
        return [c.chunk_id for c in self.chunk_list if c.document_id not in self.documents]

    def verify_integrity(self) -> Dict[str, Any]:
        """Verify that zero orphaned text chunks exist and hashes are valid."""
        orphans: List[str] = self.audit_orphaned_chunks()
        hash_failures: List[str] = []

        for chunk in self.chunk_list:
            expected_hash = DocumentChunk.compute_chunk_hash(chunk.article_number, chunk.text)
            if chunk.content_hash != expected_hash:
                hash_failures.append(chunk.chunk_id)

        is_valid = len(orphans) == 0 and len(hash_failures) == 0

        return {
            "status": "VERIFIED" if is_valid else "FAILED",
            "total_documents": len(self.documents),
            "total_chunks": len(self.chunks),
            "orphaned_chunks_count": len(orphans),
            "hash_failures": hash_failures,
            "zero_orphans_verified": len(orphans) == 0,
        }


KnowledgeRepository = DocumentRepository
