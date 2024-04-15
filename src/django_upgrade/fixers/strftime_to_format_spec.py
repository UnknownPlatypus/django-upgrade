from __future__ import annotations

import ast
import re
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.FormattedValue)
def visit_FormattedValue(
    state: State,
    node: ast.FormattedValue,
    parents: list[ast.AST],
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
    tokens[i] = tokens[i]._replace(
        src=re.sub(r"\.strftime\(['\"](.*?)['\"]\)}", r":\1}", tokens[i].src)
    )
