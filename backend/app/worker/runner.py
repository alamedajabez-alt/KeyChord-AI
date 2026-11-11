"""Run one job in a killable child process. Standard library only, so the spawned child starts fast
and never touches the database.

Why a subprocess: a timeout has to be ENFORCED. Threads cannot be killed, and long numpy/librosa
calls never check for cancellation, so the only reliable way to stop a runaway analysis is to kill the
process. "spawn" (not "fork") avoids inheriting the parent's DB connections.
"""
import multiprocessing as mp
import time
import traceback
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class Outcome:
    kind: str  # "ok" | "error" | "crashed" | "timeout" | "aborted"
    result: Any = None  # kind == "ok"
    detail: str = ""  # kind == "error": the child's traceback (log it; never show it to users)
    exitcode: int | None = None  # kind == "crashed"


def _child_main(conn, target: Callable, args: tuple) -> None:
    try:
        def progress(stage: str, fraction: float) -> None:
            conn.send(("progress", str(stage), float(fraction)))

        conn.send(("result", target(*args, progress)))
    except BaseException:  # noqa: BLE001 - report everything, including SystemExit/KeyboardInterrupt
        try:
            conn.send(("error", traceback.format_exc()))
        except Exception:  # noqa: BLE001 - pipe already broken
            pass
    finally:
        conn.close()


def _stop(proc) -> None:
    if proc.is_alive():
        proc.terminate()  # SIGTERM first
        proc.join(5)
    if proc.is_alive():
        proc.kill()  # then SIGKILL; a process stuck in C code ignores SIGTERM handlers
        proc.join()


def run_in_subprocess(
    target: Callable,
    args: tuple,
    *,
    timeout: float,
    on_progress: Callable[[str, float], bool],
    should_abort: Callable[[], bool] = lambda: False,
    poll: float = 0.2,
) -> Outcome:
    """Run target(*args, progress) in a child. `on_progress` returns False to abandon the job
    (e.g. the lease was lost). `should_abort` is polled for shutdown requests. The child is always
    reaped before this returns."""
    ctx = mp.get_context("spawn")
    receiver, sender = ctx.Pipe(duplex=False)
    proc = ctx.Process(target=_child_main, args=(sender, target, args), daemon=True)
    proc.start()
    sender.close()  # parent's copy; without this a dead child would never produce EOF
    deadline = time.monotonic() + timeout
    try:
        while True:
            if should_abort():
                return Outcome("aborted")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return Outcome("timeout")
            if receiver.poll(min(poll, remaining)):
                try:
                    message = receiver.recv()
                except (EOFError, OSError):
                    break  # child died without reporting
                if message[0] == "progress":
                    if not on_progress(message[1], message[2]):
                        return Outcome("aborted")
                elif message[0] == "result":
                    return Outcome("ok", result=message[1])
                else:
                    return Outcome("error", detail=message[1])
            elif not proc.is_alive():
                if receiver.poll(0):  # data that landed just as the child exited
                    continue
                break
        proc.join(1)
        return Outcome("crashed", exitcode=proc.exitcode)
    finally:
        _stop(proc)
        receiver.close()
