"""Tests for csvtail."""
import pytest
from csvtail import CsvTailError, tail, tail_text


class TestBasic:
    def test_tail_n_lines(self):
        text = "a,b\nc,d\ne,f\ng,h\n"
        assert tail_text(text, 2) == [["e", "f"], ["g", "h"]]

    def test_n_larger_than_rows(self):
        text = "a,b\nc,d\n"
        assert tail_text(text, 10) == [["a", "b"], ["c", "d"]]

    def test_zero_n(self):
        assert tail_text("a,b\nc,d\n", 0) == []

    def test_no_trailing_newline(self):
        assert tail_text("a,b\nc,d", 1) == [["c", "d"]]

    def test_empty_input(self):
        assert tail_text("", 5) == []

    def test_with_header(self):
        text = "name,age\nalice,30\nbob,25\ncarol,40\n"
        assert tail_text(text, 2, has_header=True) == [
            ["name", "age"], ["bob", "25"], ["carol", "40"]
        ]


class TestQuoting:
    def test_quoted_field(self):
        text = '"hello, world",2\n'
        assert tail_text(text, 1) == [["hello, world", "2"]]

    def test_doubled_quote(self):
        text = '"she said ""hi""",1\n'
        assert tail_text(text, 1) == [['she said "hi"', "1"]]

    def test_embedded_newline(self):
        text = '"line1\nline2",x\n'
        assert tail_text(text, 1) == [["line1\nline2", "x"]]

    def test_unterminated_quote(self):
        with pytest.raises(CsvTailError):
            tail_text('"unterminated\n', 1)


class TestDelimiter:
    def test_tsv(self):
        text = "a\tb\nc\td\n"
        assert tail_text(text, 1, delim="\t") == [["c", "d"]]

    def test_pipe(self):
        text = "a|b|c\nd|e|f\n"
        assert tail_text(text, 1, delim="|") == [["d", "e", "f"]]


class TestCRLF:
    def test_crlf(self):
        text = "a,b\r\nc,d\r\n"
        assert tail_text(text, 1) == [["c", "d"]]


class TestErrors:
    def test_negative_n(self):
        with pytest.raises(CsvTailError):
            tail_text("a,b\n", -1)

    def test_n_must_be_int(self):
        with pytest.raises(CsvTailError):
            tail_text("a,b\n", "two")  # type: ignore[arg-type]


class TestStreaming:
    def test_iterable_of_chunks(self):
        # Even one char at a time should work.
        chunks = ["a,", "b\n", "c", ",d\n"]
        assert tail(chunks, 1) == [["c", "d"]]


class TestFile:
    def test_from_file(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("a,b\nc,d\ne,f\n")
        assert tail(p, 2) == [["c", "d"], ["e", "f"]]

    def test_from_file_with_header(self, tmp_path):
        p = tmp_path / "data.csv"
        p.write_text("name,age\nalice,30\nbob,25\n")
        assert tail(p, 1, has_header=True) == [["name", "age"], ["bob", "25"]]
