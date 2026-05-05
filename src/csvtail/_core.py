"""Core csvtail implementation.

A small RFC-4180 state machine. We feed it characters one at a time and
it yields complete rows. By keeping only the trailing ring of N rows we
keep memory bounded regardless of file size.
"""
from __future__ import annotations

from collections import deque
from pathlib import Path
from typing import Deque, Iterable, Iterator, List, Union


__all__ = ["CsvTailError", "tail", "tail_text"]


class CsvTailError(ValueError):
    """Raised on malformed CSV input."""


# State machine states
_FIELD_START = 0  # Beginning of a new field; decide quoted vs bare.
_BARE = 1         # Inside an unquoted field.
_QUOTED = 2       # Inside a quoted field.
_QUOTED_QUOTE = 3  # Just saw `"` while in QUOTED — could be escape or end.


def _parse(stream: Iterable[str], delim: str) -> Iterator[List[str]]:
    """Yield each parsed row from a character stream."""
    state = _FIELD_START
    field_buf: List[str] = []
    row: List[str] = []

    def push_field() -> None:
        row.append("".join(field_buf))
        field_buf.clear()

    for ch in stream:
        if state == _FIELD_START:
            if ch == '"':
                state = _QUOTED
            elif ch == delim:
                push_field()
            elif ch == "\r":
                # Possibly CRLF; consume CR but emit row on the LF below.
                continue
            elif ch == "\n":
                push_field()
                yield row
                row = []
            else:
                field_buf.append(ch)
                state = _BARE
        elif state == _BARE:
            if ch == delim:
                push_field()
                state = _FIELD_START
            elif ch == "\r":
                continue
            elif ch == "\n":
                push_field()
                yield row
                row = []
                state = _FIELD_START
            else:
                field_buf.append(ch)
        elif state == _QUOTED:
            if ch == '"':
                state = _QUOTED_QUOTE
            else:
                field_buf.append(ch)
        elif state == _QUOTED_QUOTE:
            if ch == '"':
                # Escaped quote inside the field
                field_buf.append('"')
                state = _QUOTED
            elif ch == delim:
                push_field()
                state = _FIELD_START
            elif ch == "\r":
                continue
            elif ch == "\n":
                push_field()
                yield row
                row = []
                state = _FIELD_START
            else:
                raise CsvTailError(
                    f"unexpected character {ch!r} after closing quote"
                )

    # End of stream — flush trailing partial row if any.
    if state == _QUOTED:
        raise CsvTailError("unterminated quoted field at end of input")
    # Flush trailing field/row if there's buffered content or the row started.
    if state in (_BARE, _QUOTED_QUOTE) or field_buf or row:
        push_field()
        yield row


def _char_stream_from_file(path: Union[str, Path], encoding: str) -> Iterator[str]:
    p = Path(path)
    with p.open("r", encoding=encoding, newline="") as f:
        while True:
            buf = f.read(8192)
            if not buf:
                return
            for ch in buf:
                yield ch


def tail(
    source: Union[str, Path, Iterable[str]],
    n: int,
    *,
    delim: str = ",",
    encoding: str = "utf-8",
    has_header: bool = False,
) -> List[List[str]]:
    """Return the last ``n`` rows of a CSV.

    Args:
        source: A file path *or* any iterable of strings (each yielded
            string is treated as a fragment to consume — even one
            character at a time works).
        n: How many trailing rows to keep. Must be ``>= 0``.
        delim: Field delimiter. ``"\\t"`` for TSV.
        encoding: Used when ``source`` is a path.
        has_header: If True, the first row is *always* included as
            ``rows[0]``, with the next ``n`` data rows after it.

    Returns:
        A list of rows. Each row is a list of string fields.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise CsvTailError(f"n must be int, got {type(n).__name__}")
    if n < 0:
        raise CsvTailError(f"n must be non-negative, got {n}")

    if isinstance(source, Path):
        stream: Iterable[str] = _char_stream_from_file(source, encoding)
    elif isinstance(source, str):
        # Heuristic: a CSV body is short and contains newlines or commas;
        # a path is a single short string. Be conservative — only treat
        # as a file if it has no newline AND points at an existing file.
        if source and "\n" not in source and "\r" not in source and Path(source).is_file():
            stream = _char_stream_from_file(source, encoding)
        else:
            stream = iter(source)
    else:
        # Iterable of strings (fragments) — flatten to chars.
        def _flatten() -> Iterator[str]:
            for piece in source:  # type: ignore[union-attr]
                if not isinstance(piece, str):
                    raise CsvTailError("source iterable must yield str")
                for c in piece:
                    yield c
        stream = _flatten()

    ring: Deque[List[str]] = deque(maxlen=n if n > 0 else 1)
    header: List[str] | None = None
    first = True
    for row in _parse(stream, delim):
        if has_header and first:
            header = row
            first = False
            continue
        first = False
        if n > 0:
            ring.append(row)

    out: List[List[str]] = list(ring) if n > 0 else []
    if has_header and header is not None:
        out.insert(0, header)
    return out


def tail_text(text: str, n: int, **kwargs) -> List[List[str]]:
    """Convenience wrapper: tail the last ``n`` rows of a CSV string."""
    return tail(text, n, **kwargs)
