import pytest

from app.api.ranges import RangeNotSatisfiable, parse_range

SIZE = 1000


@pytest.mark.parametrize(
    "header, expected",
    [
        (None, None),
        ("", None),
        ("bytes=0-99", (0, 99)),
        ("bytes=500-", (500, 999)),
        ("bytes=0-", (0, 999)),
        ("bytes=-100", (900, 999)),
        ("bytes=-5000", (0, 999)),  # suffix longer than the file = whole file
        ("bytes=990-5000", (990, 999)),  # end clamped to the file
        ("bytes=999-999", (999, 999)),
        ("  BYTES = 10-20 ", (10, 20)),
    ],
)
def test_valid_ranges(header, expected):
    assert parse_range(header, SIZE) == expected


@pytest.mark.parametrize(
    "header",
    [
        "items=0-10",  # unknown unit
        "bytes=0-10,20-30",  # multi-range: served as a full 200
        "bytes=abc-def",
        "bytes=10-5",  # end before start: invalid, ignored
        "bytes=",
        "bytes=10",
        "bytes=\u00b2-5",  # unicode digit that isdigit() accepts but int() rejects
        "garbage",
    ],
)
def test_ignored_headers_serve_whole_file(header):
    assert parse_range(header, SIZE) is None


@pytest.mark.parametrize("header", ["bytes=1000-", "bytes=1000-1100", "bytes=5000-", "bytes=-0"])
def test_unsatisfiable(header):
    with pytest.raises(RangeNotSatisfiable):
        parse_range(header, SIZE)
