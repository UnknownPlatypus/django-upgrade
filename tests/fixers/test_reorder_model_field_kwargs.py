from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(0, 0))


def test_noop_not_a_model_file():
    check_noop(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(max_length=100, verbose_name="")
        """,
        settings,
    )


def test_noop_single_kwarg():
    check_noop(
        """\
        from django.db import models

        class Comment(models.Model):
            one_kwarg = models.EmailField(verbose_name="Author Name")

        """,
        settings,
        filename="models.py",
    )


def test_noop_single_kwarg_with_args():
    check_noop(
        """\
        from django.db import models

        class Comment(models.Model):
            one_kwarg = models.EmailField("verbose_name", "name", null=True)
        """,
        settings,
        filename="models.py",
    )


def test_noop_ordered_kwarg():
    check_noop(
        """\
        from django.db import models

        class Comment(models.Model):
            ordered = models.BooleanField(
                verbose_name="",
                default=False,
            )
            also_ordered = models.BooleanField(verbose_name="",null=True, default=False)
        """,
        settings,
        filename="models.py",
    )


def test_noop_ordered_kwarg_with_args():
    check_noop(
        """\
        from django.db import models

        class Comment(models.Model):
            ordered = models.BooleanField(
                "verbose_name",
                "name",
                blank=True,
                default=False,
            )
            also_ordered = models.BooleanField("verbose_name", null=True, default=False)

        """,
        settings,
        filename="models.py",
    )


def test_noop_only_custom_kwarg():
    check_noop(
        """\
        from django.db import models

        class Comment(models.Model):
            one_kwarg = models.CustomEmailField("Author Name", tartine=100, turlu=100)
        """,
        settings,
        filename="models.py",
    )


def test_transform_custom_kwarg():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            one_kwarg = models.CustomEmailField(turlu=100, verbose_name="Author Name")
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            one_kwarg = models.CustomEmailField(verbose_name="Author Name", turlu=100)
        """,
        settings,
        filename="models.py",
    )


def test_transform_single_line_without_comment():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(max_length=100, verbose_name="")
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(verbose_name="", max_length=100)
        """,
        settings,
        filename="models.py",
    )


def test_transform_single_line_with_comment():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(max_length=100, verbose_name="") # TODO
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(verbose_name="", max_length=100) # TODO
        """,
        settings,
        filename="models.py",
    )


def test_transform_single_line_weird_spaces_with_comment():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(max_length=100    ,    verbose_name="") # TODO
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(verbose_name="", max_length=100) # TODO
        """,
        settings,
        filename="models.py",
    )


def test_transform_wrapped_single_line_without_comment():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                max_length=100,  verbose_name="Bad ordering"
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                verbose_name="Bad ordering", max_length=100
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_wrapped_single_line_with_comment():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                max_length=100, verbose_name="Bad ordering" # TODO: verbose_name
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                verbose_name="Bad ordering", max_length=100 # TODO: verbose_name
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_wrapped_single_line_with_comment_and_trailing_comma():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                max_length=100, verbose_name="Bad ordering", # TODO: verbose_name
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                verbose_name="Bad ordering", max_length=100 # TODO: verbose_name
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_wrapped_single_line_without_comment_with_trailing_comma():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                max_length=100, verbose_name="Bad ordering",
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                verbose_name="Bad ordering", max_length=100
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_wrapped_single_line_unusual_kwargs():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            created_at = models.DateTimeField(
                auto_now_add=True, verbose_name="Date de création"
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            created_at = models.DateTimeField(
                verbose_name="Date de création", auto_now_add=True
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_mixedline_with_comment():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_multiline = models.CharField(max_length=100,
                verbose_name="Status", # verbose
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_multiline = models.CharField(verbose_name="Status", # verbose
        max_length=100,
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_small():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                max_length=100, help_text="Bad ordering", verbose_name=_(
                    "Some help text about this charfield"
                ),
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                verbose_name=_(
                    "Some help text about this charfield"
                ),
                max_length=100,
                help_text="Bad ordering",
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_with_comments():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField( # comment 0
                # comment 1.1
                # comment 1.2
                help_text="Some help text about this charfield", # comment 2
                verbose_name="Bad ordering", # comment 3
                max_length=100, # comment 4
                # comment 5
            ) # comment 6
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField( # comment 0
                verbose_name="Bad ordering", # comment 3
                max_length=100, # comment 4
                # comment 1.1
                # comment 1.2
                help_text="Some help text about this charfield", # comment 2
                # comment 5
            ) # comment 6
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_without_comments():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_multiline = models.CharField(
                max_length=100,
                choices=CommentStatus.choices,
                verbose_name="Status",
                help_text=_(
                    "Some help text about this charfield"
                ),
                default="PENDING",
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_multiline = models.CharField(
                verbose_name="Status",
                max_length=100,
                default="PENDING",
                choices=CommentStatus.choices,
                help_text=_(
                    "Some help text about this charfield"
                ),
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_weird_format():
    check_transformed(
        """\
        from django.db import models

        class Comment():
            bad_order = models.CharField(  max_length=100,  # comment 2
                verbose_name="Bad ordering",  # comment 3
                help_text="Some help text about this charfield", )  # comment 6
        """,
        """\
        from django.db import models

        class Comment():
            bad_order = models.CharField(  verbose_name="Bad ordering",  # comment 3
          max_length=100,  # comment 2
          help_text="Some help text about this charfield",
        )  # comment 6
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_with_no_trailing_comma():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_multiline = models.CharField(
                default="PENDING",
                max_length=100
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_multiline = models.CharField(
                max_length=100,
                default="PENDING",
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_with_weird_end():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_multiline = models.CharField(
                choices=CommentStatus.choices,
                help_text="Status",
                max_length=100,
                default="PENDING",
                verbose_name=_(
                    "Some help text about this charfield"
                ),)
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_multiline = models.CharField(
                verbose_name=_(
                    "Some help text about this charfield"
                ),
                max_length=100,
                default="PENDING",
                choices=CommentStatus.choices,
                help_text="Status",
        )
        """,
        settings,
        filename="models.py",
    )


def test_transform_single_line_ambiguous_parenthesis():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            test = models.CharField(db_comment=("charfield"), default="p",)
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            test = models.CharField(default="p", db_comment=("charfield"))
        """,
        settings,
        filename="models.py",
    )


def test_transform_mixed_line_ambiguous_parenthesis():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_mixed_line = models.CharField(
                db_comment=("charfield"), default="p",
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order_mixed_line = models.CharField(
                default="p", db_comment=("charfield")
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_with_multiline_string_literal_end():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            val = models.CharField(
                auto_created=False,
                db_column=(
                    "db_column_name"
                )
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            val = models.CharField(
                db_column=(
                    "db_column_name"
                ),
                auto_created=False,
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_with_multiline_string_literal_end_with_comma():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            val = models.CharField(
                auto_created=False,
                db_column=(
                    "db_column_name"
                ),
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            val = models.CharField(
                db_column=(
                    "db_column_name"
                ),
                auto_created=False,
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_with_multiline_string_literal_end_list():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            val = models.CharField(
                verbose_name="Nouvel identifiant freshdesk du Contact",
                auto_created=False,
                db_column=[
                    "db_column_name"
                ]
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            val = models.CharField(
                verbose_name="Nouvel identifiant freshdesk du Contact",
                db_column=[
                    "db_column_name"
                ],
                auto_created=False,
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_with_multiline_string_literal_middle():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            val = models.CharField(
                verbose_name="Nouvel identifiant freshdesk du Contact",
                db_column=(
                    "db_column_name"
                ),
                max_length=15,
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            val = models.CharField(
                verbose_name="Nouvel identifiant freshdesk du Contact",
                max_length=15,
                db_column=(
                    "db_column_name"
                ),
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_single_line_with_arg():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField("Bad", unique=True, max_length=100) # TODO
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField("Bad", max_length=100, unique=True) # TODO
        """,
        settings,
        filename="models.py",
    )


def test_transform_wrapped_single_line_with_arg():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                "Bad ordering", unique=True, max_length=100 # TODO
            )
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField(
                "Bad ordering", max_length=100, unique=True # TODO
            )
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_with_arg():
    check_transformed(
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField( # comment 0
                # comment 1
                "verbose_name",
                # comment 2
                help_text="Some help text about this charfield", # comment 3
                default="Bad ordering", # comment 4
                max_length=100, # comment 5
                # comment 6
            ) # comment 7
        """,
        """\
        from django.db import models

        class Comment(models.Model):
            bad_order = models.CharField( # comment 0
                # comment 1
                "verbose_name",
                max_length=100, # comment 5
                default="Bad ordering", # comment 4
                # comment 2
                help_text="Some help text about this charfield", # comment 3
                # comment 6
            ) # comment 7
        """,
        settings,
        filename="models.py",
    )


def test_transform_multiline_with_arg_weird_format():
    check_transformed(
        """\
        from django.db import models

        class Comment():
            bad_order = models.CharField(  "verbose_name",  # comment 1
                "name", db_comment = "A DB comment", # comment 2
                help_text="Some help text about this charfield", # comment 3
            )
        """,
        """\
        from django.db import models

        class Comment():
            bad_order = models.CharField(  "verbose_name",  # comment 1
                "name", help_text="Some help text about this charfield", # comment 3
         db_comment = "A DB comment", # comment 2
            )
        """,
        settings,
        filename="models.py",
    )


def test_dangling_comment():
    check_transformed(
        """\
        from django.db import models

        class Comment():
            nb = models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                verbose_name="nb",
                # TODO 1 at least
            )
        """,
        """\
        from django.db import models

        class Comment():
            nb = models.PositiveSmallIntegerField(
                verbose_name="nb",
                blank=True,
                null=True,
                # TODO 1 at least
            )
        """,
        settings,
        filename="models.py",
    )


def test_multiline_in_between_comment():
    check_transformed(
        """\
        from django.db import models
        from django.core.validators import MinValueValidator, MaxValueValidator

        class Comment():
            nb = models.PositiveSmallIntegerField(
                default=26,
                verbose_name="lorem",
                help_text="bla",
                # comment 1 ?
                # comment 2
                validators=[MinValueValidator(1), MaxValueValidator(28)],
            )
        """,
        """\
        from django.db import models
        from django.core.validators import MinValueValidator, MaxValueValidator

        class Comment():
            nb = models.PositiveSmallIntegerField(
                verbose_name="lorem",
                default=26,
                help_text="bla",
                # comment 1 ?
                # comment 2
                validators=[MinValueValidator(1), MaxValueValidator(28)],
            )
        """,
        settings,
        filename="models.py",
    )


def test_long_in_between_comment():
    check_transformed(
        """\
        from django.db import models

        class Comment():
            nb = doc_identifier = models.CharField(  # noqa: DJ001
                max_length=100,
                blank=True,
                null=True,
                verbose_name="lorem",
                # in between COMMENT
                help_text="lorem comment",
            )
        """,
        """\
        from django.db import models

        class Comment():
            nb = doc_identifier = models.CharField(  # noqa: DJ001
                verbose_name="lorem",
                max_length=100,
                blank=True,
                null=True,
                # in between COMMENT
                help_text="lorem comment",
            )
        """,
        settings,
        filename="models.py",
    )


# @pytest.mark.skip("not implemented")
# def test_transform_fk():
#     check_transformed(
#         """\
#         from django.db import models
#
#         class Comment(models.Model):
#             bad_order_fk = models.ForeignKey(
#                 to="blog.Article", on_delete=models.CASCADE, related_name="c"
#             )
#         """,
#         """\
#         from django.db import models
#
#         class Comment(models.Model):
#             bad_order_fk = models.ForeignKey(
#                 to="blog.Article", on_delete=models.CASCADE, related_name="c"
#             )
#         """,
#         settings,
#         filename="models.py",
#     )
