"""Seeded local dev user.

The MVP runs with auth disabled (KEYCHORD_AUTH_ENABLED=false) and a single fixed user owns
every song. The id is a constant so it is stable across databases, tests and restarts.
"""
import logging
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import User

log = logging.getLogger("keychord.seed")

DEV_USER_ID = uuid.UUID("00000000-0000-4000-8000-000000000001")
DEV_USER_EMAIL = "dev@keychord.local"
DEV_USER_NAME = "Dev User"
# Deliberately not a valid password hash: no password can ever verify against it,
# so this account cannot be logged into once real auth is switched on.
UNUSABLE_PASSWORD_HASH = "!"


def ensure_dev_user(db: Session) -> User:
    """Return the dev user, creating it if missing. Idempotent and safe under concurrent first requests.

    Does not commit: the caller's transaction (request-scoped `get_db`, or `seed_dev_user`) owns that.
    """
    user = db.get(User, DEV_USER_ID)
    if user is not None:
        return user
    try:
        with db.begin_nested():  # SAVEPOINT, so losing a race doesn't poison the outer transaction
            user = User(
                id=DEV_USER_ID,
                name=DEV_USER_NAME,
                email=DEV_USER_EMAIL,
                password_hash=UNUSABLE_PASSWORD_HASH,
            )
            db.add(user)
    except IntegrityError:
        user = db.get(User, DEV_USER_ID)
        if user is None:  # the conflict was something else (e.g. the email belongs to another user)
            raise
    return user


def seed_dev_user() -> None:
    """Best-effort seed used on app startup and by scripts/seed_dev_user.py."""
    from app.db.session import SessionLocal

    with SessionLocal() as db:
        ensure_dev_user(db)
        db.commit()
    log.info("dev user ready (%s)", DEV_USER_EMAIL)
