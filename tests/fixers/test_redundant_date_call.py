from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))


def test_noop_localtime_without_date():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt

        timezone.localtime() - dt.timedelta(days=365)
        """,
        settings,
    )


def test_noop_date_without_localtime():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt

        some_date.date() - dt.timedelta(days=365)
        """,
        settings,
    )


def test_noop_with_unknown_type():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt
        import foo
        import bar

        (timezone.localtime() - foo).date()
        (timezone.localtime() - bar.foo()).date()
        """,
        settings,
    )


def test_noop_invalid_bin_op():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt

        (timezone.localtime() * dt.timedelta(days=365)).date()
        (timezone.localtime() ^ dt.timedelta(days=365)).date()
        (timezone.localtime() | dt.timedelta(days=365)).date()
        """,
        settings,
    )


def test_noop_lower_than_day_timedelta_kwargs():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt

        (timezone.localtime() + dt.timedelta(minutes=30)).date()
        """,
        settings,
    )


def test_noop_lower_than_day_timedelta_args():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt

        (timezone.localtime() + dt.timedelta(1, 1, 1, 30)).date()
        """,
        settings,
    )


def test_noop_lower_than_day_timedelta_mixed():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt

        (timezone.localtime() + dt.timedelta(1, minute=1, second=1, microsecond=30)).date()
        """,
        settings,
    )


def test_transform_weird_timedelta():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt
        dt = other

        (timezone.localtime() - other.timedelta(days=365)).date()
        """,
        settings,
    )


def test_noop_invalid_sub_bin_op():
    check_noop(
        """\
        from django.utils import timezone
        import datetime as dt

        (timezone.localtime() + dt.timedelta(minutes=30)).date()
        """,
        settings,
    )


def test_transform_single_line_sub_bin_op():
    check_transformed(
        """\
        from django.utils import timezone
        import datetime as dt

        (timezone.localtime() - dt.timedelta(days=365)).date()
        """,
        """\
        from django.utils import timezone
        import datetime as dt

        (timezone.localdate() - dt.timedelta(days=365))
        """,
        settings,
    )


def test_transform_single_line_add_bin_op():
    check_transformed(
        """\
        from django.utils import timezone
        import datetime as dt

        (timezone.localtime() + dt.timedelta(days=365)).date()
        """,
        """\
        from django.utils import timezone
        import datetime as dt

        (timezone.localdate() + dt.timedelta(days=365))
        """,
        settings,
    )


def test_transform_single_line_add_bin_op_reversed():
    check_transformed(
        """\
        from django.utils import timezone
        import datetime as dt

        (dt.timedelta(days=365) + timezone.localtime()).date()
        """,
        """\
        from django.utils import timezone
        import datetime as dt

        (dt.timedelta(days=365) + timezone.localdate())
        """,
        settings,
    )


def test_transform_single_line_sub_bin_op_with_spaces():
    check_transformed(
        """\
        from django.utils import timezone
        import datetime as dt

        ( timezone.localtime() - dt.timedelta(days=365) ).date()
        """,
        """\
        from django.utils import timezone
        import datetime as dt

        ( timezone.localdate() - dt.timedelta(days=365) )
        """,
        settings,
    )


def test_transform_multi_line():
    check_transformed(
        """\
        from django.utils import timezone
        import datetime as dt

        (
            timezone.localtime() - dt.timedelta(days=365)
        ).date()
        """,
        """\
        from django.utils import timezone
        import datetime as dt

        (
            timezone.localdate() - dt.timedelta(days=365)
        )
        """,
        settings,
    )


def test_transform_nested_parentheses():
    check_transformed(
        """\
        from django.utils import timezone
        import datetime as dt

        ((timezone.localtime() - dt.timedelta(days=365)).date())
        """,
        """\
        from django.utils import timezone
        import datetime as dt

        ((timezone.localdate() - dt.timedelta(days=365)))
        """,
        settings,
    )


def test_transform_in_assignment():
    check_transformed(
        """\
        from django.utils import timezone
        import datetime as dt

        x = (timezone.localtime() - dt.timedelta(days=365)).date()
        """,
        """\
        from django.utils import timezone
        import datetime as dt

        x = (timezone.localdate() - dt.timedelta(days=365))
        """,
        settings,
    )
