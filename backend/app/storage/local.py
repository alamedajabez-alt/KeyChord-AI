import shutil
from pathlib import Path
from typing import BinaryIO


class StorageKeyError(ValueError):
    pass


class LocalStorage:
    """Filesystem storage. Callers pass SERVER-GENERATED keys (e.g. 'songs/<uuid>/original.mp3');
    user-supplied filenames are never used as paths. Every key is still validated and
    resolved to prove it stays inside the storage root (defence against path traversal)."""

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _resolve(self, key: str) -> Path:
        if not key or key.startswith(("/", "\\")) or "\x00" in key:
            raise StorageKeyError(f"invalid storage key: {key!r}")
        path = (self.root / key).resolve()
        if not path.is_relative_to(self.root) or path == self.root:
            raise StorageKeyError(f"storage key escapes root: {key!r}")
        return path

    def save(self, key: str, stream: BinaryIO) -> int:
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".part")
        try:
            with open(tmp, "wb") as out:
                shutil.copyfileobj(stream, out, length=1024 * 1024)  # streamed, never fully in memory
            tmp.replace(path)  # atomic publish
        except BaseException:
            tmp.unlink(missing_ok=True)  # never leave a half-written file behind (size cap hit, disconnect, disk full)
            self._prune_empty_parent(path)
            raise
        return path.stat().st_size

    def open(self, key: str) -> BinaryIO:
        return open(self._resolve(key), "rb")

    def local_path(self, key: str) -> str:
        return str(self._resolve(key))

    def exists(self, key: str) -> bool:
        return self._resolve(key).is_file()

    def delete(self, key: str) -> None:
        path = self._resolve(key)
        path.unlink(missing_ok=True)
        self._prune_empty_parent(path)

    def _prune_empty_parent(self, path: Path) -> None:
        """Remove the per-song directory once it is empty. Never removes the storage root."""
        parent = path.parent
        if parent != self.root:
            try:
                parent.rmdir()
            except OSError:
                pass  # not empty, or already gone
