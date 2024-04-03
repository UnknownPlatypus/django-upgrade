from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.field_order_const import MODEL_FIELD_ARG_ORDER
from django_upgrade.tokens import reorder_call_kwargs

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


def model_arg_sort_func(x: str | None) -> int:
    """Sort keyword list based on a reference index list"""
    if x in MODEL_FIELD_ARG_ORDER:
        return MODEL_FIELD_ARG_ORDER.index(x)
    return 100


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        state.looks_like_models_file
        and len(node.keywords) > 1
        and (
            (
                isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.attr.endswith("Field")
            )
            or (isinstance(node.func, ast.Name) and node.func.id.endswith("Field"))
        )
        and any(kw.arg in MODEL_FIELD_ARG_ORDER for kw in node.keywords)
    ):
        initial_kwargs = [kw.arg for kw in node.keywords]
        ordered_kwargs = sorted(initial_kwargs, key=model_arg_sort_func)

        if not initial_kwargs == ordered_kwargs:
            yield ast_start_offset(node), partial(
                reorder_call_kwargs,
                node=node,
                ordered_kwargs_idx=[initial_kwargs.index(kw) for kw in ordered_kwargs],
            )
