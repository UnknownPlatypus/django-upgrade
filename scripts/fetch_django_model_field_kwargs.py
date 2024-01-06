"""Clone every supported version of django locally.

This is used to introspect field definitions.
"""
from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path
from typing import Sequence

from django_upgrade.main import TARGET_VERSION_CHOICES

_DJANGO_GIT_URL = "https://github.com/django/django"
_CLONE_TARGET_DIR = Path.cwd() / ".django"
_DJANGO_MODEL_FIELD_FILE = _CLONE_TARGET_DIR / "django/db/models/fields/__init__.py"
_DJANGO_FIELD_ORDER_CONST_FILE = "src/django_upgrade/field_order_const.py"


class NV(ast.NodeVisitor):
    __slots__ = ("args_by_field",)

    args_by_field: dict[str, list[str]]

    def visit_Assign(self, node: ast.Assign) -> None:
        if getattr(node.targets[0], "id", "") == "__all__":
            if isinstance(node.value, (ast.List, ast.Tuple)):
                item_list = node.value.elts
            elif isinstance(node.value, ast.ListComp) and isinstance(
                node.value.generators[0].iter, (ast.List, ast.Tuple)
            ):
                item_list = node.value.generators[0].iter.elts
            else:
                raise AssertionError("Unreachable")

            self.args_by_field = {
                item.value: []
                for item in item_list
                if isinstance(item, ast.Constant) and item.value.endswith("Field")
            }

        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if node.name.endswith("Field") and any(
            isinstance(body_node, ast.FunctionDef)
            and (target_node := body_node).name == "__init__"
            for body_node in node.body
        ):
            if node.name in self.args_by_field:
                self.args_by_field[node.name].extend(
                    arg.arg
                    for arg in target_node.args.args[1:]  # Skip "self" first argument
                )
                self.args_by_field[node.name].extend(
                    arg.arg for arg in target_node.args.kwonlyargs
                )

        self.generic_visit(node)


def git_clone_branches(*, repo: str, target_dir: Path, branches: list[str]) -> None:
    """Shallow clone this repository to a temporary directory."""
    print(f"Cloning {repo}...")

    subprocess.run(
        [
            "git",
            "clone",
            "--config",
            "advice.detachedHead=false",
            "--quiet",
            "--depth",
            "1",
            "--no-tags",
            "--branch",
            branches[0],
            repo,
            target_dir,
        ],
        check=False,
    )
    print(f"Finished cloning {repo}")

    for branch_name in branches[1:]:
        print(f"Fetching branch {branch_name}...")
        subprocess.run(
            [
                "git",
                "fetch",
                "origin",
                f"{branch_name}:{branch_name}",
                "--depth",
                "1",
            ],
            cwd=target_dir,
            check=True,
        )


def _get_branches() -> list[str]:
    """Get branches to fetch from possible target version"""
    return [f"stable/{django_version}.x" for django_version in TARGET_VERSION_CHOICES]


def parse_field_args() -> dict[str, list[str]]:
    """Parse django field __init__ file and collect argument order"""
    with open(_DJANGO_MODEL_FIELD_FILE) as f:
        visitor = NV()
        visitor.visit(ast.parse(f.read()))
    return visitor.args_by_field


def get_ordered_full_kw_list(args_by_field: dict[str, list[str]]) -> list[str]:
    """
    Build a unified list of arg name respecting
    argument order for every type of field
    """
    ref_list = list(args_by_field.pop("Field"))
    for args in args_by_field.values():
        for arg_name in args:
            if arg_name not in ref_list:
                ref_list.append(arg_name)
    return ref_list


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--force-clone", action="store_true", default=False)
    args = parser.parse_args(argv)

    if args.force_clone or not _CLONE_TARGET_DIR.exists():
        git_clone_branches(
            repo=_DJANGO_GIT_URL, target_dir=_CLONE_TARGET_DIR, branches=_get_branches()
        )
    else:
        print(f"Using cloned django at {_CLONE_TARGET_DIR}")

    output_dict = {}
    for target_version, git_branch in zip(TARGET_VERSION_CHOICES, _get_branches()):
        print(f"Git checkout {git_branch}...")
        subprocess.run(
            ["git", "checkout", git_branch], cwd=_CLONE_TARGET_DIR, check=True
        )
        print(f"Parsing model field args for {git_branch}...")
        args_by_field = parse_field_args()
        output_dict[
            tuple(int(part) for part in target_version.split("."))
        ] = get_ordered_full_kw_list(args_by_field)

    # Keep list only for non-backward compatible versions.
    versions_to_keep = set()
    django_version = list(output_dict.items())[0][0]
    for current_version, arg_list in list(output_dict.items())[1:]:
        removed_fields = set(output_dict[django_version]) - set(arg_list)
        print(f"{django_version} -> {current_version}: removed_fields={removed_fields}")
        if removed_fields:
            versions_to_keep.add(django_version)
        django_version = current_version
    versions_to_keep.add(django_version)

    if len(versions_to_keep) > 1:
        output: dict[tuple[int, ...], list[str]] | list[str] = {
            k: v for k, v in output_dict.items() if k in versions_to_keep
        }
    else:
        output = output_dict[versions_to_keep.pop()]

    with open(_DJANGO_FIELD_ORDER_CONST_FILE, "w") as f:
        f.write(f"from __future__ import annotations\nMODEL_FIELD_ARG_ORDER={output}")

    print("Formatting using black...")
    subprocess.run(
        [
            "pre-commit",
            "run",
            "black",
            "--files",
            _DJANGO_FIELD_ORDER_CONST_FILE,
        ],
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
