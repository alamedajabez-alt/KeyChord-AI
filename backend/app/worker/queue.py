"""Job queue backed by the `analyses` table (that is what ix_analyses_status_created_at is for).

State machine:   queued --claim--> running --> completed | failed
                    ^                 |
                    +--- requeue -----+   (stale recovery, or clean shutdown)

Concurrency: claiming uses SELECT ... FOR UPDATE SKIP LOCKED, so any number of workers can poll the
same table and never take the same job. Every write after the claim is guarded by a "lease": the row
must still be `running` AND carry the exact `started_at` this worker stamped when it claimed it. If
the job was recovered and re-claimed meanwhile, the old worker's writes match nothing and it stops.

No heartbeat column is needed: the worker kills its own job at the timeout, so a job still `running`
past timeout + grace can only belong to a dead worker.

Functions take a Session and commit themselves. Nothing here holds a transaction open while a job runs.
"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session

from app.models import Analysis, DetectedChord, DetectedNote, Song

ANALYSIS_VERSION = "0.1.0"
ATTEMPTS_KEY = "_attempts"  # stored inside Analysis.params (no extra column / migration)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Claim:
    """A worker's lease on one job."""

    id: uuid.UUID
    song_id: uuid.UUID
    storage_key: str
    params: dict[str, Any]
    started_at: datetime
    attempts: int


def enqueue_analysis(db: Session, song_id: uuid.UUID, params: dict[str, Any] | None = None) -> Analysis:
    analysis = Analysis(
        song_id=song_id, status="queued", progress=0.0, analysis_version=ANALYSIS_VERSION, params=params or {}
    )
    db.add(analysis)
    db.commit()
    return analysis


def claim_next(db: Session) -> Claim | None:
    """Atomically take the oldest queued job, or return None."""
    analysis = db.scalars(
        select(Analysis)
        .where(Analysis.status == "queued")
        .order_by(Analysis.created_at, Analysis.id)
        .limit(1)
        .with_for_update(skip_locked=True)
    ).first()
    if analysis is None:
        db.rollback()
        return None
    song = db.get(Song, analysis.song_id)
    attempts = int((analysis.params or {}).get(ATTEMPTS_KEY, 0)) + 1
    params = {**(analysis.params or {}), ATTEMPTS_KEY: attempts}
    now = utcnow()
    analysis.status = "running"
    analysis.started_at = now
    analysis.stage = "starting"
    analysis.progress = 0.0
    analysis.error_message = None
    analysis.params = params  # reassigned, not mutated, so SQLAlchemy sees the JSONB change
    claim = Claim(analysis.id, analysis.song_id, song.storage_path, params, now, attempts)
    db.commit()
    return claim


def _leased(claim: Claim):
    return (Analysis.id == claim.id, Analysis.status == "running", Analysis.started_at == claim.started_at)


def _guarded_update(db: Session, claim: Claim, **values: Any) -> bool:
    result = db.execute(
        update(Analysis).where(*_leased(claim)).values(**values).execution_options(synchronize_session=False)
    )
    db.commit()
    return result.rowcount == 1


def update_progress(db: Session, claim: Claim, stage: str, fraction: float) -> bool:
    """Record progress. False means the lease is gone and the worker must stop working on this job."""
    return _guarded_update(db, claim, stage=stage[:48], progress=min(max(fraction, 0.0), 0.99))


def fail(db: Session, claim: Claim, message: str) -> bool:
    return _guarded_update(db, claim, status="failed", stage=None, error_message=message[:1000])


def release(db: Session, claim: Claim) -> bool:
    """Put the job back on the queue (clean shutdown). It doesn't count as a failed attempt."""
    params = {**claim.params, ATTEMPTS_KEY: max(claim.attempts - 1, 0)}
    return _guarded_update(db, claim, status="queued", stage=None, progress=0.0, started_at=None, params=params)


def complete(db: Session, claim: Claim, result: dict[str, Any]) -> bool:
    """Store the results and mark the job completed, in ONE transaction. Raises (after rolling back)
    if the result is malformed; the caller then marks the job failed."""
    try:
        analysis = db.scalar(select(Analysis).where(*_leased(claim)).with_for_update())
        if analysis is None:
            db.rollback()
            return False
        analysis.estimated_key = result.get("estimated_key")
        analysis.key_confidence = result.get("key_confidence")
        analysis.alternative_keys = result.get("alternative_keys")
        analysis.tempo = result.get("tempo")
        for c in result.get("chords", []):
            db.add(
                DetectedChord(
                    analysis_id=analysis.id,
                    chord_name=c["chord_name"],
                    root_note=c["root_note"],
                    chord_quality=c["chord_quality"],
                    bass_note=c.get("bass_note"),
                    start_time=c["start_time"],
                    end_time=c["end_time"],
                    confidence=c["confidence"],
                    inversion=c.get("inversion"),
                    source="detected",
                )
            )
        for n in result.get("notes", []):
            db.add(
                DetectedNote(
                    analysis_id=analysis.id,
                    pitch=n["pitch"],
                    note_name=n["note_name"],
                    octave=n["octave"],
                    start_time=n["start_time"],
                    end_time=n["end_time"],
                    confidence=n["confidence"],
                    estimated_hand=n.get("estimated_hand", "unknown"),
                )
            )
        analysis.status = "completed"
        analysis.stage = "done"
        analysis.progress = 1.0
        analysis.completed_at = utcnow()
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise


def recover_stale(db: Session, *, older_than_seconds: float, max_attempts: int) -> tuple[int, int]:
    """Recover jobs orphaned by a dead worker. Returns (requeued, failed).

    A `running` job older than `older_than_seconds` (timeout + grace) can't belong to a live worker.
    It goes back on the queue, unless it has already used `max_attempts` claims. That cap stops a
    poison job (one that OOM-kills or hangs its worker every time) from looping forever.
    """
    cutoff = utcnow() - timedelta(seconds=older_than_seconds)
    rows = db.scalars(
        select(Analysis)
        .where(Analysis.status == "running", or_(Analysis.started_at.is_(None), Analysis.started_at < cutoff))
        .with_for_update(skip_locked=True)
    ).all()
    requeued = failed = 0
    for a in rows:
        attempts = int((a.params or {}).get(ATTEMPTS_KEY, 0))
        a.started_at = None
        a.stage = None
        if attempts >= max_attempts:
            a.status = "failed"
            a.error_message = "Analysis kept failing and was stopped. Please try uploading again."
            failed += 1
        else:
            a.status = "queued"
            a.progress = 0.0
            requeued += 1
    db.commit()
    return requeued, failed
