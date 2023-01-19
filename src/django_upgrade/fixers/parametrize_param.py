"""
Add the 'length' argument to get_random_string():
https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1
"""
from __future__ import annotations

import ast
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import delete_argument
from django_upgrade.tokens import find
from django_upgrade.tokens import find_first_token
from django_upgrade.tokens import find_last_token
from django_upgrade.tokens import OP
from django_upgrade.tokens import parse_call_args
from django_upgrade.tokens import replace


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
        and node.func.attr == "parametrize"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "mark"
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "pytest"
        and any((ids_node := kw).arg == "ids" for kw in node.keywords)
        and isinstance(ids_node.value, (ast.List, ast.Tuple))
        and all(isinstance(id_const, ast.Constant) for id_const in ids_node.value.elts)
        and isinstance(node.args[1], (ast.List, ast.Tuple))
        and isinstance(node.args[1].elts[0], (ast.List, ast.Tuple))
    ):
        yield ast_start_offset(node), partial(
            update_parametrize_call,
            node=node,
            ids_node_idx=len(node.args) + node.keywords.index(ids_node),
            ids_values=[
                id_const.value for id_const in ids_node.value.elts  # type: ignore
            ],
        )


def update_parametrize_call(
    tokens: list[Token],
    i: int,
    *,
    node: ast.Call,
    ids_node_idx: int,
    ids_values: list[str],
) -> None:
    # Delete ids list
    j = find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, j)
    delete_argument(ids_node_idx, tokens, func_args)

    # Update params
    for param, id_value in zip(node.args[1].elts, ids_values):  # type: ignore
        start_idx = find_first_token(tokens, i, node=param)
        end_idx = find_last_token(tokens, j, node=param)

        is_multiline = param.lineno != param.end_lineno
        new_src = "" if (is_multiline or not param.elts) else ", "
        replace(tokens, start_idx, src="pytest.param(")
        replace(tokens, end_idx, src=f'{new_src}id="{id_value}")')
