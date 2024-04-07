from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))


def test_noop_wrong_chain_order():
    check_noop(
        """\
        MyModel.objects.select_related("category", "best_article__category")
        """,
        settings,
    )


def test_noop_single_underscore():
    check_noop(
        """\
        MyModel.objects.select_related("category", "category_name")
        """,
        settings,
    )


def test_transform():
    check_transformed(
        """\
        MyModel.objects.select_related("category", "category__best_article")
        """,
        """\
        MyModel.objects.select_related("category__best_article")
        """,
        settings,
    )


def test_transform_three_level():
    check_transformed(
        """\
        MyModel.objects.select_related( # Comment
            "category__best_article",
            "category__best_article__author",
            "category",
        )
        """,
        """\
        MyModel.objects.select_related( # Comment
            "category__best_article__author"
        )
        """,
        settings,
    )


def test_transform_multiline():
    check_transformed(
        """\
        MyModel.objects.select_related(
            "variables__variablevalues",
            "category",
            "category__best_article",
            "variables",
        )
        """,
        """\
        MyModel.objects.select_related(
            "variables__variablevalues",
            "category__best_article"
        )
        """,
        settings,
    )


def test_transform_mixed_line():
    check_transformed(
        """\
        MyModel.objects.select_related(  # Very important comment
            "category", "variables__bla", "category__best_article", "variables",
        )
        """,
        """\
        MyModel.objects.select_related(  # Very important comment
            "variables__bla", "category__best_article"
        )
        """,
        settings,
    )


def test_transform_mixed_line_2_args():
    check_transformed(
        """\
        MyModel.objects.select_related(  # Very important comment
            "category", "category__best_article"
        )
        """,
        """\
        MyModel.objects.select_related(  # Very important comment
            "category__best_article"
        )
        """,
        settings,
    )


def test_transform_multiline_chained_qs():
    check_transformed(
        """\
        my_model = (
            MyModel.objects.filter(identifier="aaa")
            .select_related("category", "category__best_article")
            .only(
                "identifier",
                "category_id",
                "category__best_article__id",
            )
            .first()
        )
        """,
        """\
        my_model = (
            MyModel.objects.filter(identifier="aaa")
            .select_related("category__best_article")
            .only(
                "identifier",
                "category_id",
                "category__best_article__id",
            )
            .first()
        )
        """,
        settings,
    )


def test_transform_with_var():
    check_transformed(
        """\
        to_select = "aa"
        MyModel.objects.select_related(to_select, "category", "category__best_article")
        """,
        """\
        to_select = "aa"
        MyModel.objects.select_related(to_select,"category__best_article")
        """,
        settings,
    )
