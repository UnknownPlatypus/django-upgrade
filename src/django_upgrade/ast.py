from __future__ import annotations

import ast
import warnings
from typing import Container
from typing import Literal

from tokenize_rt import Offset


def ast_parse(contents_text: str) -> ast.Module:
    # intentionally ignore warnings, we can't do anything about them
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(contents_text.encode())


def ast_start_offset(node: ast.expr | ast.keyword | ast.stmt) -> Offset:
    return Offset(node.lineno, node.col_offset)


def is_rewritable_import_from(node: ast.ImportFrom) -> bool:
    # Not relative import or import *
    return node.level == 0 and not (len(node.names) == 1 and node.names[0].name == "*")


TEST_CLIENT_REQUEST_METHODS = frozenset(
    (
        "request",
        "get",
        "post",
        "head",
        "options",
        "put",
        "patch",
        "delete",
        "trace",
    )
)


def looks_like_test_client_call(
    node: ast.AST, client_name: Literal["async_client", "client"]
) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr in TEST_CLIENT_REQUEST_METHODS
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == client_name
        and isinstance(node.func.value.value, ast.Name)
        and node.func.value.value.id == "self"
    )


def is_name_attr(
    node: ast.AST,
    imports: dict[str, set[str]],
    mods: tuple[str, ...],
    names: Container[str],
) -> bool:
    return (
        isinstance(node, ast.Name)
        and node.id in names
        and any(node.id in imports[mod] for mod in mods)
    ) or (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id in mods
        and node.attr in names
    )


def is_single_target_assign(node: ast.Assign | ast.AnnAssign) -> ast.AST | None:
    if isinstance(node, ast.Assign) and len(node.targets) == 1:
        return node.targets[0]

    if isinstance(node, ast.AnnAssign) and node.value is not None:
        return node.target

    return None
