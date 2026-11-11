"""Queue + worker-loop tests: real SQLite database, real spawned subprocesses."""
import threading
import time
import uuid
from datetime import timedelta

import pytest
import worker_pipelines as wp
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Analysis, DetectedChord, DetectedNote, Song, User
from app.worker import queue
from app.worker.loop import Worker, WorkerConfig


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


class FakeStorage:
    def __init__(self, present=True):
        self.present = present

    def exists(self, key):
        return self.present

    def local_path(self, key):
        return f"/fake/{key}"


@pytest.fixture
def Session():
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture
def song_id(Session):
    with Session() as db:
        user = User(id=uuid.uuid4(), name="U", email="u@example.com", password_hash="!")
        db.add(user)
        db.flush()
        song = Song(
            id=uuid.uuid4(), user_id=user.id, original_filename="a.wav", storage_path="songs/a/original.wav",
            duration=3.0, audio_format="wav", size_bytes=100,
        )
        db.add(song)
        db.commit()
        return song.id


def add_job(Session, song_id, *, status="queued", age=0, started_ago=None, attempts=0):
    """age: seconds since created (bigger = older). started_ago: seconds since the job was claimed."""
    now = queue.utcnow()
    with Session() as db:
        a = Analysis(
            song_id=song_id, status=status, progress=0.0, analysis_version="t",
            params={queue.ATTEMPTS_KEY: attempts} if attempts else {},
            created_at=now - timedelta(seconds=age),
            started_at=now - timedelta(seconds=started_ago) if started_ago is not None else None,
        )
        db.add(a)
        db.commit()
        return a.id


def row(Session, analysis_id) -> Analysis:
    with Session() as db:
        return db.get(Analysis, analysis_id)


def worker(Session, pipeline=wp.quick, storage=None, **cfg):
    cfg.setdefault("timeout_seconds", 30)
    return Worker(Session, storage or FakeStorage(), WorkerConfig(**cfg), pipeline=pipeline)


# ---------- queue ----------

def test_claim_takes_oldest_first_then_none(Session, song_id):
    newer = add_job(Session, song_id, age=10)
    older = add_job(Session, song_id, age=100)
    with Session() as db:
        first = queue.claim_next(db)
        second = queue.claim_next(db)
        third = queue.claim_next(db)
    assert (first.id, second.id, third) == (older, newer, None)


def test_claim_marks_running_and_counts_attempt(Session, song_id):
    job = add_job(Session, song_id)
    with Session() as db:
        claim = queue.claim_next(db)
    a = row(Session, job)
    assert a.status == "running" and a.started_at is not None and a.stage == "starting"
    assert claim.attempts == 1 and a.params[queue.ATTEMPTS_KEY] == 1
    assert claim.storage_key == "songs/a/original.wav"


def test_only_queued_jobs_are_claimed(Session, song_id):
    for status in ("running", "completed", "failed"):
        add_job(Session, song_id, status=status, started_ago=1 if status == "running" else None)
    with Session() as db:
        assert queue.claim_next(db) is None


def test_progress_is_clamped_below_one_until_completion(Session, song_id):
    job = add_job(Session, song_id)
    with Session() as db:
        claim = queue.claim_next(db)
        assert queue.update_progress(db, claim, "chroma", 5.0)
    assert row(Session, job).progress == pytest.approx(0.99)


def test_lease_blocks_writes_after_the_job_was_taken_over(Session, song_id):
    job = add_job(Session, song_id)
    with Session() as db:
        claim = queue.claim_next(db)
    with Session() as db:  # someone recovers and re-claims the job: a new started_at
        db.get(Analysis, job).started_at = queue.utcnow() + timedelta(seconds=5)
        db.commit()
    with Session() as db:
        assert queue.update_progress(db, claim, "x", 0.5) is False
        assert queue.fail(db, claim, "nope") is False
        assert queue.complete(db, claim, {"tempo": 1.0}) is False
    assert row(Session, job).status == "running"


def test_recover_stale(Session, song_id):
    stale = add_job(Session, song_id, status="running", started_ago=5000, attempts=1)
    exhausted = add_job(Session, song_id, status="running", started_ago=5000, attempts=3)
    fresh = add_job(Session, song_id, status="running", started_ago=10, attempts=1)
    queued = add_job(Session, song_id)
    with Session() as db:
        assert queue.recover_stale(db, older_than_seconds=1000, max_attempts=3) == (1, 1)
    assert row(Session, stale).status == "queued" and row(Session, stale).started_at is None
    assert row(Session, exhausted).status == "failed" and "kept failing" in row(Session, exhausted).error_message
    assert row(Session, fresh).status == "running"
    assert row(Session, queued).status == "queued"


# ---------- worker ----------

def test_empty_queue(Session):
    assert worker(Session).run_once() is False


def test_happy_path_persists_results(Session, song_id):
    job = add_job(Session, song_id)
    assert worker(Session).run_once() is True
    a = row(Session, job)
    assert (a.status, a.stage, a.progress) == ("completed", "done", 1.0)
    assert a.estimated_key == "C major" and a.tempo == 120.0 and a.completed_at is not None
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(DetectedChord)) == 2
        assert db.scalar(select(func.count()).select_from(DetectedNote)) == 1


def test_timeout_is_enforced(Session, song_id):
    job = add_job(Session, song_id)
    start = time.monotonic()
    worker(Session, pipeline=wp.slow, timeout_seconds=1.5).run_once()
    a = row(Session, job)
    assert a.status == "failed" and "timed out" in a.error_message
    assert time.monotonic() - start < 20


def test_pipeline_error_gives_a_generic_message(Session, song_id):
    job = add_job(Session, song_id)
    worker(Session, pipeline=wp.boom).run_once()
    a = row(Session, job)
    assert a.status == "failed" and a.error_message == "Analysis failed. Please try again."
    assert "secret" not in a.error_message and "/home" not in a.error_message


def test_child_crash_fails_the_job(Session, song_id):
    job = add_job(Session, song_id)
    worker(Session, pipeline=wp.crash).run_once()
    a = row(Session, job)
    assert a.status == "failed" and "unexpectedly" in a.error_message


def test_malformed_result_fails_and_rolls_back_cleanly(Session, song_id):
    job = add_job(Session, song_id)
    worker(Session, pipeline=wp.bad_result).run_once()
    a = row(Session, job)
    assert a.status == "failed" and "invalid" in a.error_message
    with Session() as db:
        assert db.scalar(select(func.count()).select_from(DetectedChord)) == 0


def test_missing_audio_file_fails_without_running_the_pipeline(Session, song_id):
    job = add_job(Session, song_id)
    worker(Session, pipeline=wp.slow, storage=FakeStorage(present=False)).run_once()
    a = row(Session, job)
    assert a.status == "failed" and "missing" in a.error_message


def test_shutdown_returns_the_job_to_the_queue_without_burning_an_attempt(Session, song_id):
    job = add_job(Session, song_id)
    stop = threading.Event()
    stop.set()
    worker(Session, pipeline=wp.slow).run_once(stop)
    a = row(Session, job)
    assert a.status == "queued" and a.started_at is None and a.params[queue.ATTEMPTS_KEY] == 0


def test_a_worker_that_lost_its_lease_stops_and_leaves_the_job_alone(Session, song_id):
    job = add_job(Session, song_id)
    t = threading.Thread(target=lambda: worker(Session, pipeline=wp.trickle).run_once(), daemon=True)
    t.start()
    deadline = time.monotonic() + 30
    while row(Session, job).stage in (None, "starting") and time.monotonic() < deadline:
        time.sleep(0.05)
    taken_over = queue.utcnow() + timedelta(seconds=30)
    with Session() as db:  # another worker "recovers" and re-claims it
        db.get(Analysis, job).started_at = taken_over
        db.commit()
    t.join(30)
    assert not t.is_alive()  # the child was killed instead of running its full 60 s
    a = row(Session, job)
    assert a.status == "running"  # untouched by the old worker


def test_run_forever_recovers_a_stale_job_then_processes_it(Session, song_id):
    job = add_job(Session, song_id, status="running", started_ago=99999, attempts=1)
    stop = threading.Event()
    w = worker(Session, poll_interval_seconds=0.1, stale_grace_seconds=0)
    t = threading.Thread(target=w.run_forever, args=(stop,), daemon=True)
    t.start()
    deadline = time.monotonic() + 60
    while row(Session, job).status != "completed" and time.monotonic() < deadline:
        time.sleep(0.1)
    stop.set()
    t.join(10)
    assert not t.is_alive()
    a = row(Session, job)
    assert a.status == "completed" and a.params[queue.ATTEMPTS_KEY] == 2  # original claim + the retry
