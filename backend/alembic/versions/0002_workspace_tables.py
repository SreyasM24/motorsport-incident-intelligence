"""Steward workspace investigation tables migration.

Revision ID: 0002_workspace_tables
Revises: 0001_initial_schema
Create Date: 2026-10-10 10:15:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_workspace_tables"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Evidence Acknowledgements
    op.create_table(
        "evidence_acknowledgements",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("candidate_id", sa.String(length=64), nullable=False),
        sa.Column(
            "incident_id",
            sa.String(length=64),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("evidence_id", sa.String(length=64), nullable=False),
        sa.Column("reviewer_id", sa.String(length=64), nullable=False, server_default="steward-panel"),
        sa.Column("action", sa.String(length=32), nullable=False, server_default="CONSIDERED"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_acknowledgements_id", "evidence_acknowledgements", ["id"], unique=False)
    op.create_index("ix_evidence_acknowledgements_candidate_id", "evidence_acknowledgements", ["candidate_id"], unique=False)
    op.create_index("ix_evidence_acknowledgements_incident_id", "evidence_acknowledgements", ["incident_id"], unique=False)
    op.create_index("ix_evidence_acknowledgements_evidence_id", "evidence_acknowledgements", ["evidence_id"], unique=False)
    op.create_index("ix_evidence_acknowledgements_action", "evidence_acknowledgements", ["action"], unique=False)

    # 2. Unresolved Questions
    op.create_table(
        "unresolved_questions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("candidate_id", sa.String(length=64), nullable=False),
        sa.Column(
            "incident_id",
            sa.String(length=64),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("question", sa.Text(), nullable=False),
        sa.Column("evidence_ids_json", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_unresolved_questions_id", "unresolved_questions", ["id"], unique=False)
    op.create_index("ix_unresolved_questions_candidate_id", "unresolved_questions", ["candidate_id"], unique=False)
    op.create_index("ix_unresolved_questions_incident_id", "unresolved_questions", ["incident_id"], unique=False)
    op.create_index("ix_unresolved_questions_status", "unresolved_questions", ["status"], unique=False)

    # 3. Discrepancy Annotations
    op.create_table(
        "discrepancy_annotations",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("candidate_id", sa.String(length=64), nullable=False),
        sa.Column(
            "incident_id",
            sa.String(length=64),
            sa.ForeignKey("incidents.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("discrepancy_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="OPEN"),
        sa.Column("reviewer_id", sa.String(length=64), nullable=False, server_default="steward-panel"),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_discrepancy_annotations_id", "discrepancy_annotations", ["id"], unique=False)
    op.create_index("ix_discrepancy_annotations_candidate_id", "discrepancy_annotations", ["candidate_id"], unique=False)
    op.create_index("ix_discrepancy_annotations_incident_id", "discrepancy_annotations", ["incident_id"], unique=False)
    op.create_index("ix_discrepancy_annotations_discrepancy_id", "discrepancy_annotations", ["discrepancy_id"], unique=False)
    op.create_index("ix_discrepancy_annotations_status", "discrepancy_annotations", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("discrepancy_annotations")
    op.drop_table("unresolved_questions")
    op.drop_table("evidence_acknowledgements")
