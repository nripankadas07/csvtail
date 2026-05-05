"""csvtail — streaming last-N rows of a CSV/TSV in constant memory.

The parser is a small RFC 4180-style state machine; it handles quoted
fields, embedded newlines, doubled-quote escapes, and CRLF line endings.
Memory usage is O(N) (the ring of last-N rows) rather than O(file).

Public API:
* :func:`tail`           — yield last ``n`` rows of a file or text-iter.
* :func:`tail_text`      — same, but takes a string.
* :class:`CsvTailError`  — raised on malformed input (ValueError subclass).
"""
from __future__ import annotations

from ._core import CsvTailError, tail, tail_text

__all__ = ["CsvTailError", "tail", "tail_text"]
__version__ = "0.1.0"
