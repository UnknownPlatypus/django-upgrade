from __future__ import annotations

from django_upgrade.data import Settings
from tests.fixers.tools import check_noop
from tests.fixers.tools import check_transformed

settings = Settings(target_version=(4, 2))


def test_noop_wrong_filename():
    check_noop(
        """\
        from django.db import models

        class Article(models.Model):
            objects: int = models.Manager()
            truc = fkjehgfdManager()
            author_name = models.CharField(max_length=100, verbose_name=_("Nom"))
        """,
        settings,
    )


def test_noop_ordered_class():
    check_noop(
        """\
        from django.db import models

        class Article(models.Model):
            author_name = models.CharField(max_length=100, verbose_name=_("Name"))
            title = models.CharField(max_length=100, verbose_name=_("Title"))

            objects = models.Manager()
            validated = ValidatedCommentManager()

            class Meta:
                verbose_name = _("Commentaire Blog")
                verbose_name_plural = _("Commentaires Blog")

            def __str__(self):
                return f"Comment - {self.author_name}..."

            def clean(self):
                pass

            def save(self, *args, **kwargs):
                super().save(*args, **kwargs)

            def asave(self, *args, **kwargs):
                pass

            def delete(self, *args, **kwargs):
                pass

            def adelete(self, *args, **kwargs):
                pass

            def get_absolute_url(self) -> str:
                return ""

            @property
            def edit_link(self):
                return urljoin(
                    settings.MY_DOMAIN,
                    reverse(
                        "admin:blog_comment_change",
                        args=(self.id,),
                    ),
                )

            @cached_property
            def raw_content(self):
                return html.unescape(strip_tags(self.content))

            def my_method(self) -> str:
                return ""

            @random_decorator
            def my_decorated_method(self) -> str:
                return ""

            @classmethod
            def my_class_method(cls) -> str:
                return ""

            @staticmethod
            def my_static_method() -> str:
                return ""
        """,
        settings,
        filename="blog/models/article.py",
    )


def test_annotated_fields_and_managers():
    check_transformed(
        """\
        from django.db import models

        class Article(models.Model):
            author_name = models.CharField(max_length=100, verbose_name=_("Nom"))

            people = models.Manager()
            people2 = PersonQuerySet.as_manager()
            people3 = foo.PersonQuerySet.as_manager()
            other_module_manager = foo.MyManager()
            from_q_manager = CustomManager.from_queryset(CustomQuerySet)()
            objects: PollManager = PollManager()
            dahl_objects = DahlBookManager()

            author_name2: str = models.CharField(max_length=100, verbose_name=_("Nom"))
        """,
        """\
        from django.db import models

        class Article(models.Model):
            author_name = models.CharField(max_length=100, verbose_name=_("Nom"))

            author_name2: str = models.CharField(max_length=100, verbose_name=_("Nom"))

            people = models.Manager()
            people2 = PersonQuerySet.as_manager()
            people3 = foo.PersonQuerySet.as_manager()
            other_module_manager = foo.MyManager()
            from_q_manager = CustomManager.from_queryset(CustomQuerySet)()
            objects: PollManager = PollManager()
            dahl_objects = DahlBookManager()
        """,
        settings,
        filename="blog/models/article.py",
    )


def test_last_element_expr():
    check_transformed(
        """\
        from django.db import models

        class Article(models.Model):
            title = models.CharField(max_length=255, verbose_name="H1")

            def my_method(self) -> str:
                return ""

            my_method.short_description = "short desc"

            sub_title = models.CharField(max_length=255, verbose_name="H1")

            def my_method2(self) -> str:
                return ""

            my_method2.short_description = "short desc2"
        """,
        """\
        from django.db import models

        class Article(models.Model):
            title = models.CharField(max_length=255, verbose_name="H1")

            sub_title = models.CharField(max_length=255, verbose_name="H1")

            def my_method(self) -> str:
                return ""

            my_method.short_description = "short desc"

            def my_method2(self) -> str:
                return ""

            my_method2.short_description = "short desc2"
            """,
        settings,
        filename="blog/models/article.py",
    )


def test_properties():
    check_transformed(
        """\
        from django.db import models

        class Article(models.Model):
            title = models.CharField(max_length=255, verbose_name="H1")

            @property
            def my_property(self) -> str:
                return self._prop

            @my_property.setter
            def my_property(self, value) -> str:
                self._prop = value

            @my_property.deleter
            def my_property(self, value) -> str:
                del self._prop

            sub_title = models.CharField(max_length=255, verbose_name="H1")

            @cached_property
            def my_cached_property(self) -> str:
                return ""
        """,
        """\
        from django.db import models

        class Article(models.Model):
            title = models.CharField(max_length=255, verbose_name="H1")

            sub_title = models.CharField(max_length=255, verbose_name="H1")

            @property
            def my_property(self) -> str:
                return self._prop

            @my_property.setter
            def my_property(self, value) -> str:
                self._prop = value

            @my_property.deleter
            def my_property(self, value) -> str:
                del self._prop

            @cached_property
            def my_cached_property(self) -> str:
                return ""
            """,
        settings,
        filename="blog/models/article.py",
    )


def test_extra_manager():
    check_transformed(
        """\
        from django.db import models
        from foo import MyCustomManager

        class Article(models.Model):
            '''My Article class'''
            objects = MyCustomManager()
            title = models.CharField(max_length=255, verbose_name="H1")

            @property
            def my_property(self) -> str:
                return ""

            manager_2 = MyCustomManager()
        """,
        """\
        from django.db import models
        from foo import MyCustomManager

        class Article(models.Model):
            '''My Article class'''
            title = models.CharField(max_length=255, verbose_name="H1")

            objects = MyCustomManager()

            manager_2 = MyCustomManager()

            @property
            def my_property(self) -> str:
                return ""
        """,
        settings,
        filename="blog/models/article.py",
    )


def test_preceding_comments():
    check_transformed(
        """\
        from django.db import models
        from foo import MyCustomManager

        class Article(models.Model):
            # This comment describe
            # The following custom manager
            objects = MyCustomManager()

            # This is a comment

            # This one too
            title = models.CharField(max_length=255, verbose_name="H1")

            @property
            def my_property(self) -> str:
                '''Super useful property'''
                return ""

            manager_2 = MyCustomManager()

            def test(self):
                return None

            # Some random commented code
            # # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            # BBB = models.BooleanField(default=True)
            # DDD = models.BooleanField(default=True)

            # CCC = models.BooleanField(
            #     default=True
            # )  # CCC

            def save(self, *args, **kwargs):
                super().save(*args, **kwargs)
        """,
        """\
        from django.db import models
        from foo import MyCustomManager

        class Article(models.Model):
            # This is a comment

            # This one too
            title = models.CharField(max_length=255, verbose_name="H1")

            # This comment describe
            # The following custom manager
            objects = MyCustomManager()

            manager_2 = MyCustomManager()

            # Some random commented code
            # # AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
            # BBB = models.BooleanField(default=True)
            # DDD = models.BooleanField(default=True)

            # CCC = models.BooleanField(
            #     default=True
            # )  # CCC

            def save(self, *args, **kwargs):
                super().save(*args, **kwargs)

            @property
            def my_property(self) -> str:
                '''Super useful property'''
                return ""

            def test(self):
                return None
        """,
        settings,
        filename="blog/models/article.py",
    )


def test_trailing_line_comments():
    check_transformed(
        """\
        from django.db import models

        class Article(models.Model):
            mail_range: str  # bla bla bla bla
            nb_reviews = models.IntegerField(default=0)  # AAA

            def my_method(self) -> str:
                return ""

            def __str__(self):
                return "FOO"

        """,
        """\
        from django.db import models

        class Article(models.Model):
            mail_range: str  # bla bla bla bla
            nb_reviews = models.IntegerField(default=0)  # AAA

            def __str__(self):
                return "FOO"

            def my_method(self) -> str:
                return ""

        """,
        settings,
        filename="blog/models/article.py",
    )


def test_clash_with_other_fixers():
    check_transformed(
        """\
        from django.db import models
        from django.db.models import NullBooleanField

        class Article(models.Model):
            mail_range: str  # bla bla bla bla
            author = models.OneToOneField("auth.User")  # AAA
            valuable = NullBooleanField("Valuable")

            def my_method(self) -> str:
                return ""

            def __str__(self):
                return "FOO"

            reviewer = models.OneToOneField("auth.User")  # B
        """,
        """\
        from django.db import models
        from django.db.models import BooleanField

        class Article(models.Model):
            mail_range: str  # bla bla bla bla
            author = models.OneToOneField("auth.User", on_delete=models.CASCADE)  # AAA
            valuable = BooleanField("Valuable", null=True)

            reviewer = models.OneToOneField("auth.User", on_delete=models.CASCADE)  # B

            def __str__(self):
                return "FOO"

            def my_method(self) -> str:
                return ""
        """,
        settings,
        filename="blog/models/article.py",
    )


def test_no_trailing_newline_class_end():
    check_transformed(
        """\
        from django.db import models

        class Article(models.Model):
            author_name = models.CharField(max_length=100, verbose_name=_("Nom"))

            objects = models.Manager()
            validated = ValidatedCommentManager()

            def __str__(self):
                return f"Comment - {self.author_name}..."

            class Meta:
                verbose_name = _("Commentaire Blog")
                verbose_name_plural = _("Commentaires Blog")

            @property
            def raw_content(self):
                return html.unescape(strip_tags(self.content))

        """,
        """\
        from django.db import models

        class Article(models.Model):
            author_name = models.CharField(max_length=100, verbose_name=_("Nom"))

            objects = models.Manager()
            validated = ValidatedCommentManager()

            class Meta:
                verbose_name = _("Commentaire Blog")
                verbose_name_plural = _("Commentaires Blog")

            def __str__(self):
                return f"Comment - {self.author_name}..."

            @property
            def raw_content(self):
                return html.unescape(strip_tags(self.content))

        """,
        settings,
        filename="blog/models/article.py",
    )


def test_trailing_newlines():
    check_transformed(
        """\
        from django.db import models

        class Article(models.Model):
            nb_reviews = models.IntegerField(default=0)  # AAA

            def my_method(self) -> str:
                return ""

            def __str__(self):
                return "FOO"
        # Exactly 3 NL



        class Foo:
            pass
        """,
        """\
        from django.db import models

        class Article(models.Model):
            nb_reviews = models.IntegerField(default=0)  # AAA

            def __str__(self):
                return "FOO"

            def my_method(self) -> str:
                return ""
        # Exactly 3 NL



        class Foo:
            pass
        """,
        settings,
        filename="blog/models/article.py",
    )


def test_bare_annotations_untouched():
    check_transformed(
        """\
        from django.db import models

        class Article(models.Model):
            a: int

            objects: int = models.Manager()
            truc = CustomManager()
            comment_set: QuerySet[Comment]

            author_name = models.CharField(max_length=100, verbose_name=_("Nom"))
        """,
        """\
        from django.db import models

        class Article(models.Model):
            a: int
            author_name = models.CharField(max_length=100, verbose_name=_("Nom"))

            objects: int = models.Manager()
            truc = CustomManager()
            comment_set: QuerySet[Comment]
        """,
        settings,
        filename="blog/models/article.py",
    )


def test_docstring_as_comment_not_supported():
    check_transformed(
        """\
        from django.db import models

        class MyModel(models.Model):
            class Meta:
                abstract = True

            '''Specific fields'''
            title = models.CharField(max_length=255, verbose_name="H1")
        """,
        """\
        from django.db import models

        class MyModel(models.Model):
            title = models.CharField(max_length=255, verbose_name="H1")

            class Meta:
                abstract = True

            '''Specific fields'''
        """,
        settings,
        filename="blog/models/article.py",
    )


def test_full_transform():
    check_transformed(
        """\
        from __future__ import annotations

        from django.db import models
        from django.db.models import Prefetch

        class EntryStatus(models.TextChoices):
            PUBLISHED = "published"
            SCHEDULED = "scheduled"
            HIDDEN = "hidden"
            SCRATCH = "scratch"

        class ArticleQuerySet(models.QuerySet):
            def with_validated_comments(self):
                return self.prefetch_related(
                    Prefetch(
                        "comments",
                        queryset=Comment.validated.all(),
                    ),
                )

        ArticleManager = models.Manager.from_queryset(ArticleQuerySet)

        class Article(PlusPlusMixin, models.Model, metaclass=PlusPlusMetaClass):
            '''docstring'''
            title = models.CharField(max_length=255, verbose_name="H1")
            meta_title = models.CharField(
                max_length=255,
                blank=True,
                verbose_name=_("Title"),
                help_text=_("Utilisé pour les balises meta"),
            )
            # COMMENT
            status = models.CharField(
                choices=EntryStatus.choices,
                max_length=50,
                default="hidden",
                verbose_name=_("Statut"),
                db_index=True,
            )

            objects = ArticleManager()

            lead = HTMLField(verbose_name=_("Texte d'intro de l'article"))
            content = PlusPlusField(verbose_name=_("Contenu de l'article"))
            excerpt = models.TextField(
                blank=True,
                verbose_name=_("Extrait"),
            )

            @property
            def is_active(self) -> bool:
                return True

            def save(self, *args, **kwargs):
                super().save(*args, **kwargs)

            def count_words(self) -> int:
                return strip_tags(self.content).count(" ") + 1

            def method_none(self) -> None:
                return None

            def get_absolute_url(self) -> str:
                return reverse(
                    "blog:blog_multiple_views",
                    kwargs={"slug": self.slug},
                )

            def __str__(self):
                return f"Article: {self.title}"

            class Meta:
                ordering = ["-published_at"]
                indexes = [
                    models.Index(fields=["slug"], name="slug_index"),
                    models.Index(fields=["title"], name="title_index"),
                ]
                verbose_name = _("Article")
                verbose_name_plural = _("Articles")
        """,
        """\
        from __future__ import annotations

        from django.db import models
        from django.db.models import Prefetch

        class EntryStatus(models.TextChoices):
            PUBLISHED = "published"
            SCHEDULED = "scheduled"
            HIDDEN = "hidden"
            SCRATCH = "scratch"

        class ArticleQuerySet(models.QuerySet):
            def with_validated_comments(self):
                return self.prefetch_related(
                    Prefetch(
                        "comments",
                        queryset=Comment.validated.all(),
                    ),
                )

        ArticleManager = models.Manager.from_queryset(ArticleQuerySet)

        class Article(PlusPlusMixin, models.Model, metaclass=PlusPlusMetaClass):
            '''docstring'''
            title = models.CharField(max_length=255, verbose_name="H1")
            meta_title = models.CharField(
                max_length=255,
                blank=True,
                verbose_name=_("Title"),
                help_text=_("Utilisé pour les balises meta"),
            )
            # COMMENT
            status = models.CharField(
                choices=EntryStatus.choices,
                max_length=50,
                default="hidden",
                verbose_name=_("Statut"),
                db_index=True,
            )

            lead = HTMLField(verbose_name=_("Texte d'intro de l'article"))
            content = PlusPlusField(verbose_name=_("Contenu de l'article"))
            excerpt = models.TextField(
                blank=True,
                verbose_name=_("Extrait"),
            )

            objects = ArticleManager()

            class Meta:
                ordering = ["-published_at"]
                indexes = [
                    models.Index(fields=["slug"], name="slug_index"),
                    models.Index(fields=["title"], name="title_index"),
                ]
                verbose_name = _("Article")
                verbose_name_plural = _("Articles")

            def __str__(self):
                return f"Article: {self.title}"

            def save(self, *args, **kwargs):
                super().save(*args, **kwargs)

            def get_absolute_url(self) -> str:
                return reverse(
                    "blog:blog_multiple_views",
                    kwargs={"slug": self.slug},
                )

            @property
            def is_active(self) -> bool:
                return True

            def count_words(self) -> int:
                return strip_tags(self.content).count(" ") + 1

            def method_none(self) -> None:
                return None
        """,
        settings,
        filename="blog/models/article.py",
    )
