from __future__ import annotations

import ast
import enum
from collections import defaultdict
from functools import partial
from typing import Iterable

from tokenize_rt import Offset
from tokenize_rt import Token

from django_upgrade.ast import ast_start_offset
from django_upgrade.ast import is_name_attr
from django_upgrade.ast import is_single_target_assign
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import consume
from django_upgrade.tokens import find_first_token_at_line
from django_upgrade.tokens import PHYSICAL_NEWLINE
from django_upgrade.tokens import reverse_consume_non_semantic_elements

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


class ContentType(int, enum.Enum):
    """Enumeration of possible types of block in a django class"""

    UNKNOWN = 0
    FIELD_DECLARATION = enum.auto()
    MANAGER_DECLARATION = enum.auto()
    META_CLASS = enum.auto()
    NATURAL_KEY_METHOD = enum.auto()
    INIT_METHOD = enum.auto()
    REPR_METHOD = enum.auto()
    STR_METHOD = enum.auto()
    CLEAN_METHOD = enum.auto()
    SAVE_METHOD = enum.auto()
    ASAVE_METHOD = enum.auto()
    DELETE_METHOD = enum.auto()
    ADELETE_METHOD = enum.auto()
    GET_ABSOLUTE_URL_METHOD = enum.auto()
    CUSTOM_PROPERTY = enum.auto()
    CUSTOM_METHOD = enum.auto()
    CUSTOM_CLASS_METHOD = enum.auto()
    CUSTOM_STATIC_METHOD = enum.auto()


_function_name_to_content_type = {
    "__str__": ContentType.STR_METHOD,
    "__init__": ContentType.INIT_METHOD,
    "__repr__": ContentType.REPR_METHOD,
    "save": ContentType.SAVE_METHOD,
    "get_absolute_url": ContentType.GET_ABSOLUTE_URL_METHOD,
    "clean": ContentType.CLEAN_METHOD,
    "delete": ContentType.DELETE_METHOD,
    "asave": ContentType.ASAVE_METHOD,
    "adelete": ContentType.ADELETE_METHOD,
    "natural_key": ContentType.NATURAL_KEY_METHOD,
}
_decorator_to_content_type = {
    "property": ContentType.CUSTOM_PROPERTY,
    "cached_property": ContentType.CUSTOM_PROPERTY,
    "setter": ContentType.CUSTOM_PROPERTY,
    "deleter": ContentType.CUSTOM_PROPERTY,
    "classmethod": ContentType.CUSTOM_CLASS_METHOD,
    "staticmethod": ContentType.CUSTOM_STATIC_METHOD,
}

_PHYSICAL_NEWLINE_TOKEN = Token(name=PHYSICAL_NEWLINE, src="\n")


def get_element_type_with_lineno(
    element: ast.AST,
) -> tuple[ContentType, int]:
    if (
        isinstance(element, (ast.Assign, ast.AnnAssign))
        and (target := is_single_target_assign(element))
        and isinstance(target, ast.Name)
    ):
        if target.id == "objects" or (
            isinstance(element.value, ast.Call)
            and "Manager" in getattr(element.value.func, "id", "")
        ):
            # Because Manager definition order in the class matter, it is not a
            # safe idea to try distinguishing the `object` manager from other ones.
            # https://docs.djangoproject.com/fr/4.2/topics/db/managers/#default-managers
            return ContentType.MANAGER_DECLARATION, element.lineno
        return ContentType.FIELD_DECLARATION, element.lineno

    if isinstance(element, ast.ClassDef) and element.name == "Meta":
        return ContentType.META_CLASS, element.lineno

    if isinstance(element, ast.FunctionDef):
        el_lineno = element.lineno - len(element.decorator_list)
        if content_type := _function_name_to_content_type.get(element.name):
            return content_type, el_lineno

        for decorator in element.decorator_list:
            # We only need to check for `@foo` or `@foo.bar`.
            if content_type := _decorator_to_content_type.get(
                getattr(decorator, "id", getattr(decorator, "attr", ""))
            ):
                return content_type, el_lineno

        return ContentType.CUSTOM_METHOD, el_lineno

    return ContentType.UNKNOWN, element.lineno


@fixer.register(ast.ClassDef)
def visit_ClassDef(
    state: State,
    node: ast.ClassDef,
    parents: list[ast.AST],
) -> Iterable[tuple[Offset, TokenFunc]]:
    if (
        isinstance(parents[-1], ast.Module)
        and state.looks_like_models_file
        and (
            any(  # class inherit from models.Model
                is_name_attr(
                    base_node,
                    state.from_imports,
                    ("models",),
                    ("Model",),
                )
                for base_node in node.bases
            )
            or any(  # class contain a django model field declaration
                isinstance(body_node, ast.Assign)
                and isinstance(body_node.value, ast.Call)
                and isinstance(body_node.value.func, ast.Attribute)
                and getattr(body_node.value.func.value, "id", "") == "models"
                for body_node in node.body
            )
        )
    ):
        prev_element_type: ContentType | None = None
        prev_start_lineno = node.lineno
        element_types_with_range: list[tuple[ContentType, int, int]] = []
        need_reordering = False

        for element in node.body:
            curr_element_type, curr_element_start_lineno = get_element_type_with_lineno(
                element
            )
            if curr_element_type is prev_element_type:
                # Bind element of same type together.
                continue

            if curr_element_type is ContentType.UNKNOWN:
                # If we don't know the type of the element, bind it with preceding one
                # since it's where he was before anyway.
                continue

            if prev_element_type is not None:
                element_types_with_range.append(
                    (
                        prev_element_type,
                        prev_start_lineno,
                        curr_element_start_lineno - 1,
                    )
                )
                if curr_element_type < prev_element_type:
                    need_reordering = True

            prev_start_lineno = curr_element_start_lineno
            prev_element_type = curr_element_type

        if need_reordering:
            # Don't forget the last element
            element_types_with_range.append(
                (
                    prev_element_type,
                    prev_start_lineno,
                    node.end_lineno,
                )  # type: ignore[arg-type]  # ast.ClassDef always have end_lineno
            )
            yield ast_start_offset(node), partial(
                reorder_class_body,
                element_types_with_range=element_types_with_range,
            )


def reorder_class_body(
    tokens: list[Token],
    i: int,
    *,
    element_types_with_range: list[tuple[ContentType, int, int]],
) -> None:
    j = find_first_token_at_line(
        tokens,
        i,
        line=element_types_with_range[0][1],
    )
    j = reverse_consume_non_semantic_elements(tokens, j)
    new_tokens = tokens[i:j]

    element_types_to_tokens: defaultdict[ContentType, list[Token]] = defaultdict(list)
    for el_type, start_lineno, end_lineno in element_types_with_range:
        j = find_first_token_at_line(tokens, j, line=start_lineno)
        j = reverse_consume_non_semantic_elements(tokens, j)
        j = consume(tokens, j - 1, name=PHYSICAL_NEWLINE) + 1

        last_token_idx = find_first_token_at_line(tokens, j, line=end_lineno + 1)
        k = reverse_consume_non_semantic_elements(tokens, last_token_idx)
        if (
            element_types_to_tokens[el_type]
            and element_types_to_tokens[el_type][-1].name != PHYSICAL_NEWLINE
        ):
            # When merging chunks of the same ContentType, separate them with newlines.
            # This is necessary for methods definitions.
            element_types_to_tokens[el_type].append(_PHYSICAL_NEWLINE_TOKEN)
        element_types_to_tokens[el_type].extend(tokens[j:k])
        j = last_token_idx

    # Replace class body with ordered tokens.
    nb_blocks = len(element_types_to_tokens)
    for idx, (_, el_type_tokens) in enumerate(sorted(element_types_to_tokens.items())):
        if el_type_tokens[-1].name != PHYSICAL_NEWLINE and not idx + 1 == nb_blocks:
            # Ensure we have a trailing newline for every block (except the last one).
            el_type_tokens.append(_PHYSICAL_NEWLINE_TOKEN)
        new_tokens.extend(el_type_tokens)
    tokens[i:j] = new_tokens
