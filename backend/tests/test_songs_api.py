"""End-to-end tests for upload / metadata / streaming against SQLite + a temp storage dir."""
import io
import struct
import uuid
import wave
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.middleware import MaxBodySizeMiddleware
from app.core.config import Settings, get_settings
from app.core.seed import DEV_USER_EMAIL, DEV_USER_ID, ensure_dev_user
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models import Song, User
from app.storage import get_storage
from app.storage.local import LocalStorage


@compiles(JSONB, "sqlite")  # the models use Postgres JSONB; SQLite stores it as JSON
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


def make_wav(seconds: float, rate: int = 8000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(1)
        w.setframerate(rate)
        w.writeframes(b"\x80" * int(seconds * rate))
    return buf.getvalue()


def files_on_disk(storage: LocalStorage):
    return [p for p in storage.root.rglob("*") if p.is_file()]


@pytest.fixture
def env(tmp_path):
    engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_db():
        db = Session()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    storage = LocalStorage(tmp_path / "storage")
    settings = Settings(max_upload_mb=1, max_duration_seconds=10, auth_enabled=False)
    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_settings] = lambda: settings
    yield SimpleNamespace(client=TestClient(app), storage=storage, Session=Session)
    app.dependency_overrides.clear()


def upload(env, data: bytes, name: str = "song.wav", content_type: str = "audio/wav"):
    return env.client.post("/api/songs/upload", files={"file": (name, data, content_type)})


# ---------- dev user ----------

def test_dev_user_seed_is_idempotent(env):
    with env.Session() as db:
        a = ensure_dev_user(db)
        db.commit()
        b = ensure_dev_user(db)
        db.commit()
        assert a.id == b.id == DEV_USER_ID
        assert db.scalar(select(func.count()).select_from(User)) == 1
        assert a.email == DEV_USER_EMAIL and a.password_hash == "!"


# ---------- upload ----------

def test_upload_ok(env):
    wav = make_wav(2)
    r = upload(env, wav, name="../../My Take.WAV")
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["original_filename"] == "My Take.WAV"  # path parts stripped
    assert body["audio_format"] == "wav"
    assert body["size_bytes"] == len(wav)
    assert body["duration"] == pytest.approx(2.0, abs=0.05)
    assert "storage_path" not in body
    assert env.storage.exists(f"songs/{body['id']}/original.wav")
    with env.Session() as db:
        assert db.get(Song, uuid.UUID(body["id"])).user_id == DEV_USER_ID


def test_rejects_unsupported_extension(env):
    r = upload(env, make_wav(1), name="notes.txt", content_type="text/plain")
    assert r.status_code == 415
    assert files_on_disk(env.storage) == []


def test_rejects_wrong_magic_bytes_even_with_audio_extension(env):
    r = upload(env, b"MZ\x90\x00" + b"\x00" * 200, name="totally-an-mp3.mp3", content_type="audio/mpeg")
    assert r.status_code == 415
    assert files_on_disk(env.storage) == []


def test_rejects_empty_file(env):
    r = upload(env, b"")
    assert r.status_code == 400


def test_corrupt_audio_gets_safe_error_and_leaves_nothing_behind(env):
    corrupt = b"RIFF" + struct.pack("<I", 100) + b"WAVE" + b"junkjunk" * 30  # right magic bytes, no real chunks
    r = upload(env, corrupt)
    assert r.status_code == 422
    assert "corrupt" in r.json()["detail"]
    assert "Traceback" not in r.text and "mutagen" not in r.text.lower()
    assert files_on_disk(env.storage) == []
    with env.Session() as db:
        assert db.scalar(select(func.count()).select_from(Song)) == 0


def test_duration_limit(env):
    r = upload(env, make_wav(11))  # limit is 10 s in this fixture
    assert r.status_code == 422
    assert "limit" in r.json()["detail"]
    assert files_on_disk(env.storage) == []


def test_size_cap_enforced_and_partial_file_removed(env):
    big = make_wav(1) + b"\x00" * (1024 * 1024 + 10)  # > 1 MB cap, still under the middleware allowance
    r = upload(env, big)
    assert r.status_code == 413
    assert "1 MB" in r.json()["detail"]
    assert files_on_disk(env.storage) == []


# ---------- metadata + ownership ----------

def test_get_song_and_ownership(env):
    song_id = upload(env, make_wav(1)).json()["id"]
    r = env.client.get(f"/api/songs/{song_id}")
    assert r.status_code == 200 and r.json()["id"] == song_id

    assert env.client.get(f"/api/songs/{uuid.uuid4()}").status_code == 404

    with env.Session() as db:  # a song that belongs to someone else
        other = User(id=uuid.uuid4(), name="Other", email="other@example.com", password_hash="!")
        db.add(other)
        db.flush()
        theirs = Song(
            id=uuid.uuid4(), user_id=other.id, original_filename="x.wav", storage_path="songs/x/original.wav",
            duration=1.0, audio_format="wav", size_bytes=10,
        )
        db.add(theirs)
        db.commit()
        theirs_id = theirs.id
    assert env.client.get(f"/api/songs/{theirs_id}").status_code == 404
    assert env.client.get(f"/api/songs/{theirs_id}/audio").status_code == 404  # same 404: existence isn't revealed


# ---------- streaming ----------

@pytest.fixture
def stored(env):
    wav = make_wav(3)
    song_id = upload(env, wav).json()["id"]
    return SimpleNamespace(url=f"/api/songs/{song_id}/audio", data=wav, size=len(wav))


def test_full_download(env, stored):
    r = env.client.get(stored.url)
    assert r.status_code == 200
    assert r.headers["accept-ranges"] == "bytes"
    assert r.headers["content-type"] == "audio/wav"
    assert r.content == stored.data


def test_range_slice(env, stored):
    r = env.client.get(stored.url, headers={"Range": "bytes=10-109"})
    assert r.status_code == 206
    assert r.headers["content-range"] == f"bytes 10-109/{stored.size}"
    assert r.headers["content-length"] == "100"
    assert r.content == stored.data[10:110]


def test_open_ended_and_suffix_ranges(env, stored):
    r = env.client.get(stored.url, headers={"Range": f"bytes={stored.size - 50}-"})
    assert r.status_code == 206 and r.content == stored.data[-50:]
    r = env.client.get(stored.url, headers={"Range": "bytes=-20"})
    assert r.status_code == 206 and r.content == stored.data[-20:]


def test_unsatisfiable_range(env, stored):
    r = env.client.get(stored.url, headers={"Range": f"bytes={stored.size}-"})
    assert r.status_code == 416
    assert r.headers["content-range"] == f"bytes */{stored.size}"


def test_stale_if_range_falls_back_to_full_body(env, stored):
    r = env.client.get(stored.url, headers={"Range": "bytes=0-9", "If-Range": '"stale"'})
    assert r.status_code == 200 and r.content == stored.data


def test_matching_if_range_keeps_the_range(env, stored):
    etag = env.client.head(stored.url).headers["etag"]
    r = env.client.get(stored.url, headers={"Range": "bytes=0-9", "If-Range": etag})
    assert r.status_code == 206 and len(r.content) == 10


def test_head_has_headers_and_no_body(env, stored):
    r = env.client.head(stored.url)
    assert r.status_code == 200
    assert r.headers["content-length"] == str(stored.size)
    assert r.content == b""


def test_missing_file_on_disk_is_a_clean_404(env, stored):
    for p in files_on_disk(env.storage):
        p.unlink()
    assert env.client.get(stored.url).status_code == 404


# ---------- body-size middleware ----------

def _guarded_app(limit: int) -> TestClient:
    guarded = FastAPI()
    guarded.add_middleware(MaxBodySizeMiddleware, path="/up", max_bytes=limit, message="too big")

    @guarded.post("/up")
    async def up(request: Request):
        return {"n": len(await request.body())}

    return TestClient(guarded)


def test_middleware_rejects_by_content_length():
    c = _guarded_app(1000)
    assert c.post("/up", content=b"x" * 500).status_code == 200
    r = c.post("/up", content=b"x" * 2000)
    assert r.status_code == 413 and r.json() == {"detail": "too big"}


def test_middleware_counts_chunked_bodies_without_content_length():
    c = _guarded_app(1000)

    def chunks():
        for _ in range(10):
            yield b"x" * 300

    r = c.post("/up", content=chunks())
    assert r.status_code == 413
