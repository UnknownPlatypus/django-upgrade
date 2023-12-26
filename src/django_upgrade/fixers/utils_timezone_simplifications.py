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
from django_upgrade.tokens import find_and_replace_name
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
    if is_name_attr(
        node=node.func,
        imports=state.from_imports,
        mods=("timezone",),
        names={"localdate", "localtime"},
    ):
        # `timezone.localdate(timezone.now())` -> `timezone.localdate()`
        # `timezone.localtime(timezone.now())` -> `timezone.localtime()`
        if (
            len(node.args) == 1
            and isinstance(node.args[0], ast.Call)
            and is_name_attr(
                node=node.args[0].func,
                imports=state.from_imports,
                mods=("timezone",),
                names={"now"},
            )
        ):
            yield ast_start_offset(node), partial(remove_call_args)

        # `timezone.localtime(...).date()` -> `timezone.localdate()`
        if (
            isinstance(parents[-1], ast.Attribute)
            and parents[-1].attr == "date"
            and isinstance(parents[-2], ast.Call)
            and not parents[-2].args
            and not parents[-2].keywords
        ):
            yield ast_start_offset(node), partial(
                find_and_replace_name, name="localtime", new="localdate"
            )
            yield ast_start_offset(node), partial(remove_attr_call)

    elif (
        is_name_attr(
            node=node.func,
            imports=state.from_imports,
            mods=("timezone",),
            names={"make_aware"},
        )
        and len(node.args) == 1
        and isinstance((inner_node := node.args[0]), ast.Call)
        and isinstance(inner_node.func, ast.Attribute)
        and inner_node.func.attr == "now"
        and is_name_attr(
            node=inner_node.func.value,
            imports=state.from_imports,
            mods=("dt", "datetime"),
            names={"datetime"},
        )
    ):
        yield ast_start_offset(node), partial(remove_call_args)
        yield ast_start_offset(node), partial(
            find_and_replace_name, name="make_aware", new="localtime"
        )


def remove_call_args(tokens: list[Token], i: int) -> None:
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)
    del tokens[open_idx + 1 : close_idx - 1]


def remove_attr_call(tokens: list[Token], i: int) -> None:
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)
    attr_call_close_idx = find(tokens, close_idx, name=OP, src=")")
    del tokens[close_idx : attr_call_close_idx + 1]
