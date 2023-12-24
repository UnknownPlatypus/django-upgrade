from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(5, 0))


def test_noop_django_models():
    check_noop(
        """\
        from django.contrib.auth.models import Group
        class MyModel(models.Model):
            group = models.ForeignKey(Group, on_delete=models.SET_NULL)
        """,
        settings,
    )


def test_noop_fk_defined_in_same_file():
    check_noop(
        """\
        class Category(models.Model):
            name = models.CharField(max_length=12)

        class Article(models.Model):
            category = models.ForeignKey(Category, on_delete=models.SET_NULL)
        """,
        settings,
    )


def test_transform_simple_import():
    check_transformed(
        """\
        from core.models import User
        class MyModel(models.Model):
            user = models.ForeignKey(User, on_delete=models.SET_NULL)
            user2 = models.OneToOneField(User, on_delete=models.SET_NULL)
            users = models.ManyToManyField(User, on_delete=models.SET_NULL)
        """,
        """\
        from core.models import User
        class MyModel(models.Model):
            user = models.ForeignKey("core.User", on_delete=models.SET_NULL)
            user2 = models.OneToOneField("core.User", on_delete=models.SET_NULL)
            users = models.ManyToManyField("core.User", on_delete=models.SET_NULL)
        """,
        settings,
    )


def test_transform_absolute_import():
    check_transformed(
        """\
        from core.models.user import User
        from core.models.weird.weirdo import WeirdUser
        class MyModel(models.Model):
            user = models.ForeignKey(User, on_delete=models.SET_NULL)
            weird_user = models.ForeignKey(WeirdUser, on_delete=models.SET_NULL)
        """,
        """\
        from core.models.user import User
        from core.models.weird.weirdo import WeirdUser
        class MyModel(models.Model):
            user = models.ForeignKey("core.User", on_delete=models.SET_NULL)
            weird_user = models.ForeignKey("core.WeirdUser", on_delete=models.SET_NULL)
        """,
        settings,
    )


def test_transform_inferred_app_name():
    check_transformed(
        """\
        class MyModel(models.Model):
            user = models.ForeignKey("User", on_delete=models.SET_NULL)
        """,
        """\
        class MyModel(models.Model):
            user = models.ForeignKey("core.User", on_delete=models.SET_NULL)
        """,
        settings,
        filename="core/models/mymodels.py",
    )


def test_noop_self():
    check_noop(
        """\
        class MyModel(models.Model):
            group = models.ForeignKey("self", on_delete=models.SET_NULL)
        """,
        settings,
        filename="core/models/mymodels.py",
    )
