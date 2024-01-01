from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))


def test_noop():
    check_noop(
        """\


        """,
        settings,
    )


def test_transform_unnecessary_localtime_default():
    check_transformed(
        """\
        timezone.localtime(timezone.now())
        """,
        """\
        timezone.localtime()
        """,
        settings,
    )


def test_transform_unnecessary_localdate_default():
    check_transformed(
        """\
        timezone.localdate(timezone.now())
        """,
        """\
        timezone.localtime()
        """,
        settings,
    )


def test_transform_unnecessary_localtime_default_multiline():
    check_transformed(
        """\
        timezone.localtime(
            timezone.now()
        )
        timezone.localdate(
        timezone.now())
        """,
        """\
        timezone.localtime()
        timezone.localdate()
        """,
        settings,
    )


def test_transform_conplicated_localtime():
    check_transformed(
        """\
        timezone.make_aware(dt.datetime.now())
        """,
        """\
        timezone.localtime()
        """,
        settings,
    )
