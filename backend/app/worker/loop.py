"""The worker loop: recover stale jobs, claim, run in a killable subprocess, report progress, finish."""
import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from app.worker import queue
from app.worker.pipeline import run_analysis
from app.worker.runner import run_in_subprocess

log = logging.getLogger("keychord.worker")

PROGRESS_MIN_INTERVAL = 0.5  # seconds between DB progress writes
PROGRESS_MIN_DELTA = 0.01
MAX_BACKOFF = 30.0


class _Storage(Protocol):
    def exists(self, key: str) -> bool: ...
    def local_path(self, key: str) -> str: ...


@dataclass(frozen=True)
class WorkerConfig:
    timeout_seconds: float
    poll_interval_seconds: float = 2.0
    stale_grace_seconds: float = 120.0
    max_attempts: int = 3
    sweep_interval_seconds: float = 60.0

    @classmethod
    def from_settings(cls, s: Any) -> "WorkerConfig":
        return cls(
            timeout_seconds=s.analysis_timeout_seconds,
            poll_interval_seconds=s.worker_poll_interval_seconds,
            stale_grace_seconds=s.worker_stale_grace_seconds,
            max_attempts=s.worker_max_attempts,
        )


def _duration(seconds: float) -> str:
    return f"{seconds / 60:g} minutes" if seconds >= 60 else f"{seconds:g} seconds"


class Worker:
    def __init__(
        self,
        session_factory: Callable[[], Any],
        storage: _Storage,
        config: WorkerConfig,
        pipeline: Callable[..., dict] = run_analysis,
    ):
        self.session_factory = session_factory
        self.storage = storage
        self.config = config
        self.pipeline = pipeline  # must be importable at module top level (it runs in a spawned child)

    def _db(self, fn: Callable[[Any], Any]) -> Any:
        with self.session_factory() as db:
            return fn(db)

    # ---------- public ----------

    def recover_stale(self) -> None:
        older_than = self.config.timeout_seconds + self.config.stale_grace_seconds
        requeued, failed = self._db(
            lambda db: queue.recover_stale(db, older_than_seconds=older_than, max_attempts=self.config.max_attempts)
        )
        if requeued or failed:
            log.warning("stale-job recovery: %d requeued, %d failed", requeued, failed)

    def run_once(self, stop: threading.Event | None = None) -> bool:
        """Claim and process at most one job. Returns True if a job was claimed."""
        stop = stop or threading.Event()
        claim = self._db(queue.claim_next)
        if claim is None:
            return False
        log.info("claimed analysis %s (attempt %d)", claim.id, claim.attempts)
        try:
            self._process(claim, stop)
        except Exception:
            # Anything unexpected must not leave the job `running` until the stale sweep finds it.
            log.exception("unexpected error while processing %s", claim.id)
            self._safely(lambda db: queue.fail(db, claim, "Analysis failed. Please try again."))
        return True

    def run_forever(self, stop: threading.Event) -> None:
        log.info("worker started (timeout=%ss, poll=%ss)", self.config.timeout_seconds, self.config.poll_interval_seconds)
        backoff = self.config.poll_interval_seconds
        last_sweep = float("-inf")  # sweep immediately on startup
        while not stop.is_set():
            try:
                if time.monotonic() - last_sweep >= self.config.sweep_interval_seconds:
                    self.recover_stale()
                    last_sweep = time.monotonic()
                worked = self.run_once(stop)
                backoff = self.config.poll_interval_seconds
                if not worked:
                    stop.wait(self.config.poll_interval_seconds)
            except Exception:  # e.g. the database went away: wait, back off, keep the worker alive
                log.exception("worker loop error; retrying in %.0fs", backoff)
                stop.wait(backoff)
                backoff = min(backoff * 2, MAX_BACKOFF)
        log.info("worker stopped")

    # ---------- internals ----------

    def _safely(self, fn: Callable[[Any], Any]) -> None:
        try:
            self._db(fn)
        except Exception:
            log.exception("could not record job state; the stale-job sweep will recover it")

    def _process(self, claim: queue.Claim, stop: threading.Event) -> None:
        if not self.storage.exists(claim.storage_key):
            log.error("audio file missing for analysis %s (%s)", claim.id, claim.storage_key)
            self._safely(lambda db: queue.fail(db, claim, "The audio file for this song is missing."))
            return

        lost = False
        last = {"t": 0.0, "p": 0.0, "stage": "starting"}

        def on_progress(stage: str, fraction: float) -> bool:
            nonlocal lost
            fraction = max(fraction, last["p"])  # progress never goes backwards
            now = time.monotonic()
            if stage == last["stage"] and (
                now - last["t"] < PROGRESS_MIN_INTERVAL or fraction - last["p"] < PROGRESS_MIN_DELTA
            ):
                return True
            try:
                if not self._db(lambda db: queue.update_progress(db, claim, stage, fraction)):
                    lost = True
                    return False
            except Exception:
                log.warning("progress update failed for %s", claim.id, exc_info=True)
                return True  # a missed tick is harmless; don't kill the job for it
            last.update(t=now, p=fraction, stage=stage)
            return True

        outcome = run_in_subprocess(
            self.pipeline,
            (self.storage.local_path(claim.storage_key), dict(claim.params)),
            timeout=self.config.timeout_seconds,
            on_progress=on_progress,
            should_abort=stop.is_set,
        )

        if outcome.kind == "ok":
            try:
                if not self._db(lambda db: queue.complete(db, claim, outcome.result)):
                    log.warning("lease lost before completing %s; discarding result", claim.id)
                else:
                    log.info("analysis %s completed", claim.id)
            except Exception:
                log.exception("invalid analysis result for %s", claim.id)
                self._safely(lambda db: queue.fail(db, claim, "Analysis produced invalid results."))
        elif outcome.kind == "timeout":
            log.error("analysis %s exceeded %ss; child killed", claim.id, self.config.timeout_seconds)
            msg = f"Analysis timed out after {_duration(self.config.timeout_seconds)}."
            self._safely(lambda db: queue.fail(db, claim, msg))
        elif outcome.kind == "crashed":
            log.error("analysis %s: child died with exit code %s", claim.id, outcome.exitcode)
            self._safely(lambda db: queue.fail(db, claim, "Analysis stopped unexpectedly. Please try again."))
        elif outcome.kind == "error":
            log.error("analysis %s failed in the pipeline:\n%s", claim.id, outcome.detail)
            self._safely(lambda db: queue.fail(db, claim, "Analysis failed. Please try again."))
        elif lost:
            log.warning("lease lost for %s (recovered by another worker); abandoning", claim.id)
        else:  # shutdown requested mid-job
            log.info("shutdown: returning analysis %s to the queue", claim.id)
            self._safely(lambda db: queue.release(db, claim))
