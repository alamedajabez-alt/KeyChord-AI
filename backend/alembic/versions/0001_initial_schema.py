"""initial schema

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql as pg

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

UUID = sa.Uuid()
TS = sa.DateTime(timezone=True)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID, nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_table(
        "songs",
        sa.Column("id", UUID, nullable=False),
        sa.Column("user_id", UUID, nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("storage_path", sa.String(512), nullable=False),
        sa.Column("duration", sa.Float, nullable=False),
        sa.Column("audio_format", sa.String(16), nullable=False),
        sa.Column("size_bytes", sa.Integer, nullable=False),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_songs"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_songs_user_id_users"),
        sa.CheckConstraint("duration > 0", name="ck_songs_duration_positive"),
    )
    op.create_index("ix_songs_user_id_created_at", "songs", ["user_id", "created_at"])
    op.create_table(
        "analyses",
        sa.Column("id", UUID, nullable=False),
        sa.Column("song_id", UUID, nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("stage", sa.String(48)),
        sa.Column("progress", sa.Float, nullable=False),
        sa.Column("error_message", sa.Text),
        sa.Column("estimated_key", sa.String(16)),
        sa.Column("key_confidence", sa.Float),
        sa.Column("alternative_keys", pg.JSONB),
        sa.Column("tempo", sa.Float),
        sa.Column("analysis_version", sa.String(32), nullable=False),
        sa.Column("params", pg.JSONB),
        sa.Column("created_at", TS, server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", TS),
        sa.Column("completed_at", TS),
        sa.PrimaryKeyConstraint("id", name="pk_analyses"),
        sa.ForeignKeyConstraint(["song_id"], ["songs.id"], ondelete="CASCADE", name="fk_analyses_song_id_songs"),
        sa.CheckConstraint("status IN ('queued', 'running', 'completed', 'failed')", name="ck_analyses_status_valid"),
        sa.CheckConstraint("progress >= 0 AND progress <= 1", name="ck_analyses_progress_range"),
    )
    op.create_index("ix_analyses_song_id", "analyses", ["song_id"])
    op.create_index("ix_analyses_status_created_at", "analyses", ["status", "created_at"])
    op.create_table(
        "detected_chords",
        sa.Column("id", UUID, nullable=False),
        sa.Column("analysis_id", UUID, nullable=False),
        sa.Column("chord_name", sa.String(24), nullable=False),
        sa.Column("root_note", sa.String(3), nullable=False),
        sa.Column("chord_quality", sa.String(16), nullable=False),
        sa.Column("bass_note", sa.String(3)),
        sa.Column("start_time", sa.Float, nullable=False),
        sa.Column("end_time", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("inversion", sa.Integer),
        sa.Column("source", sa.String(12), nullable=False, server_default="detected"),
        sa.PrimaryKeyConstraint("id", name="pk_detected_chords"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE",
                                name="fk_detected_chords_analysis_id_analyses"),
        sa.CheckConstraint("end_time > start_time", name="ck_detected_chords_time_order"),
        sa.CheckConstraint("start_time >= 0", name="ck_detected_chords_start_nonneg"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_detected_chords_confidence_range"),
        sa.CheckConstraint("source IN ('detected', 'manual')", name="ck_detected_chords_source_valid"),
    )
    op.create_index("ix_detected_chords_analysis_id_start_time", "detected_chords", ["analysis_id", "start_time"])
    op.create_table(
        "detected_notes",
        sa.Column("id", UUID, nullable=False),
        sa.Column("analysis_id", UUID, nullable=False),
        sa.Column("pitch", sa.Integer, nullable=False),
        sa.Column("note_name", sa.String(3), nullable=False),
        sa.Column("octave", sa.Integer, nullable=False),
        sa.Column("start_time", sa.Float, nullable=False),
        sa.Column("end_time", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("estimated_hand", sa.String(8), nullable=False, server_default="unknown"),
        sa.PrimaryKeyConstraint("id", name="pk_detected_notes"),
        sa.ForeignKeyConstraint(["analysis_id"], ["analyses.id"], ondelete="CASCADE",
                                name="fk_detected_notes_analysis_id_analyses"),
        sa.CheckConstraint("pitch BETWEEN 0 AND 127", name="ck_detected_notes_pitch_range"),
        sa.CheckConstraint("end_time > start_time", name="ck_detected_notes_time_order"),
        sa.CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_detected_notes_confidence_range"),
        sa.CheckConstraint("estimated_hand IN ('left', 'right', 'unknown')", name="ck_detected_notes_hand_valid"),
    )
    op.create_index("ix_detected_notes_analysis_id_start_time", "detected_notes", ["analysis_id", "start_time"])
    op.create_table(
        "chord_voicings",
        sa.Column("id", UUID, nullable=False),
        sa.Column("detected_chord_id", UUID, nullable=False),
        sa.Column("left_hand_notes", pg.JSONB, nullable=False),
        sa.Column("right_hand_notes", pg.JSONB, nullable=False),
        sa.Column("voicing_type", sa.String(24), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_chord_voicings"),
        sa.ForeignKeyConstraint(["detected_chord_id"], ["detected_chords.id"], ondelete="CASCADE",
                                name="fk_chord_voicings_detected_chord_id_detected_chords"),
    )
    op.create_index("ix_chord_voicings_detected_chord_id", "chord_voicings", ["detected_chord_id"])


def downgrade() -> None:
    for t in ("chord_voicings", "detected_notes", "detected_chords", "analyses", "songs", "users"):
        op.drop_table(t)
