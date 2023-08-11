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
from django_upgrade.data import Fixer
from django_upgrade.data import State
from django_upgrade.data import TokenFunc
from django_upgrade.tokens import consume
from django_upgrade.tokens import find_first_token_at_line
from django_upgrade.tokens import find_last_token_at_line
from django_upgrade.tokens import PHYSICAL_NEWLINE
from django_upgrade.tokens import reverse_consume_non_semantic_elements

fixer = Fixer(
    __name__,
    min_version=(0, 0),
)


class ContentType(int, enum.Enum):
    """Enumeration of possible types of block in a django class"""

    UNKNOWN = 0
    BARE_ANNOTATION = 1
    FIELD_DECLARATION = 2
    MANAGER_DECLARATION = 3
    META_CLASS = 4
    STR_METHOD = 5
    CLEAN_METHOD = 6
    SAVE_METHOD = 7
    GET_ABSOLUTE_URL_METHOD = 8
    CUSTOM_PROPERTY = 9
    CUSTOM_METHOD = 10
    CUSTOM_CLASS_METHOD = 11
    CUSTOM_STATIC_METHOD = 12


decorator_to_content_type = {
    "property": ContentType.CUSTOM_PROPERTY,
    "cached_property": ContentType.CUSTOM_PROPERTY,
    "setter": ContentType.CUSTOM_PROPERTY,
    "deleter": ContentType.CUSTOM_PROPERTY,
    "classmethod": ContentType.CUSTOM_CLASS_METHOD,
    "staticmethod": ContentType.CUSTOM_STATIC_METHOD,
}


def get_element_type_with_lineno(
    element: ast.AST,
) -> tuple[ContentType, int]:
    if isinstance(element, ast.Assign):
        if getattr(element.targets[0], "id", "") == "objects" or (
            isinstance(element.value, ast.Call)
            and "Manager"
            in getattr(element.value.func, "id", "")  # TODO: could be endswith check ?
        ):
            # Because Manager definition order in the class matter, it is not a
            # safe idea to try distinguishing the `object` manager from other ones.
            # https://docs.djangoproject.com/fr/4.2/topics/db/managers/#default-managers
            return ContentType.MANAGER_DECLARATION, element.lineno

        if isinstance(element.targets[0], ast.Name):
            return ContentType.FIELD_DECLARATION, element.lineno

    if isinstance(element, ast.ClassDef) and element.name == "Meta":
        return ContentType.META_CLASS, element.lineno

    if isinstance(element, ast.FunctionDef):
        el_lineno = element.lineno - len(element.decorator_list)
        if element.name == "__str__":
            return ContentType.STR_METHOD, el_lineno
        elif element.name == "save":
            return ContentType.SAVE_METHOD, el_lineno
        elif element.name == "get_absolute_url":
            return ContentType.GET_ABSOLUTE_URL_METHOD, el_lineno
        elif element.name == "clean":
            return ContentType.CLEAN_METHOD, el_lineno
        else:
            if any(
                (dec_name := getattr(decorator, "id", getattr(decorator, "attr", "")))
                in decorator_to_content_type.keys()
                for decorator in element.decorator_list
            ):
                return decorator_to_content_type[dec_name], el_lineno

            return ContentType.CUSTOM_METHOD, el_lineno

    if isinstance(element, ast.AnnAssign):
        if getattr(element.target, "id", "") == "objects":
            return ContentType.MANAGER_DECLARATION, element.lineno
        if isinstance(element.target, ast.Name):
            return ContentType.FIELD_DECLARATION, element.lineno
        if element.value is None:
            return ContentType.BARE_ANNOTATION, element.lineno
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
        element_types: list[ContentType] = []
        prev_element_type: ContentType | None = None
        element_types_to_range: list[tuple[int, int, ContentType]] = []
        start_lineno = node.lineno
        need_reordering = False

        for element in node.body:
            element_type, element_start_lineno = get_element_type_with_lineno(element)
            if element_type is ContentType.UNKNOWN:
                continue

            if prev_element_type == element_type:
                continue

            if prev_element_type is not None:
                element_types_to_range.append(
                    (start_lineno, element_start_lineno - 1, prev_element_type)
                )

            start_lineno = element_start_lineno
            prev_element_type = element_type

            if any(element_type < prev_element for prev_element in element_types):
                need_reordering = True
            else:
                element_types.append(element_type)

        if need_reordering:
            # if False:
            #     yield
            element_types_to_range.append(  # Don't forget the last element
                (
                    start_lineno,
                    node.end_lineno,
                    prev_element_type,
                )  # type: ignore[arg-type]  #ast.ClassDef always have end_lineno
            )
            yield ast_start_offset(node), partial(
                reorder_class_body,
                element_types_to_range=element_types_to_range,
            )


def reorder_class_body(
    tokens: list[Token],
    i: int,
    *,
    element_types_to_range: list[tuple[int, int, ContentType]],
) -> None:
    element_types_to_tokens: defaultdict[ContentType, list[Token]] = defaultdict(list)

    j = (
        find_last_token_at_line(
            tokens, i, line=next(iter(element_types_to_range))[0] - 1
        )
        + 1
    )
    j = reverse_consume_non_semantic_elements(tokens, j)
    new_tokens = tokens[i:j]

    for start, end, el_type in element_types_to_range:
        j = find_first_token_at_line(tokens, j, line=start)
        j = reverse_consume_non_semantic_elements(tokens, j)
        j = consume(tokens, j - 1, name=PHYSICAL_NEWLINE) + 1

        last_token_idx = find_last_token_at_line(tokens, j, line=end) + 1
        k = reverse_consume_non_semantic_elements(tokens, last_token_idx)
        if (
            element_types_to_tokens[el_type]
            and element_types_to_tokens[el_type][-1].name != PHYSICAL_NEWLINE
        ):
            # Separate chunks of the same ContentType with newlines.
            # It is usefull for most but not really for Field and Manager declarations.
            # TODO: maybe special case here ?
            element_types_to_tokens[el_type].append(
                Token(name=PHYSICAL_NEWLINE, src="\n")
            )
        element_types_to_tokens[el_type].extend(tokens[j:k])
        j = last_token_idx

    # Replace class body with ordered tokens.
    nb_blocks = len(element_types_to_tokens)
    for idx, (_, el_type_tokens) in enumerate(sorted(element_types_to_tokens.items())):
        if el_type_tokens[-1].name != PHYSICAL_NEWLINE and not idx == nb_blocks - 1:
            # Ensure we have a trailing newline for every block (except the last one).
            el_type_tokens.append(Token(name=PHYSICAL_NEWLINE, src="\n"))
        new_tokens.extend(el_type_tokens)
    tokens[i:j] = new_tokens
