"""
Use multiple `pytest.param(..., id=...)` over `ids=[...]`
"""

from __future__ import annotations

import ast
from collections.abc import Iterable
from functools import partial
from typing import cast

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import OP
from django_upgrade.tokens import delete_argument
from django_upgrade.tokens import find
from django_upgrade.tokens import find_first_token
from django_upgrade.tokens import find_last_token
from django_upgrade.tokens import insert
from django_upgrade.tokens import parse_call_args
from django_upgrade.tokens import replace
from django_upgrade.tokens import reverse_consume_non_semantic_elements

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: tuple[ast.AST, ...],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        state.looks_like_test_file
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "parametrize"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "mark"
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "pytest"
        and any((ids_node := kw).arg == "ids" for kw in node.keywords)
        and isinstance(ids_node.value, (ast.List, ast.Tuple))
        and ids_node.value.elts
        and all(isinstance(el, ast.Constant) for el in ids_node.value.elts)
        and isinstance(node.args[1], (ast.List, ast.Tuple))
        and isinstance(node.args[1].elts[0], (ast.List, ast.Tuple))
        and isinstance(node.args[0], (ast.Constant, ast.List, ast.Tuple))
    ):
        yield ast_start_offset(node), partial(
            update_parametrize_call,
            pytest_argnames=node.args[0],
            pytest_argvalues=node.args[1],
            ids_node_idx=len(node.args) + node.keywords.index(ids_node),
            ids_values=[cast(ast.Constant, el).value for el in ids_node.value.elts],
        )


def update_parametrize_call(
    tokens: list[Token],
    i: int,
    *,
    pytest_argnames: ast.Constant | ast.List | ast.Tuple,
    pytest_argvalues: ast.List | ast.Tuple,
    ids_node_idx: int,
    ids_values: list[str],
) -> None:
    # Delete ids list
    j = find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, j)
    delete_argument(ids_node_idx, tokens, func_args)

    nb_argnames = len(
        pytest_argnames.value.split(",")
        if isinstance(pytest_argnames, ast.Constant)
        else pytest_argnames.elts
    )
    # Update params
    for param, id_value in zip(pytest_argvalues.elts, ids_values):
        start_idx = find_first_token(tokens, i, node=param)
        end_idx = find_last_token(tokens, j, node=param)
        last_nl_idx = reverse_consume_non_semantic_elements(tokens, end_idx)
        sep = "" if tokens[last_nl_idx - 1].matches(name=OP, src=",") else ", "

        if nb_argnames == 1:
            insert(tokens, start_idx, new_src="pytest.param(")
            insert(tokens, end_idx + 2, new_src=f', id="{id_value}")')
        else:
            replace(tokens, start_idx, src="pytest.param(")
            replace(tokens, end_idx, src=f'{sep}id="{id_value}")')
