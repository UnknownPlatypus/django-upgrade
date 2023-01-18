"""
Add the 'length' argument to get_random_string():
https://docs.djangoproject.com/en/3.1/releases/3.1/#features-deprecated-in-3-1
"""
from __future__ import annotations

import ast
import subprocess
from functools import partial
from pprint import pprint
from typing import Iterable
from typing import MutableMapping
from weakref import WeakKeyDictionary

import astpretty
from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_rewritable_import_from
from django_upgrade.compat import str_removesuffix
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import CODE
from django_upgrade.tokens import find
from django_upgrade.tokens import OP
from django_upgrade.tokens import replace
from django_upgrade.tokens import update_import_names

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


def is_mongo_stage_node(node: ast.AST, stage_name: str) -> bool:
    return (
        isinstance(node, ast.Dict)
        and len(node.keys) == 1
        and isinstance(node.keys[0], ast.Constant)
        and node.keys[0].value == stage_name
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
        and print(
            f"\n=================================\n"
            f"bat {state.filename[2:]} -r {node.lineno}:{node.end_lineno}\n"
            f"{subprocess.call(f'bat {state.filename[2:]} --paging always -r {node.lineno}:{node.end_lineno}',shell=True)}"
            f"\n=================================\n"
        )
    ):
        yield
        print("That's SICK")
