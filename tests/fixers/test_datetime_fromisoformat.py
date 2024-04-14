from __future__ import annotations

import datetime as dt

import pytest

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))

DATE_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%d %H",
    "%Y-%m-%dT%H",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S.%f",
)


def test_noop_invalid_strptime_call():
    check_noop(
        """\
        dt.datetime.strptime("2024-02-12", "%Y-%m-%d", "??").date()
        """,
        settings,
    )


def test_noop_custom_date_format():
    check_noop(
        """\
        dt.datetime.strptime("2024-02-12", "%Y/%m/%d").date()
        """,
        settings,
    )


@pytest.mark.parametrize(
    "date_format",
    DATE_FORMATS,
)
def test_safe_round_trip_naive_datetime(date_format):
    aware_datetime = dt.datetime(2024, 4, 14)
    date_string = aware_datetime.strftime(date_format)

    strptime_parsed_date = dt.datetime.strptime(date_string, date_format)
    isoformat_parsed_date = dt.datetime.fromisoformat(date_string)
    assert strptime_parsed_date == aware_datetime
    assert isoformat_parsed_date == aware_datetime


@pytest.mark.parametrize(
    "date_format",
    DATE_FORMATS,
)
def test_transform_datetime_single_line(date_format):
    check_transformed(
        f"""\
        import datetime as dt
        dt.datetime.strptime(date_string, {date_format!r})
        """,
        """\
        import datetime as dt
        dt.datetime.fromisoformat(date_string)
        """,
        settings,
    )


def test_transform_date_single_line():
    check_transformed(
        """\
        import datetime as dt
        dt.datetime.strptime("2024-02-12", "%Y-%m-%d").date()  # Date conversion
        """,
        """\
        import datetime as dt
        dt.date.fromisoformat("2024-02-12")  # Date conversion
        """,
        settings,
    )


def test_transform_mixed_line():
    check_transformed(
        """\
        import datetime as dt
        end_date=dt.datetime.strptime(
            "2024-02-12", "%Y-%m-%d"
        ).date()
        """,
        """\
        import datetime as dt
        end_date=dt.date.fromisoformat(
            "2024-02-12"
        )
        """,
        settings,
    )


def test_transform_multiline():
    check_transformed(
        """\
        import datetime as dt
        end_date=dt.datetime.strptime(
            "2024-02-12",
            "%Y-%m-%d",
        ).date()
        """,
        """\
        import datetime as dt
        end_date=dt.date.fromisoformat(
            "2024-02-12"
        )
        """,
        settings,
    )


# @pytest.mark.skip(reason="TODO: improve remove_arg to keep comments")
# def test_transform_mixed_line_with_comments():
#     check_transformed(
#         """\
#         import datetime as dt
#         dt.datetime.strptime( # comment 1
#             # comment 2
#             "2024-02-12", "%Y-%m-%d" # comment 3
#             # comment 4
#         ).date() # comment 5
#         """,
#         """\
#         import datetime as dt
#         dt.date.fromisoformat( # comment 1
#             # comment 2
#             "2024-02-12" # comment 3
#             # comment 4
#         ) # comment 5
#         """,
#         settings,
#     )
#
#
# @pytest.mark.skip(reason="TODO: improve remove_arg to keep comments")
# def test_transform_multiline_with_comments():
#     check_transformed(
#         """\
#         import datetime as dt
#         dt.datetime.strptime( # comment 1
#             # comment 2
#             # comment 3
#             "2024-02-12", # comment 4
#             # comment 5
#             "%Y-%m-%d" # comment 6
#             # comment 7
#         ).date() # comment 8
#         """,
#         """\
#         import datetime as dt
#         dt.datetime.strptime( # comment 1
#             # comment 2
#             # comment 3
#             "2024-02-12", # comment 4
#             # comment 5
#             # comment 7
#         ).date() # comment 8
#         """,
#         settings,
#     )
