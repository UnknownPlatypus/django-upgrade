from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(0, 0))


def test_params_generated_from_func():
    check_noop(
        """\
        @pytest.mark.parametrize(
            "due_by, expected",
            compute_params(),
            ids=[
                "Weekday - 7 minutes before start_hour - unavailable",
                "Weekday - 3 minutes before start_lunch_hour - unavailable",
            ],
        )
        def test_check_if_responder_could_be_available(due_by, expected):
            pass
        """,
        settings,
    )


def test_rewrite_tuple():
    check_transformed(
        """\
        import datetime as dt
        @pytest.mark.parametrize(
            "due_by, expected",
            [
                # Week day
                (dt.date(2022, 5, 1), False),
                (dt.date(2022, 5, 1), True),
                (dt.date(2022, 5, 1), True),
                # Saturday
                (dt.date(2022, 5, 1), False),
            ],
            ids=[
                "Weekday - 7 minutes",
                "Weekday - 3 minutes",
                "Weekday - 9 minutes",
                "Weekday - 3 minutes",
            ],
        )
        def test_check_if_responder_could_be_available(due_by, expected):
            pass
        """,
        """\
        import datetime as dt
        @pytest.mark.parametrize(
            "due_by, expected",
            [
                # Week day
                pytest.param(dt.date(2022, 5, 1), False, id="Weekday - 7 minutes"),
                pytest.param(dt.date(2022, 5, 1), True, id="Weekday - 3 minutes"),
                pytest.param(dt.date(2022, 5, 1), True, id="Weekday - 9 minutes"),
                # Saturday
                pytest.param(dt.date(2022, 5, 1), False, id="Weekday - 3 minutes"),
            ],
        )
        def test_check_if_responder_could_be_available(due_by, expected):
            pass
        """,
        settings,
    )


def test_rewrite_list():
    check_transformed(
        """\
        import datetime as dt
        @pytest.mark.parametrize(
            "due_by, expected",
            [
                # Week day
                [dt.date(2022, 5, 1), False],
                [dt.date(2022, 5, 1), True],
                [dt.date(2022, 5, 1), True],
                # Saturday
                [dt.date(2022, 5, 1), False],
            ],
            ids=[
                "Weekday - 7 minutes",
                "Weekday - 3 minutes",
                "Weekday - 9 minutes",
                "Weekday - 3 minutes",
            ],
        )
        def test_check_if_responder_could_be_available(due_by, expected):
            pass
        """,
        """\
        import datetime as dt
        @pytest.mark.parametrize(
            "due_by, expected",
            [
                # Week day
                pytest.param(dt.date(2022, 5, 1), False, id="Weekday - 7 minutes"),
                pytest.param(dt.date(2022, 5, 1), True, id="Weekday - 3 minutes"),
                pytest.param(dt.date(2022, 5, 1), True, id="Weekday - 9 minutes"),
                # Saturday
                pytest.param(dt.date(2022, 5, 1), False, id="Weekday - 3 minutes"),
            ],
        )
        def test_check_if_responder_could_be_available(due_by, expected):
            pass
        """,
        settings,
    )


def test_rewrite_multiline():
    check_transformed(
        """\
        import datetime as dt
        @pytest.mark.parametrize(
            "due_by, expected",
            [
                # Week day
                [
                    dt.date(2022, 5, 1),
                    False,
                ],
                [
                    dt.date(2022, 5, 1),
                    True,
                ],
            ],
            ids=[
                "Weekday - 7 minutes",
                "Weekday - 3 minutes",
            ],
        )
        def test_check_if_responder_could_be_available(due_by, expected):
            pass
        """,
        """\
        import datetime as dt
        @pytest.mark.parametrize(
            "due_by, expected",
            [
                # Week day
                pytest.param(
                    dt.date(2022, 5, 1),
                    False,
                id="Weekday - 7 minutes"),
                pytest.param(
                    dt.date(2022, 5, 1),
                    True,
                id="Weekday - 3 minutes"),
            ],
        )
        def test_check_if_responder_could_be_available(due_by, expected):
            pass
        """,
        settings,
    )


def test_rewrite_single_arg():
    check_transformed(
        """\
        @pytest.mark.parametrize(
            "events_data",
            [
                [1, 2],
                [],
            ],
            ids=[
                "2 events",
                "No events",
            ],
        )
        def test_thing(events_data, expected):
            pass
        """,
        """\
        @pytest.mark.parametrize(
            "events_data",
            [
                pytest.param(1, 2, id="2 events"),
                pytest.param(id="No events"),
            ],
        )
        def test_thing(events_data, expected):
            pass
        """,
        settings,
    )
