from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))


def test_noop_specific_date():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt

        timezone.localtime(timezone.make_aware(dt.datetime(2022, 1, 1)))
        my_date = timezone.make_aware(dt.datetime(2022, 1, 1))
        timezone.localdate(my_date)
        """,
        settings,
    )


def test_noop_full_datetime_import():
    check_noop(
        """\
        from django.utils import timezone
        from datetime.datetime import now

        timezone.make_aware(now())
        """,
        settings,
    )


def test_noop_other_module_now():
    check_noop(
        """\
        from django.utils import timezone
        import foo

        timezone.make_aware(foo.now())
        """,
        settings,
    )


def test_noop_other_default():
    check_noop(
        """\
        from django.utils import timezone
        from foo import now

        timezone.make_aware(now())
        """,
        settings,
    )


def test_missing_imports():
    check_noop(
        """\
        localtime(now())
        """,
        settings,
    )


def test_transform_unnecessary_localtime_default():
    check_transformed(
        """\
        from django.utils import timezone

        timezone.localtime(timezone.now())
        """,
        """\
        from django.utils import timezone

        timezone.localtime()
        """,
        settings,
    )


def test_transform_unnecessary_localtime_default_full_import():
    check_transformed(
        """\
        from django.utils.timezone import localtime, now

        localtime(now())
        """,
        """\
        from django.utils.timezone import localtime, now

        localtime()
        """,
        settings,
    )


def test_transform_unnecessary_localdate_default():
    check_transformed(
        """\
        from django.utils import timezone

        timezone.localdate(timezone.now())
        """,
        """\
        from django.utils import timezone

        timezone.localdate()
        """,
        settings,
    )


def test_transform_unnecessary_localtime_default_multiline():
    check_transformed(
        """\
        from django.utils import timezone

        timezone.localtime(
            timezone.now()
        )
        timezone.localdate(
        timezone.now())
        """,
        """\
        from django.utils import timezone

        timezone.localtime()
        timezone.localdate()
        """,
        settings,
    )


def test_transform_localdate_instead_of_localtime():
    check_transformed(
        """\
        from django.utils import timezone

        timezone.localtime(timezone.now()).date()
        timezone.localtime().date()
        """,
        """\
        from django.utils import timezone

        timezone.localdate()
        timezone.localdate()
        """,
        settings,
    )


def test_transform_localdate_instead_of_localtime_with_date():
    check_transformed(
        """\
        from django.utils import timezone
        import datetime as dt

        timezone.localtime(timezone.make_aware(dt.datetime(2022, 1, 1))).date()
        """,
        """\
        from django.utils import timezone
        import datetime as dt

        timezone.localdate(timezone.make_aware(dt.datetime(2022, 1, 1)))
        """,
        settings,
    )


def test_transform_overcomplicated_localtime_dt_datetime():
    check_transformed(
        """\
        from django.utils import timezone
        import datetime as dt

        timezone.make_aware(dt.datetime.now())
        """,
        """\
        from django.utils import timezone
        import datetime as dt

        timezone.localtime()
        """,
        settings,
    )


def test_transform_overcomplicated_localtime_datetime():
    check_transformed(
        """\
        from django.utils import timezone
        from datetime import datetime

        timezone.make_aware(datetime.now())
        """,
        """\
        from django.utils import timezone
        from datetime import datetime

        timezone.localtime()
        """,
        settings,
    )
