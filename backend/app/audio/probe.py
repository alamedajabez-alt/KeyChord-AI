"""Read audio metadata (duration) from a stored file."""
import math

from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4
from mutagen.wave import WAVE

_LOADERS = {"mp3": MP3, "wav": WAVE, "flac": FLAC, "m4a": MP4}


class AudioProbeError(Exception):
    """The file could not be parsed as the audio format it claims to be."""


def probe_duration(path: str, fmt: str) -> float:
    """Return the duration in seconds. Raises AudioProbeError for corrupt, truncated or empty audio."""
    loader = _LOADERS.get(fmt)
    if loader is None:
        raise AudioProbeError(f"unsupported format {fmt!r}")
    try:
        length = float(loader(path).info.length)
    except Exception as exc:  # noqa: BLE001 - mutagen surfaces corruption as many types (MutagenError, struct.error, EOFError...)
        raise AudioProbeError("unreadable audio") from exc
    if not math.isfinite(length) or length <= 0:
        raise AudioProbeError("no audio data")
    return length
