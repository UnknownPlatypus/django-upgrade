from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))


def test_noop_getter_with_kwargs():
    check_noop(
        """\
        queryset.values("id").get(name="a")["id"]
        """,
        settings,
    )


def test_noop_getter_with_args():
    check_noop(
        """\
        queryset.values("id").latest("name")["id"]
        """,
        settings,
    )


def test_transform_first():
    check_transformed(
        """\
        queryset.values("id").first()["id"]
        """,
        """\
        queryset.values_list("id", flat=True).first()
        """,
        settings,
    )


def test_transform_last():
    check_transformed(
        """\
        queryset.values("id").last()["id"]
        """,
        """\
        queryset.values_list("id", flat=True).last()
        """,
        settings,
    )


def test_transform_get():
    check_transformed(
        """\
        queryset.values("id").get()["id"]
        """,
        """\
        queryset.values_list("id", flat=True).get()
        """,
        settings,
    )


def test_transform_multiple():
    check_transformed(
        """\
        tag = (
            Tag.objects.filter(category="aaa")
            .values("tag__name")
            .first()["tag__name"]
        )
        provider_id = (
            Offer.objects.filter(id=1).values("provider_id").first()["provider_id"]
        )
        """,
        """\
        tag = (
            Tag.objects.filter(category="aaa")
            .values_list("tag__name", flat=True).first()
        )
        provider_id = (
            Offer.objects.filter(id=1).values_list("provider_id", flat=True).first()
        )
        """,
        settings,
    )


def test_transform_get_with_args():
    check_transformed(
        """\
        queryset.values("id").get(name="a")["id"]
        """,
        """\
        queryset.values_list("id", flat=True).get(name="a")
        """,
        settings,
    )
