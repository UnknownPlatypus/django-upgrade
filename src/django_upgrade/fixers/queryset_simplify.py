from __future__ import annotations

import ast
from functools import partial
from typing import Iterable
from typing import Literal

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import CODE
from django_upgrade.tokens import find
from django_upgrade.tokens import NAME
from django_upgrade.tokens import OP

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)

_QS_GETTERS = {
    "first",
    "last",
    "get",
    "latest",
    "earliest",
    "afirst",
    "alast",
    "aget",
    "alatest",
    "aearliest",
}


@fixer.register(ast.Subscript)
def visit_Subscript(
    state: State,
    node: ast.Subscript,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.slice, ast.Index)
        and isinstance(
            (slice_value := node.slice.value),  # type: ignore[attr-defined]
            ast.Constant,
        )
        and isinstance(node.value, ast.Call)
        and len(node.value.args) == 0
        and len(node.value.keywords) == 0
        and isinstance(node.value.func, ast.Attribute)
        and (modifier := node.value.func.attr) in _QS_GETTERS
        and isinstance(node.value.func.value, ast.Call)
        and isinstance(node.value.func.value.func, ast.Attribute)
        and node.value.func.value.func.attr == "values"
        and len(node.value.func.value.args) == 1
        and isinstance(node.value.func.value.args[0], ast.Constant)
        and node.value.func.value.args[0].value == slice_value.value
    ):
        yield ast_start_offset(node), partial(
            fix_values_subscript, slice_value=slice_value.value, modifier=modifier
        )


def fix_values_subscript(
    tokens: list[Token], i: int, *, slice_value: str, modifier: Literal["first", "last"]
) -> None:
    start_idx = find(tokens, i, name=NAME, src="values")
    end_idx = find(tokens, start_idx, name=OP, src="]")
    tokens[start_idx : end_idx + 1] = [
        Token(name=CODE, src=f'values_list("{slice_value}", flat=True).{modifier}()')
    ]
