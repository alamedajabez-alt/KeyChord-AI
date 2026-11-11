import logging
import uuid
from typing import BinaryIO

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_song
from app.api.ranges import RangeNotSatisfiable, parse_range
from app.audio.probe import AudioProbeError, probe_duration
from app.audio.validation import (
    ALLOWED_EXTENSIONS,
    HEAD_BYTES,
    MEDIA_TYPES,
    LimitedReader,
    UploadTooLarge,
    detect_format,
    extension_of,
    sanitize_filename,
)
from app.core.config import Settings, get_settings
from app.db.session import get_db
from app.models import Song, User
from app.schemas.songs import SongOut
from app.storage import get_storage
from app.storage.base import StorageBackend

log = logging.getLogger("keychord.songs")
router = APIRouter(prefix="/songs", tags=["songs"])

STREAM_CHUNK = 64 * 1024


def _describe_limit(seconds: int) -> str:
    return f"{seconds // 60}-minute" if seconds % 60 == 0 else f"{seconds}-second"


def _discard(storage: StorageBackend, key: str) -> None:
    try:
        storage.delete(key)
    except Exception:  # noqa: BLE001 - cleanup must never mask the real error
        log.exception("could not clean up %s", key)


@router.post("/upload", response_model=SongOut, status_code=201)
def upload_song(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
    settings: Settings = Depends(get_settings),
) -> Song:
    """Validate, store and register an audio upload.

    Order matters: cheap checks first (name, magic bytes), then a size-capped streamed save,
    then decode-level checks (readable, duration). Anything that fails after the file is on
    disk deletes it again, so rejected uploads leave nothing behind.
    """
    name = sanitize_filename(file.filename)
    if extension_of(name) not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Unsupported file type. Use MP3, WAV, M4A or FLAC.")

    head = file.file.read(HEAD_BYTES)
    file.file.seek(0)
    if not head:
        raise HTTPException(status_code=400, detail="The uploaded file is empty.")
    fmt = detect_format(head)  # the CONTENT decides the format; the extension is only a first filter
    if fmt is None:
        raise HTTPException(status_code=415, detail="This doesn't look like a valid MP3, WAV, M4A or FLAC file.")

    song_id = uuid.uuid4()
    key = f"songs/{song_id}/original.{fmt}"  # server-generated; the client filename never touches the filesystem
    saved = False
    try:
        try:
            size = storage.save(key, LimitedReader(file.file, settings.max_upload_bytes))
            saved = True
        except UploadTooLarge:
            raise HTTPException(status_code=413, detail=f"File is larger than {settings.max_upload_mb} MB.")

        try:
            duration = probe_duration(storage.local_path(key), fmt)
        except AudioProbeError:
            raise HTTPException(
                status_code=422,
                detail="We couldn't read this audio file. It may be corrupt or incomplete.",
            )
        if duration > settings.max_duration_seconds:
            raise HTTPException(
                status_code=422,
                detail=f"Audio is longer than the {_describe_limit(settings.max_duration_seconds)} limit.",
            )

        song = Song(
            id=song_id,
            user_id=user.id,
            original_filename=name,
            storage_path=key,
            duration=duration,
            audio_format=fmt,
            size_bytes=size,
        )
        db.add(song)
        db.commit()  # commit explicitly: if it fails we must delete the file before returning
        db.refresh(song)
        return song
    except HTTPException:
        if saved:
            _discard(storage, key)
        raise
    except Exception:
        log.exception("upload failed")
        if saved:
            _discard(storage, key)
        raise HTTPException(status_code=500, detail="Something went wrong while saving your file. Please try again.")


@router.get("/{song_id}", response_model=SongOut)
def get_song(song: Song = Depends(get_owned_song)) -> Song:
    return song


@router.api_route("/{song_id}/audio", methods=["GET", "HEAD"])
def stream_audio(
    request: Request,
    song: Song = Depends(get_owned_song),
    db: Session = Depends(get_db),
    storage: StorageBackend = Depends(get_storage),
) -> Response:
    """Serve the original audio with HTTP Range support, so <audio> can seek without downloading everything."""
    key, size, fmt = song.storage_path, song.size_bytes, song.audio_format
    etag = f'"{song.id.hex}-{size}"'
    db.close()  # release the DB connection now; a stream can last minutes

    try:
        rng = parse_range(request.headers.get("range"), size)
    except RangeNotSatisfiable:
        raise HTTPException(status_code=416, detail="Requested range not satisfiable.", headers={"Content-Range": f"bytes */{size}"})
    if_range = request.headers.get("if-range")
    if rng is not None and if_range is not None and if_range.strip() != etag:
        rng = None  # the client's cached copy is stale: send the whole file instead of a mismatched slice

    if rng is None:
        status, start, end = 200, 0, size - 1
    else:
        status, (start, end) = 206, rng
    length = end - start + 1

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(length),
        "ETag": etag,
        "Cache-Control": "private, max-age=3600",
        "X-Content-Type-Options": "nosniff",
    }
    if status == 206:
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    media_type = MEDIA_TYPES.get(fmt, "application/octet-stream")

    if request.method == "HEAD":
        return Response(status_code=status, headers=headers, media_type=media_type)

    try:
        handle = storage.open(key)
    except FileNotFoundError:
        log.error("audio file missing for song %s (%s)", song.id, key)
        raise HTTPException(status_code=404, detail="The audio file for this song is missing.")

    def iter_range(f: BinaryIO = handle):
        try:
            f.seek(start)
            remaining = length
            while remaining > 0:
                chunk = f.read(min(STREAM_CHUNK, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                yield chunk
        finally:
            f.close()

    return StreamingResponse(iter_range(), status_code=status, headers=headers, media_type=media_type)
