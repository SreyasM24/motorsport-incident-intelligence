"""Initial database schema migration for Motorsport Incident Intelligence.

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-09-29 08:45:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Races
    op.create_table(
        "races",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("series", sa.String(length=64), nullable=False, server_default="Formula 1"),
        sa.Column("season", sa.String(length=16), nullable=False),
        sa.Column("round", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("circuit", sa.String(length=128), nullable=False),
        sa.Column("country", sa.String(length=64), nullable=False),
        sa.Column("city", sa.String(length=64), nullable=True),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="fastf1"),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_races_id", "races", ["id"], unique=False)
    op.create_index("ix_races_series", "races", ["series"], unique=False)
    op.create_index("ix_races_season", "races", ["season"], unique=False)

    # 2. Sessions
    op.create_table(
        "sessions",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("race_id", sa.String(length=64), sa.ForeignKey("races.id", ondelete="CASCADE"), nullable=False),
        sa.Column("session_type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("total_laps", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="ANALYSIS_READY"),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="fastf1"),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_sessions_id", "sessions", ["id"], unique=False)
    op.create_index("ix_sessions_race_id", "sessions", ["race_id"], unique=False)
    op.create_index("ix_sessions_session_type", "sessions", ["session_type"], unique=False)
    op.create_index("ix_sessions_status", "sessions", ["status"], unique=False)

    # 3. Drivers
    op.create_table(
        "drivers",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", sa.String(length=8), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=128), nullable=False),
        sa.Column("first_name", sa.String(length=64), nullable=True),
        sa.Column("last_name", sa.String(length=64), nullable=True),
        sa.Column("abbreviation", sa.String(length=8), nullable=False),
        sa.Column("nationality", sa.String(length=32), nullable=True),
        sa.Column("team", sa.String(length=128), nullable=False),
        sa.Column("team_color", sa.String(length=16), nullable=True),
        sa.Column("secondary_color", sa.String(length=16), nullable=True),
        sa.Column("laps_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_speed_kmh", sa.Float(), nullable=True),
        sa.Column("max_speed_kmh", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="fastf1"),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("session_id", "code", name="uq_session_driver_code"),
    )
    op.create_index("ix_drivers_id", "drivers", ["id"], unique=False)
    op.create_index("ix_drivers_session_id", "drivers", ["session_id"], unique=False)
    op.create_index("ix_drivers_code", "drivers", ["code"], unique=False)

    # 4. Incidents
    op.create_table(
        "incidents",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("incident_type", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="REQUIRES_REVIEW"),
        sa.Column("severity", sa.String(length=16), nullable=False, server_default="MEDIUM"),
        sa.Column("lap", sa.Integer(), nullable=False),
        sa.Column("turn", sa.String(length=64), nullable=False),
        sa.Column("timestamp_str", sa.String(length=32), nullable=False),
        sa.Column("start_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("track_position", sa.String(length=64), nullable=True),
        sa.Column("x", sa.Float(), nullable=True),
        sa.Column("y", sa.Float(), nullable=True),
        sa.Column("z", sa.Float(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("detection_method", sa.String(length=128), nullable=True),
        sa.Column("evidence_strength", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("analysis_version", sa.String(length=32), nullable=True, server_default="v1.0"),
        sa.Column("video_available", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("video_path", sa.String(length=256), nullable=True),
        sa.Column("telemetry_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("regulations_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="fastf1"),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("candidate_id", sa.String(length=64), nullable=True),
        sa.Column("canonical_fingerprint", sa.String(length=128), nullable=True),
        sa.Column("preprocessing_version", sa.String(length=32), nullable=True, server_default="telemetry_preprocessing_v1"),
        sa.Column("data_quality_summary", sa.String(length=64), nullable=True, server_default="FULL_FIDELITY"),
        sa.Column("minimum_gap_meters", sa.Float(), nullable=True),
        sa.Column("peak_closing_speed_ms", sa.Float(), nullable=True),
        sa.Column("dossier_data", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_incidents_id", "incidents", ["id"], unique=False)
    op.create_index("ix_incidents_session_id", "incidents", ["session_id"], unique=False)
    op.create_index("ix_incidents_status", "incidents", ["status"], unique=False)
    op.create_index("ix_incidents_severity", "incidents", ["severity"], unique=False)
    op.create_index("ix_incidents_lap", "incidents", ["lap"], unique=False)
    op.create_index("ix_incidents_candidate_id", "incidents", ["candidate_id"], unique=False)
    op.create_index("ix_incidents_canonical_fingerprint", "incidents", ["canonical_fingerprint"], unique=False)

    # 5. Incident Drivers (junction)
    op.create_table(
        "incident_drivers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("incident_id", sa.String(length=64), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", sa.String(length=64), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="INVOLVED"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("incident_id", "driver_id", name="uq_incident_driver"),
    )
    op.create_index("ix_incident_drivers_incident_id", "incident_drivers", ["incident_id"], unique=False)
    op.create_index("ix_incident_drivers_driver_id", "incident_drivers", ["driver_id"], unique=False)

    # 6. Telemetry
    op.create_table(
        "telemetry",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("session_id", sa.String(length=64), sa.ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("driver_id", sa.String(length=64), sa.ForeignKey("drivers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("time_offset", sa.Float(), nullable=False),
        sa.Column("lap_number", sa.Integer(), nullable=True),
        sa.Column("distance", sa.Float(), nullable=True),
        sa.Column("x", sa.Float(), nullable=True),
        sa.Column("y", sa.Float(), nullable=True),
        sa.Column("z", sa.Float(), nullable=True),
        sa.Column("speed", sa.Float(), nullable=True),
        sa.Column("throttle", sa.Float(), nullable=True),
        sa.Column("brake", sa.Float(), nullable=True),
        sa.Column("steering", sa.Float(), nullable=True),
        sa.Column("gear", sa.Integer(), nullable=True),
        sa.Column("rpm", sa.Integer(), nullable=True),
        sa.Column("drs", sa.Integer(), nullable=True),
        sa.Column("accel_x", sa.Float(), nullable=True),
        sa.Column("accel_y", sa.Float(), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False, server_default="fastf1"),
    )
    op.create_index("ix_telemetry_session_id", "telemetry", ["session_id"], unique=False)
    op.create_index("ix_telemetry_driver_id", "telemetry", ["driver_id"], unique=False)
    op.create_index("ix_telemetry_timestamp", "telemetry", ["timestamp"], unique=False)
    op.create_index("ix_telemetry_session_driver_time", "telemetry", ["session_id", "driver_id", "timestamp"], unique=False)
    op.create_index("ix_telemetry_session_lap", "telemetry", ["session_id", "lap_number"], unique=False)

    # 7. Regulations
    op.create_table(
        "regulations",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("series", sa.String(length=64), nullable=False, server_default="Formula 1"),
        sa.Column("season", sa.String(length=16), nullable=False),
        sa.Column("document", sa.String(length=128), nullable=False),
        sa.Column("document_version", sa.String(length=32), nullable=True),
        sa.Column("article", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_url", sa.String(length=512), nullable=True),
        sa.Column("effective_date", sa.Date(), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False, server_default="FIA World Motor Sport Council"),
        sa.Column("source_id", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_regulations_id", "regulations", ["id"], unique=False)
    op.create_index("ix_regulations_series", "regulations", ["series"], unique=False)
    op.create_index("ix_regulations_season", "regulations", ["season"], unique=False)
    op.create_index("ix_regulations_article", "regulations", ["article"], unique=False)

    # 8. Review Records
    op.create_table(
        "review_records",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("incident_id", sa.String(length=64), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="REQUIRES_REVIEW"),
        sa.Column("reviewer_id", sa.String(length=64), nullable=False, server_default="steward-panel"),
        sa.Column("review_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("evidence_considered", sa.Text(), nullable=True),
        sa.Column("evidence_missing", sa.Text(), nullable=True),
        sa.Column("observations", sa.Text(), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("review_rationale", sa.Text(), nullable=True),
        sa.Column("regulatory_references", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_review_records_id", "review_records", ["id"], unique=False)
    op.create_index("ix_review_records_incident_id", "review_records", ["incident_id"], unique=False)
    op.create_index("ix_review_records_status", "review_records", ["status"], unique=False)


def downgrade() -> None:
    op.drop_table("review_records")
    op.drop_table("regulations")
    op.drop_table("telemetry")
    op.drop_table("incident_drivers")
    op.drop_table("incidents")
    op.drop_table("drivers")
    op.drop_table("sessions")
    op.drop_table("races")
