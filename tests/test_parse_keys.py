import pytest
import pytest

from py_rgd.parser import Parser, RGDKeyValueError


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
    p = Parser()
    test_str = r"""
    A
    more.complex.key
    perfectly-fine
    12
    15.0
    """
    answers = [ "A", "more.complex.key", "perfectly-fine", "12", "15.0", ]
    for line, answer in zip(test_str.strip().splitlines(), answers):
        key, line = p._parse_key(line.strip())
        assert key == answer


def test_parse_bad_keys():
    p = Parser()
    test_str = r"""
    ?
    <ex>
    😈
    ""
    ''
    invalid=char
    no spaces
    {}
    """
    for line in test_str.strip().splitlines():
        print(line)
        with pytest.raises(RGDKeyValueError):
            key, line = p._parse_key(line.strip())

