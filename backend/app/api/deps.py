"""Shared FastAPI dependencies: current user and the ownership check."""
import uuid

from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.seed import ensure_dev_user
from app.db.session import get_db
from app.models import Song, User


def get_current_user(db: Session = Depends(get_db)) -> User:
    """The user making the request.

    MVP: auth is off, so this is the seeded dev user. When auth is switched on this must be
    replaced with real token verification. Until then it fails closed rather than silently
    handing every caller the dev user's data.
    """
    if get_settings().auth_enabled:
        raise HTTPException(status_code=501, detail="Authentication is not implemented yet.")
    return ensure_dev_user(db)


def get_owned_song(
    song_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Song:
    """Load a song only if it belongs to the current user.

    Ownership is part of the query, so another user's row is never loaded. A missing song and
    someone else's song produce the same 404, so ids can't be probed for existence.
    """
    song = db.scalar(select(Song).where(Song.id == song_id, Song.user_id == user.id))
    if song is None:
        raise HTTPException(status_code=404, detail="Song not found.")
    return song
