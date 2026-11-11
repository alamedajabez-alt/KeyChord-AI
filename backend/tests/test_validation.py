import io

import pytest

from app.audio.validation import (
    LimitedReader,
    UploadTooLarge,
    detect_format,
    extension_of,
    sanitize_filename,
)


@pytest.mark.parametrize(
    "head, expected",
    [
        (b"RIFF\x24\x08\x00\x00WAVEfmt ", "wav"),
        (b"fLaC\x00\x00\x00\x22" + b"\x00" * 8, "flac"),
        (b"\x00\x00\x00\x20ftypM4A \x00\x00\x00\x00", "m4a"),
        (b"\x00\x00\x00\x18ftypmp42\x00\x00\x00\x00", "m4a"),
        (b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 4, "mp3"),
        (b"\xff\xfb\x90\x64" + b"\x00" * 12, "mp3"),  # MPEG-1 Layer III frame
        (b"\xff\xf3\x90\x64" + b"\x00" * 12, "mp3"),  # MPEG-2 Layer III frame
    ],
)
def test_detects_supported_formats(head, expected):
    assert detect_format(head) == expected


@pytest.mark.parametrize(
    "head",
    [
        b"",
        b"short",
        b"MZ\x90\x00" + b"\x00" * 20,  # Windows executable
        b"%PDF-1.7\n%\xe2\xe3\xcf\xd3\n",
        b"\x89PNG\r\n\x1a\n" + b"\x00" * 8,
        b"RIFF\x24\x08\x00\x00AVI LIST",  # RIFF but not WAVE
        b"\xff\xe1\x90\x64" + b"\x00" * 12,  # sync bits but reserved layer (00)
        b"\xff\xea\x90\x64" + b"\x00" * 12,  # sync bits but reserved version (01)
        b"\x00\x00\x00\x20ftypqt  \x00\x00\x00\x00",  # QuickTime, not an audio brand
        b"hello world, I am definitely an mp3",
    ],
)
def test_rejects_everything_else(head):
    assert detect_format(head) is None


def test_extension_of():
    assert extension_of("Song.MP3") == ".mp3"
    assert extension_of("archive.tar.flac") == ".flac"
    assert extension_of("noext") == ""
    assert extension_of(".mp3") == ""  # a dotfile has no extension


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("My Song.mp3", "My Song.mp3"),
        ("../../etc/passwd.mp3", "passwd.mp3"),
        ("C:\\Users\\me\\song.wav", "song.wav"),
        ("evil\x00name.mp3", "evilname.mp3"),
        ("a\u202etxt.mp3", "atxt.mp3"),  # bidi override stripped
        ("  spaced   out .flac", "spaced out .flac"),
        ("", "untitled"),
        (None, "untitled"),
        ("...", "untitled"),
        ("/", "untitled"),
    ],
)
def test_sanitize_filename(raw, expected):
    assert sanitize_filename(raw) == expected


def test_sanitize_filename_truncates_but_keeps_extension():
    out = sanitize_filename("a" * 400 + ".mp3")
    assert len(out) == 255 and out.endswith(".mp3")


def test_limited_reader_allows_exactly_the_limit():
    r = LimitedReader(io.BytesIO(b"x" * 100), 100)
    total = 0
    while chunk := r.read(30):
        total += len(chunk)
    assert total == 100


def test_limited_reader_stops_one_byte_past_the_limit():
    src = io.BytesIO(b"x" * 1000)
    r = LimitedReader(src, 100)
    with pytest.raises(UploadTooLarge):
        while r.read(64):
            pass
    assert src.tell() == 101  # never read the rest of the oversized upload


def test_limited_reader_unbounded_read_is_still_capped():
    with pytest.raises(UploadTooLarge):
        LimitedReader(io.BytesIO(b"x" * 1000), 10).read()
