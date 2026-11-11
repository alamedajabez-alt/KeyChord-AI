"""Pipelines used by the worker tests. They must live in an importable module because the worker runs
them in a *spawned* child process."""
import os
import time


def quick(audio_path, params, progress):
    progress("chroma", 0.3)
    progress("chord_decoding", 0.8)
    return {
        "estimated_key": "C major",
        "key_confidence": 0.9,
        "alternative_keys": [{"key": "A minor", "score": 0.7}],
        "tempo": 120.0,
        "chords": [
            {"chord_name": "C", "root_note": "C", "chord_quality": "maj", "start_time": 0.0, "end_time": 1.0, "confidence": 0.9},
            {"chord_name": "G", "root_note": "G", "chord_quality": "maj", "start_time": 1.0, "end_time": 2.0, "confidence": 0.8},
        ],
        "notes": [
            {"pitch": 60, "note_name": "C", "octave": 4, "start_time": 0.0, "end_time": 0.5, "confidence": 0.9},
        ],
    }


def slow(audio_path, params, progress):
    progress("chroma", 0.2)
    time.sleep(120)


def trickle(audio_path, params, progress):
    """Keeps reporting progress (changing stage each time) so the worker keeps touching the database."""
    for i in range(300):
        progress(f"s{i}", min(i / 300, 0.9))
        time.sleep(0.2)


def boom(audio_path, params, progress):
    raise ValueError("secret detail at /home/someone/private/path")


def crash(audio_path, params, progress):
    os._exit(3)


def bad_result(audio_path, params, progress):
    return {"estimated_key": "C major", "chords": [{"chord_name": "C"}]}  # missing required fields
