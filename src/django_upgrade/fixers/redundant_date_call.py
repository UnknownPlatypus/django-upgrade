from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_name_attr
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.fixers.utils_timezone_simplifications import remove_attr_call
from django_upgrade.tokens import find_and_replace_name

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


def _is_timezone_localtime(node: ast.expr, state: State) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and is_name_attr(
            node.func,
            imports=state.from_imports,
            mods=("timezone", "django.utils.timezone"),
            names={"localtime"},
        )
    )


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    # Check for .date() call
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr == "date"
        and not node.args
        and not node.keywords
        and isinstance(node.func.value, ast.BinOp)
        and (
            (
                isinstance(node.func.value.op, ast.Sub)
                and _is_timezone_localtime(node.func.value.left, state)
            )
            or (
                isinstance(node.func.value.op, ast.Add)
                and (
                    _is_timezone_localtime(node.func.value.left, state)
                    or _is_timezone_localtime(node.func.value.right, state)
                )
            )
        )
    ):
        yield ast_start_offset(node), partial(
            find_and_replace_name, name="localtime", new="localdate"
        )
        yield ast_start_offset(node), partial(remove_attr_call)
