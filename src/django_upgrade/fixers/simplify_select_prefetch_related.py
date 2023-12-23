from __future__ import annotations

import ast
from functools import partial
from typing import Dict
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import OP
from django_upgrade.tokens import parse_call_args
from django_upgrade.tokens import remove_arg
from django_upgrade.tokens import reverse_find

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)

NestedDict = Dict[str, "NestedDict"]


@fixer.register(ast.Call)
def visit_Call(
    state: State,
    node: ast.Call,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(node.func, ast.Attribute)
        and node.func.attr in {"select_related", "prefetch_related"}
        and not node.keywords
        and len(node.args) > 1
        and any(
            isinstance(arg, ast.Constant) and "__" in arg.value for arg in node.args
        )
    ):
        fields = sorted(
            (
                (arg.value, idx)
                for idx, arg in enumerate(node.args)
                if isinstance(arg, ast.Constant)
            ),
            key=lambda k: len(k[0]),
            reverse=True,
        )

        args_idx_to_remove = []
        field_dict: NestedDict = {}
        for field, arg_idx in fields:
            d = field_dict
            for part in field.split("__"):
                d = d.setdefault(part, {})
            if d != {}:
                args_idx_to_remove.append(arg_idx)

        if args_idx_to_remove:
            yield ast_start_offset(node.args[0]), partial(
                simplify_related_lookup, args_idx_to_remove=args_idx_to_remove
            )


def simplify_related_lookup(
    tokens: list[Token], i: int, *, args_idx_to_remove: list[int]
) -> None:
    open_idx = reverse_find(tokens, i, name=OP, src="(")
    func_args, _ = parse_call_args(tokens, open_idx)

    for arg_idx in sorted(args_idx_to_remove, reverse=True):
        remove_arg(tokens, func_args=func_args, arg_idx_to_remove=arg_idx)
