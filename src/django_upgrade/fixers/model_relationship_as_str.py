"""
"""
from __future__ import annotations

import ast
import os
from functools import partial
from typing import Iterable

from tokenize_rt import Offset

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_name_attr
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
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
        is_name_attr(
            node=node.func,
            imports=state.from_imports,
            mods=("models",),
            names={"ForeignKey", "ManyToManyField", "OneToOneField"},
        )
        and len(node.args) > 0
    ):
        if isinstance((related_model := node.args[0]), ast.Name):
            for module, names in state.from_imports.items():
                if related_model.id in names and "django." not in module:
                    new_str = f"{module.rpartition('.models')[0]}.{related_model.id}"
                    yield ast_start_offset(related_model), partial(
                        replace, src=f'"{new_str}"'
                    )
        elif (
            isinstance((related_model := node.args[0]), ast.Constant)
            and related_model.value != "self"
            and "." not in related_model.value
        ):
            app_name = os.path.normpath(state.filename).rpartition("/models")[0]
            new_str = f"{app_name}.{related_model.value}"
            yield ast_start_offset(related_model), partial(replace, src=f'"{new_str}"')
