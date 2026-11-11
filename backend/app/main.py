import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging()
log = logging.getLogger("keychord")

app = FastAPI(
    title="KeyChord AI API",
    version="0.1.0",
    description="Chord and note transcription for keyboard players.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix="/api")
log.info("KeyChord AI API started (env=%s)", settings.env)
