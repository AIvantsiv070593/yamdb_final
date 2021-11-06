from datetime import datetime, MINYEAR

from django.db import models
from django.core import validators
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager


class CustomUserManager(UserManager):
    """Custom user model manager,
    where email and username is the unique identifiers.
    """

    def create_user(
        self, username, email, password, role="user", **extra_fields
    ):
        """Create and save a User with the given email and password."""
        if not username:
            raise ValueError("Имя ползователя должно быть указано")
        if not email:
            raise ValueError("Email должен быть указан")
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(
            username=username, email=email, role=role, **extra_fields
        )
        user.set_password(password)
        user.save()
        return user

    def create_superuser(
        self, username, email, password, role="admin", **extra_fields
    ):
        """Create and save a SuperUser with the given
        username, email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен "
                             "иметь значение is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен "
                             "иметь значение is_superuser=True.")
        return self.create_user(
            username, email, password, role=role, **extra_fields
        )


class CustomUser(AbstractUser):
    """Defines parameters for the User model."""

    email = models.EmailField("email address", unique=True)
    bio = models.CharField("bio", max_length=100, null=True)
    confirmation_code = models.CharField("code", max_length=50, default="null")

    # class ROLE_CHOICES(models.TextChoices):
    #     USER = "U", ("user")
    #     MODERATOR = "M", ("moderator")
    #     ADMIN = "A", ("admin")
    ROLE_CHOICES = (
        ("U", "user"),
        ("M", "moderator"),
        ("A", "admin")
    )
    # role = models.CharField(
    #     max_length=50, choices=ROLE_CHOICES.choices,
    # default=ROLE_CHOICES.USER
    # )
    role = models.CharField(
        max_length=50, choices=ROLE_CHOICES, default="U"
    )
    objects = CustomUserManager()

    def is_admin(self):
        return self.role == "admin"

    def is_moderator(self):
        return self.role == "moderator"

    def __str__(self):
        return self.username


class Genre(models.Model):
    """Defines parameters for the genres."""

    name = models.CharField(
        verbose_name="Genre", max_length=200, unique=True, db_index=True)
    slug = models.SlugField(verbose_name="Slug", unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class Category(models.Model):
    """Defines parameters for the category."""

    name = models.CharField(
        verbose_name="Category", max_length=200, unique=True, db_index=True)
    slug = models.SlugField(verbose_name="Slug", unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return f"{self.name} {self.slug}"


class Title(models.Model):
    """Defines parameters for the title."""

    name = models.CharField(verbose_name="Title", max_length=200)
    year = models.PositiveSmallIntegerField(
        verbose_name="Year", blank=True, null=True, db_index=True)
    description = models.CharField(
        verbose_name="Description", max_length=500, blank=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name="title",
        verbose_name="category",
    )
    genre = models.ManyToManyField(Genre, through="Title2Genre")

    class Meta:
        """Constraint check added to make sure that year is in range."""

        ordering = ("name",)
        constraints = [
            models.CheckConstraint(
                check=(
                    models.Q(year__gte=MINYEAR)
                    & models.Q(year__lte=datetime.now().year + 50)
                ),
                name="invalid_year",
            )
        ]

    def __str__(self):
        return f"{self.name} {self.year}"


class Title2Genre(models.Model):
    """M2M model for Titles to Genres relation tracking."""

    title = models.ForeignKey(Title, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)

    class Meta:
        """Constraint check added to avoid duplicates in DB."""

        ordering = ("title",)
        constraints = [
            models.UniqueConstraint(
                fields=["title", "genre"], name="unique_genre"
            )
        ]

    def __str__(self):
        return f"{self.title} {self.genre}"


class Review(models.Model):
    """Review model for Titles."""

    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="author"
    )
    text = models.TextField()
    score = models.IntegerField(
        verbose_name="score",
        validators=[
            validators.MinValueValidator(
                limit_value=1, message="Рейтинг не может быть меньше 1"),
            validators.MaxValueValidator(
                limit_value=10, message="Рейтинг не может быть больше 10")
        ],

    )
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name="title",
        blank=True,
        null=True,
    )
    pub_date = models.DateTimeField(
        "Дата добавления", auto_now_add=True, db_index=True
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "review"

    def __str__(self) -> str:
        return (
            f"Автор: {self.author} "
            f"Дата публикации: {self.pub_date.strftime('%m/%d/%Y, %H:%M')} "
            f"Текст: {self.text[:15]}"
            f"Оценка: {self.score}"
        )


class Comment(models.Model):
    """Comment model for Review."""

    author = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="comments"
    )
    review = models.ForeignKey(
        Review, on_delete=models.CASCADE, related_name="comments"
    )
    text = models.TextField()
    pub_date = models.DateTimeField(
        "Дата добавления", auto_now_add=True, db_index=True
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "comment"

    def __str__(self) -> str:
        return (
            f"Автор: {self.author} "
            f"Дата публикации: {self.pub_date.strftime('%m/%d/%Y, %H:%M')} "
            f"Текст: {self.text[:15]}"
        )
