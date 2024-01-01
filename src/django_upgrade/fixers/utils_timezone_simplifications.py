from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_name_attr
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import find
from django_upgrade.tokens import OP
from django_upgrade.tokens import parse_call_args

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        is_name_attr(
            node=node.func,
            imports=state.from_imports,
            mods=("timezone",),
            names={"localdate", "localtime"},
        )
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Call)
        and is_name_attr(
            node=node.args[0].func,
            imports=state.from_imports,
            mods=("timezone",),
            names={"now"},
        )
    ):
        yield ast_start_offset(node), partial(remove_call_args)


def remove_call_args(tokens: list[Token], i: int) -> None:
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)
    del tokens[open_idx + 1 : close_idx - 1]
