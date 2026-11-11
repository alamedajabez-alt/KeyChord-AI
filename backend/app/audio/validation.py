"""Upload validation helpers. Pure Python, no framework imports, so they are trivially testable."""
import unicodedata
from typing import BinaryIO

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac"}
MEDIA_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "m4a": "audio/mp4",
    "flac": "audio/flac",
}
HEAD_BYTES = 64  # enough to identify every supported container

_M4A_BRANDS = {b"M4A ", b"M4B ", b"mp42", b"mp41", b"isom", b"iso2", b"MSNV"}


def detect_format(head: bytes) -> str | None:
    """Identify the audio container from its leading bytes. Never trusts the filename or Content-Type."""
    if len(head) < 12:
        return None
    if head[:4] == b"RIFF" and head[8:12] == b"WAVE":
        return "wav"
    if head[:4] == b"fLaC":
        return "flac"
    if head[4:8] == b"ftyp" and head[8:12] in _M4A_BRANDS:
        return "m4a"
    if head[:3] == b"ID3":
        return "mp3"
    # Bare MPEG audio frame: 11 sync bits, then version != reserved, layer != reserved.
    if head[0] == 0xFF and (head[1] & 0xE0) == 0xE0 and (head[1] >> 3) & 3 != 1 and (head[1] >> 1) & 3 != 0:
        return "mp3"
    return None


def extension_of(filename: str) -> str:
    dot = filename.rfind(".")
    return filename[dot:].lower() if dot > 0 else ""


def sanitize_filename(name: str | None, max_len: int = 255) -> str:
    """Make a client-supplied filename safe to store and display. It is NEVER used as a filesystem path."""
    name = (name or "").replace("\\", "/").rsplit("/", 1)[-1]
    # Drop control and format characters (includes NUL and bidi overrides such as U+202E).
    name = "".join(c for c in name if not unicodedata.category(c).startswith("C"))
    name = " ".join(name.split()).strip(". ")
    if not name:
        return "untitled"
    if len(name) > max_len:
        dot = name.rfind(".")
        ext = name[dot:] if 0 < dot and len(name) - dot <= 8 else ""
        name = name[: max_len - len(ext)] + ext
    return name


class UploadTooLarge(Exception):
    pass


class LimitedReader:
    """Wraps a binary stream and raises UploadTooLarge as soon as more than `limit` bytes are read.

    It never reads more than limit + 1 bytes, so an oversized upload is cut off early instead of
    being copied to storage in full.
    """

    def __init__(self, raw: BinaryIO, limit: int):
        self._raw = raw
        self._limit = limit
        self.count = 0

    def read(self, size: int | None = -1) -> bytes:
        room = self._limit + 1 - self.count
        size = room if size is None or size < 0 else min(size, room)
        data = self._raw.read(size)
        self.count += len(data)
        if self.count > self._limit:
            raise UploadTooLarge
        return data
