from app.core.config import get_settings
from app.storage.base import StorageBackend
from app.storage.local import LocalStorage


def get_storage() -> StorageBackend:
    s = get_settings()
    if s.storage_backend == "local":
        return LocalStorage(s.storage_root)
    raise NotImplementedError(f"storage backend {s.storage_backend!r} not implemented yet")
