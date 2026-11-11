"""HTTP Range header parsing (RFC 9110 section 14). Single byte-range only. No framework imports."""


class RangeNotSatisfiable(Exception):
    pass


def parse_range(header: str | None, size: int) -> tuple[int, int] | None:
    """Return the inclusive (start, end) byte range to serve, or None to serve the whole file.

    - Missing, malformed, non-"bytes" or multi-range headers are ignored (a 200 with the full body is valid).
    - Raises RangeNotSatisfiable when the range is well-formed but lies outside the file (-> 416).
    """
    if not header:
        return None
    unit, eq, spec = header.partition("=")
    if not eq or unit.strip().lower() != "bytes":
        return None
    spec = spec.strip()
    if "," in spec:
        return None
    first, dash, last = spec.partition("-")
    first, last = first.strip(), last.strip()
    if not dash:
        return None

    def num(s: str) -> int | None:
        return int(s) if s.isascii() and s.isdigit() else None

    if first == "":  # suffix range: the last N bytes
        n = num(last)
        if n is None:
            return None
        if n == 0 or size == 0:
            raise RangeNotSatisfiable
        return max(size - n, 0), size - 1

    start = num(first)
    if start is None:
        return None
    if last == "":
        end = size - 1
    else:
        parsed = num(last)
        if parsed is None or parsed < start:
            return None  # syntactically invalid: ignore the header
        end = min(parsed, size - 1)
    if start >= size:
        raise RangeNotSatisfiable
    return start, end
