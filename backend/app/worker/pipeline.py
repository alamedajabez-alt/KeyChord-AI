"""The analysis pipeline the worker runs in a child process.

Contract (what `run_analysis` must follow so the worker can drive any implementation):
  - Called as run_analysis(audio_path, params, progress) in a SPAWNED subprocess, so it must be a
    top-level, importable function and import heavy libraries (librosa, ...) inside the function.
  - Call progress(stage, fraction) as it goes: stage is a short label (<= 48 chars), fraction is 0..1.
  - Return a plain, picklable dict:
        {"estimated_key": str|None, "key_confidence": float|None, "alternative_keys": list|None,
         "tempo": float|None,
         "chords": [{"chord_name","root_note","chord_quality","bass_note","start_time","end_time","confidence","inversion"}],
         "notes":  [{"pitch","note_name","octave","start_time","end_time","confidence","estimated_hand"}]}
  - Raise on failure. The traceback is logged server-side; users only ever see a generic message.
"""
from collections.abc import Callable
from typing import Any

Progress = Callable[[str, float], None]


def run_analysis(audio_path: str, params: dict[str, Any], progress: Progress) -> dict[str, Any]:
    # Deliberately not faked: returning empty "completed" analyses would look like real results.
    raise NotImplementedError("The analysis pipeline (chroma, key, chord decoding) is not implemented yet.")
