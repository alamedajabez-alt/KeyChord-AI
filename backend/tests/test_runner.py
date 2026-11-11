import time

import worker_pipelines as wp

from app.worker.runner import run_in_subprocess

NOOP = lambda stage, fraction: True  # noqa: E731


def run(target, timeout=30, **kw):
    kw.setdefault("on_progress", NOOP)
    return run_in_subprocess(target, ("/x.wav", {}), timeout=timeout, **kw)


def test_ok_returns_result_and_reports_progress():
    seen = []
    out = run(wp.quick, on_progress=lambda s, f: seen.append((s, f)) or True)
    assert out.kind == "ok" and out.result["tempo"] == 120.0
    assert seen == [("chroma", 0.3), ("chord_decoding", 0.8)]


def test_timeout_kills_the_child():
    start = time.monotonic()
    out = run(wp.slow, timeout=1.5)
    assert out.kind == "timeout"
    assert time.monotonic() - start < 15  # the child sleeps for 120 s; it was killed, not waited for


def test_exception_in_child_is_reported_with_traceback():
    out = run(wp.boom)
    assert out.kind == "error" and "ValueError" in out.detail


def test_child_that_dies_is_reported_as_crashed():
    out = run(wp.crash)
    assert out.kind == "crashed" and out.exitcode == 3


def test_shutdown_request_aborts_quickly():
    start = time.monotonic()
    out = run(wp.slow, should_abort=lambda: True)
    assert out.kind == "aborted" and time.monotonic() - start < 10


def test_on_progress_false_abandons_the_job():
    out = run(wp.trickle, on_progress=lambda s, f: False)
    assert out.kind == "aborted"
