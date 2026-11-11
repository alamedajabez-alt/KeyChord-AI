import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SongOut(BaseModel):
    """Public view of a song. `storage_path` is an internal key and is never exposed."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    original_filename: str
    duration: float
    audio_format: str
    size_bytes: int
    created_at: datetime
