from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))


def test_noop_not_constant():
    check_noop(
        r"""
        DATE_FORMAT = "%Y"
        b = f"{dt.datetime.now().strftime(DATE_FORMAT)}"
        """,
        settings,
    )


def test_noop_empty_format():
    check_noop(
        r"""
        DATE_FORMAT = "%Y"
        b = f"{dt.datetime.now().strftime(DATE_FORMAT)}"
        """,
        settings,
    )


def test_noop_joined_str():
    check_noop(
        r"""
        f' ''{dt.datetime.now().strftime("%Y")}'''
        """,
        settings,
    )


def test_noop_other_modifier():
    check_noop(
        r"""
        f'''{dt.datetime.now().strftime("%Y")!r}'''
        """,
        settings,
    )


def test_noop_not_last_call():
    check_noop(
        r"""
        f'''{dt.datetime.now().strftime("%Y").lower()}'''
        """,
        settings,
    )


def test_transform_single_quote():
    check_transformed(
        r"""
        f'Now: {dt.datetime.now().strftime("%Y-%m-%d")}'
        """,
        r"""
        f'Now: {dt.datetime.now():%Y-%m-%d}'
        """,
        settings,
    )


def test_transform_double_quote():
    check_transformed(
        r"""
        f"Now: {dt.datetime.now().strftime('%Y-%m-%d')}"
        """,
        r"""
        f"Now: {dt.datetime.now():%Y-%m-%d}"
        """,
        settings,
    )


def test_transform_single_quote_rf():
    check_transformed(
        r"""
        rf'Now: {dt.datetime.now().strftime("%Y-%m-%d")}'
        """,
        r"""
        rf'Now: {dt.datetime.now():%Y-%m-%d}'
        """,
        settings,
    )


def test_transform_double_quote_rf():
    check_transformed(
        r"""
        fr"Now: {dt.datetime.now().strftime('%Y-%m-%d')}"
        """,
        r"""
        fr"Now: {dt.datetime.now():%Y-%m-%d}"
        """,
        settings,
    )


def test_transform_triple_quoted_string():
    check_transformed(
        r"""
        f'''{dt.datetime.now().strftime("%Y")}'''
        f'''       {dt.datetime.now().strftime("%Y")}     '''
        f'''{dt.datetime.now().strftime("%Y")}     '''
        """,
        r"""
        f'''{dt.datetime.now():%Y}'''
        f'''       {dt.datetime.now():%Y}     '''
        f'''{dt.datetime.now():%Y}     '''
        """,
        settings,
    )


def test_transform_multiple_pattern():
    check_transformed(
        r"""
        now = dt.datetime.now()
        f"Now: {now.strftime('%Y-%m-%d')}, Now 2: {now.strftime('%Y-%m-%d')}"
        """,
        r"""
        now = dt.datetime.now()
        f"Now: {now:%Y-%m-%d}, Now 2: {now:%Y-%m-%d}"
        """,
        settings,
    )


def test_transform_weird_pattern_with_spaces():
    check_transformed(
        r"""
        f"Now: {dt.datetime.now().strftime('%d/%m/%Y after %H:%M')}"
        """,
        r"""
        f"Now: {dt.datetime.now():%d/%m/%Y after %H:%M}"
        """,
        settings,
    )
