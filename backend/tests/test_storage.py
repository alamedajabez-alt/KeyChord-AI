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


def test_failed_save_leaves_no_partial_file_or_empty_dir(tmp_path):
    class Boom(io.RawIOBase):
        def readinto(self, b):
            raise RuntimeError("client went away")

    s = LocalStorage(tmp_path)
    with pytest.raises(RuntimeError):
        s.save("songs/xyz/original.wav", Boom())
    assert not s.exists("songs/xyz/original.wav")
    assert not (tmp_path / "songs" / "xyz").exists()


def test_delete_prunes_empty_song_dir_but_not_root(tmp_path):
    s = LocalStorage(tmp_path)
    s.save("songs/abc/original.wav", io.BytesIO(b"1"))
    s.delete("songs/abc/original.wav")
    assert not (tmp_path / "songs" / "abc").exists()
    assert tmp_path.exists()
