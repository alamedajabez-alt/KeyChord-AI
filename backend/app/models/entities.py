"""ORM models. Mirrors the spec; extra columns are marked (+)."""
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

ANALYSIS_STATUSES = ("queued", "running", "completed", "failed")
CHORD_SOURCES = ("detected", "manual")
HANDS = ("left", "right", "unknown")


def _uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(primary_key=True, default=uuid.uuid4)


def _created() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = _created()
    songs: Mapped[list["Song"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Song(Base):
    __tablename__ = "songs"
    id: Mapped[uuid.UUID] = _uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)  # storage KEY, never a raw FS path
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    audio_format: Mapped[str] = mapped_column(String(16), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)  # (+)
    created_at: Mapped[datetime] = _created()
    user: Mapped[User] = relationship(back_populates="songs")
    analyses: Mapped[list["Analysis"]] = relationship(back_populates="song", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("duration > 0", name="duration_positive"),
        Index("ix_songs_user_id_created_at", "user_id", "created_at"),
    )


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[uuid.UUID] = _uuid_pk()
    song_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("songs.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued")
    stage: Mapped[str | None] = mapped_column(String(48))  # (+) e.g. "chroma", "chord_decoding"
    progress: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)  # (+) 0..1
    error_message: Mapped[str | None] = mapped_column(Text)  # (+)
    estimated_key: Mapped[str | None] = mapped_column(String(16))
    key_confidence: Mapped[float | None] = mapped_column(Float)  # (+)
    alternative_keys: Mapped[list | None] = mapped_column(JSONB)  # (+) [{"key": "...", "score": 0.0}]
    tempo: Mapped[float | None] = mapped_column(Float)
    analysis_version: Mapped[str] = mapped_column(String(32), nullable=False)
    params: Mapped[dict | None] = mapped_column(JSONB)  # (+) options used (e.g. use_separation)
    created_at: Mapped[datetime] = _created()
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))  # (+) job lock time
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    song: Mapped[Song] = relationship(back_populates="analyses")
    chords: Mapped[list["DetectedChord"]] = relationship(
        back_populates="analysis", cascade="all, delete-orphan", order_by="DetectedChord.start_time")
    notes: Mapped[list["DetectedNote"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint(f"status IN {ANALYSIS_STATUSES}", name="status_valid"),
        CheckConstraint("progress >= 0 AND progress <= 1", name="progress_range"),
        Index("ix_analyses_song_id", "song_id"),
        Index("ix_analyses_status_created_at", "status", "created_at"),  # worker polling
    )


class DetectedChord(Base):
    __tablename__ = "detected_chords"
    id: Mapped[uuid.UUID] = _uuid_pk()
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    chord_name: Mapped[str] = mapped_column(String(24), nullable=False)
    root_note: Mapped[str] = mapped_column(String(3), nullable=False)
    chord_quality: Mapped[str] = mapped_column(String(16), nullable=False)
    bass_note: Mapped[str | None] = mapped_column(String(3))  # (+) slash-chord bass
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    inversion: Mapped[int | None] = mapped_column(Integer)  # 0 root, 1 first, 2 second, 3 third; NULL = unknown
    source: Mapped[str] = mapped_column(String(12), nullable=False, default="detected")  # (+) manual edits
    analysis: Mapped[Analysis] = relationship(back_populates="chords")
    voicings: Mapped[list["ChordVoicing"]] = relationship(back_populates="chord", cascade="all, delete-orphan")
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="time_order"),
        CheckConstraint("start_time >= 0", name="start_nonneg"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        CheckConstraint(f"source IN {CHORD_SOURCES}", name="source_valid"),
        Index("ix_detected_chords_analysis_id_start_time", "analysis_id", "start_time"),
    )


class DetectedNote(Base):
    __tablename__ = "detected_notes"
    id: Mapped[uuid.UUID] = _uuid_pk()
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    pitch: Mapped[int] = mapped_column(Integer, nullable=False)  # MIDI number
    note_name: Mapped[str] = mapped_column(String(3), nullable=False)
    octave: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_hand: Mapped[str] = mapped_column(String(8), nullable=False, default="unknown")  # an ESTIMATE
    analysis: Mapped[Analysis] = relationship(back_populates="notes")
    __table_args__ = (
        CheckConstraint("pitch BETWEEN 0 AND 127", name="pitch_range"),
        CheckConstraint("end_time > start_time", name="time_order"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="confidence_range"),
        CheckConstraint(f"estimated_hand IN {HANDS}", name="hand_valid"),
        Index("ix_detected_notes_analysis_id_start_time", "analysis_id", "start_time"),
    )


class ChordVoicing(Base):
    """A SUGGESTED playable voicing. Never a verified transcription of the original performance."""
    __tablename__ = "chord_voicings"
    id: Mapped[uuid.UUID] = _uuid_pk()
    detected_chord_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("detected_chords.id", ondelete="CASCADE"), nullable=False)
    left_hand_notes: Mapped[list[str]] = mapped_column(JSONB, nullable=False)   # ["C3","G3"]
    right_hand_notes: Mapped[list[str]] = mapped_column(JSONB, nullable=False)  # ["C4","E4","G4"]
    voicing_type: Mapped[str] = mapped_column(String(24), nullable=False)  # "suggested_basic" | "user_edited" | ...
    chord: Mapped[DetectedChord] = relationship(back_populates="voicings")
    __table_args__ = (Index("ix_chord_voicings_detected_chord_id", "detected_chord_id"),)
