import ast
import math
import re
from datetime import date, datetime, time
from lark import Transformer, v_args


class RGDValueTransformer(Transformer):
    def basic_string(self, items):
        text = str(items[0])

        # Python string literals support \x, \u, \U, \n, \t, etc.,
        # but not TOML/RGD-style \e.
        text = text.replace(r"\e", r"\x1b")
        return ast.literal_eval(text)

    def literal_string(self, items):
        text = str(items[0])
        return text[1:-1]

    def UNQUOTED_KEY(self, items):
        return str(items)

    def bool(self, items):
        return str(items[0]) == "true"

    def int(self, items):
        return int(str(items[0]).replace("_", ""), 10)

    def hex_int(self, items):
        return int(str(items[0]).replace("_", ""), 16)

    def oct_int(self, items):
        return int(str(items[0]).replace("_", ""), 8)

    def bin_int(self, items):
        return int(str(items[0]).replace("_", ""), 2)

    def float(self, items):
        text = str(items[0]).replace("_", "")
        return float(text)

    def datetime(self, items):
        return parse_rgd_datetime(str(items[0]))

    def array(self, items):
        return list(items)

    def keyval(self, items):
        return (items[0], items[1])

    def metadata(self, items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate metadata key: {key!r}")
            out[key] = value
        return out

    def key_set(self, items):
        values = set(items)
        if len(items) != len(values):
            raise ValueError(f"duplicate key in key set: {items!r}")
        return values

    def legacy_bare(self, items):
        return str(items[0])

    def legacy_description(self, items):
        return list(items)

    def lr(self, items):
        return "->"

    def rl(self, items):
        return "<-"

    def bi(self, items):
        return "<>"

    def un(self, items):
        return "--"


_DATE_ONLY = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_TIME_ONLY = re.compile(r"^\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?$")

def parse_rgd_datetime(text: str):
    normalized = text

    if "t" in normalized:
        normalized = normalized.replace("t", "T", 1)

    if normalized.endswith(("Z", "z")):
        normalized = normalized[:-1] + "+00:00"

    if _DATE_ONLY.fullmatch(normalized):
        return date.fromisoformat(normalized)

    if _TIME_ONLY.fullmatch(normalized):
        return time.fromisoformat(normalized)

    return datetime.fromisoformat(normalized)
