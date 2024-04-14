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
from django_upgrade.tokens import CODE
from django_upgrade.tokens import NAME
from django_upgrade.tokens import OP
from django_upgrade.tokens import find
from django_upgrade.tokens import find_and_replace_name
from django_upgrade.tokens import parse_call_args
from django_upgrade.tokens import remove_arg

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
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "strptime"
        and len(node.args) == 2
        and isinstance(node.args[1], ast.Constant)
        and is_name_attr(
            node=node.func.value,
            imports=state.from_imports,
            mods=("dt", "datetime"),
            names={"datetime"},
        )
    ):
        # dt.datetime.strptime("2024-02-12", "%Y-%m-%d").date()
        if (
            isinstance(parents[-1], ast.Attribute)
            and parents[-1].attr == "date"
            and node.args[1].value == "%Y-%m-%d"  # Isoformat
            and isinstance(parents[-2], ast.Call)
            and not parents[-2].args
            and not parents[-2].keywords
        ):
            yield ast_start_offset(node), partial(use_isoformat_over_date_strptime)

        # dt.datetime.strptime("2024-12-13T12:00:23", "%Y-%m-%dT%H:%M:%S")
        elif node.args[1].value[:8] == "%Y-%m-%d" and node.args[1].value[9:] in {
            "",
            "%H",
            "%H:%M",
            "%H:%M:%S",
            "%H:%M:%S.%f",
        }:
            yield ast_start_offset(node), partial(use_isoformat_over_datetime_strptime)


def use_isoformat_over_date_strptime(tokens: list[Token], i: int) -> None:
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)

    # Remove `.date()` attribute call.
    attr_call_close_idx = find(tokens, close_idx, name=OP, src=")")
    del tokens[close_idx : attr_call_close_idx + 1]

    # Remove "%Y-%m-%d" 2nd argument
    remove_arg(tokens, func_args, close_idx, arg_idx=1)

    # Replace `datetime.strptime` with `date.fromisoformat`
    datetime_idx = find(tokens, i, name=NAME, src="datetime")
    tokens[datetime_idx:open_idx] = [Token(name=CODE, src="date.fromisoformat")]


def use_isoformat_over_datetime_strptime(tokens: list[Token], i: int) -> None:
    open_idx = find(tokens, i, name=OP, src="(")
    func_args, close_idx = parse_call_args(tokens, open_idx)

    # Remove 2nd argument (Format string)
    remove_arg(tokens, func_args, close_idx, arg_idx=1)

    # Replace `datetime.strptime` with `datetime.fromisoformat`
    find_and_replace_name(tokens, i, name="strptime", new="fromisoformat")
