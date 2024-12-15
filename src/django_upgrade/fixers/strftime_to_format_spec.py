from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import CODE
from django_upgrade.tokens import NAME
from django_upgrade.tokens import OP
from django_upgrade.tokens import STRING
from django_upgrade.tokens import find
from django_upgrade.tokens import parse_call_args

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.FormattedValue)
def visit_FormattedValue(
    state: State,
    node: ast.FormattedValue,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.value, ast.Call)
        and len(node.value.args) == 1
        and isinstance(node.value.args[0], ast.Constant)
        and isinstance(node.value.func, ast.Attribute)
        and node.value.func.attr == "strftime"
    ):
        yield ast_start_offset(node), partial(fix_strftime_in_fstring)


def fix_strftime_in_fstring(tokens: list[Token], i: int) -> None:
    if tokens[i].name == STRING:
        tokens[i] = tokens[i]._replace(
            src=re.sub(r"\.strftime\(['\"](.*?)['\"]\)}", r":\1}", tokens[i].src)
        )
    else:
        # Python 3.12
        start_idx = find(tokens, i, name=NAME, src="strftime")
        format_spec = tokens[find(tokens, i, name=STRING)].src
        _, close_idx = parse_call_args(tokens, start_idx + 1)
        if tokens[close_idx].name == OP and tokens[close_idx].src == "}":
            tokens[start_idx - 1 : close_idx] = [
                Token(name=CODE, src=f":{format_spec[1:-1]}")
            ]
