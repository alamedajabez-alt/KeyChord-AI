import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import MaxBodySizeMiddleware
from app.api.routes import health, songs
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.seed import seed_dev_user

settings = get_settings()
configure_logging()
log = logging.getLogger("keychord")

MULTIPART_OVERHEAD_BYTES = 1024 * 1024  # boundaries + headers around the file part


@asynccontextmanager
async def lifespan(_: FastAPI):
    if not settings.auth_enabled:
        try:
            seed_dev_user()
        except Exception:  # noqa: BLE001 - the API must still boot if the DB isn't migrated yet
            log.warning("could not seed the dev user (has `alembic upgrade head` been run?)", exc_info=True)
    yield


app = FastAPI(
    title="KeyChord AI API",
    version="0.1.0",
    description="Chord and note transcription for keyboard players.",
    lifespan=lifespan,
)
# Order matters: the LAST middleware added is the OUTERMOST. The size guard is added first so
# CORS wraps it and its 413 responses still carry CORS headers (otherwise browsers hide the error).
app.add_middleware(
    MaxBodySizeMiddleware,
    path="/api/songs/upload",
    max_bytes=settings.max_upload_bytes + MULTIPART_OVERHEAD_BYTES,
    message=f"File is larger than {settings.max_upload_mb} MB.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Range", "Accept-Ranges", "Content-Length"],
)
app.include_router(health.router, prefix="/api")
app.include_router(songs.router, prefix="/api")
log.info("KeyChord AI API started (env=%s)", settings.env)
