import io

import pytest

from app.storage.local import LocalStorage, StorageKeyError


def test_save_and_read_roundtrip(tmp_path):
    s = LocalStorage(tmp_path)
    size = s.save("songs/abc/original.wav", io.BytesIO(b"hello"))
    assert size == 5 and s.exists("songs/abc/original.wav")
    assert s.open("songs/abc/original.wav").read() == b"hello"


@pytest.mark.parametrize("bad", ["../evil", "songs/../../evil", "/etc/passwd", "", "a\x00b", ".", "songs/.."])
def test_path_traversal_rejected(tmp_path, bad):
    with pytest.raises(StorageKeyError):
        LocalStorage(tmp_path).save(bad, io.BytesIO(b"x"))


def test_delete_is_idempotent(tmp_path):
    s = LocalStorage(tmp_path)
    s.save("k/a.bin", io.BytesIO(b"1"))
    s.delete("k/a.bin")
    s.delete("k/a.bin")
    assert not s.exists("k/a.bin")
