import pytest

from py_rgd.parser import Parser


def test_parse_key_quoted():
    p = Parser()
    test_str = r"""
    "A"
    'B'
    "'C'"
    '"D"'
    "\"E\""
    '\'F\''
    "🫡"
    "\"more complex\".'key'"
    """
    answers = ["A", "B", "'C'", '"D"', r'\"E\"', r"\'F\'", "🫡", r"\"more complex\".'key'"]
    for line, answer in zip(test_str.strip().splitlines(), answers):
        key, line = p._parse_key(line.strip())
        assert key == answer

def test_parse_key_unquoted():
    ...

