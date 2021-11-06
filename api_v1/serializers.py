from datetime import datetime, MINYEAR

from django.core.exceptions import ValidationError
from django.contrib.auth.models import update_last_login
from django.shortcuts import get_object_or_404
from django.db.models import Avg
from rest_framework import serializers
from rest_framework_simplejwt.serializers import (
    TokenObtainSerializer,
    api_settings,
)
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.validators import UniqueValidator

from .models import (
    CustomUser,
    Title,
    Category,
    Genre,
    Title2Genre,
    Comment,
    Review,
)


class CustomUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all())]
    )
    username = serializers.CharField(
        max_length=100,
        validators=[UniqueValidator(queryset=CustomUser.objects.all())],
    )
    role = serializers.CharField(required=False)

    class Meta:
        fields = (
            "first_name",
            "last_name",
            "username",
            "bio",
            "email",
            "role",
            "is_admin"
        )
        model = CustomUser


class MyCustomSerializer(CustomUserSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=CustomUser.objects.all())],
        required=False,
    )
    username = serializers.CharField(
        max_length=100,
        validators=[UniqueValidator(queryset=CustomUser.objects.all())],
        required=False,
    )


class MyTokenObtainSerializer(TokenObtainSerializer):
    username_field = CustomUser.EMAIL_FIELD

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"] = serializers.EmailField()
        self.fields["confirmation_code"] = serializers.CharField(required=True)
        self.fields.pop("password")

    def validate(self, attrs):
        """
        Check user and confirmation_code is valid.
        """
        try:
            self.user = CustomUser.objects.get(
                email=attrs[self.username_field]
            )
        except CustomUser.DoesNotExist:
            raise ValidationError("The email is not found.")

        if not (self.user.confirmation_code == attrs["confirmation_code"]):
            raise ValidationError("Confirmation_code is not valid.")

        code = "null"
        self.user.confirmation_code = code
        self.user.save()
        return {}


class MyTokenObtainPairSerializer(MyTokenObtainSerializer):
    @classmethod
    def get_token(cls, user):
        return RefreshToken.for_user(user)

    def validate(self, attrs):
        data = super().validate(attrs)

        refresh = self.get_token(self.user)

        data["refresh"] = str(refresh)
        data["access"] = str(refresh.access_token)

        if api_settings.UPDATE_LAST_LOGIN:
            update_last_login(None, self.user)

        return data


class GenreSerializer(serializers.ModelSerializer):
    """Serializer to work on the Genre model.
    The 'slug' set to be a lookup filed."""
    class Meta:
        fields = ("name", "slug")
        lookup_field = "slug"
        extra_field_kwargs = {"url": {"lookup_field": "slug"}}
        model = Genre


class CategorySerializer(serializers.ModelSerializer):
    """Serializer to work on the Category model.
    The 'slug' set to be a lookup filed."""
    class Meta:
        fields = ("name", "slug")
        lookup_field = "slug"
        extra_field_kwargs = {"url": {"lookup_field": "slug"}}
        model = Category


class TitleSerializerList(serializers.ModelSerializer):
    """Simplified Serializer to support a GET operation."""
    rating = serializers.SerializerMethodField()
    category = CategorySerializer(many=False, read_only=True)
    genre = GenreSerializer(many=True, read_only=True)

    class Meta:
        fields = (
            "id",
            "name",
            "year",
            "rating",
            "description",
            "category",
            "genre",
        )
        model = Title
        validators = []
        depth = 1
        lookup_field = "slug"
        extra_field_kwargs = {"url": {"lookup_field": "slug"}}
        read_only_fields = [
            "rating",
        ]

    def get_rating(self, obj):
        try:
            current_rating = int(
                obj.title.aggregate(rating=Avg("score"))["rating"]
            )
            return current_rating
        except TypeError:
            return None


class TitleSerializer(serializers.ModelSerializer):
    """Serializer to support POST/PATCH/DEL operations."""
    rating = serializers.SerializerMethodField()
    category = CategorySerializer(many=False, read_only=True, required=False)
    genre = GenreSerializer(many=True, read_only=True)

    class Meta:
        fields = (
            "id",
            "name",
            "year",
            "rating",
            "description",
            "category",
            "genre",
        )
        model = Title
        validators = []
        depth = 1
        read_only_fields = [
            "rating",
        ]

    def create(self, validated_data):
        """Create method modified to introduce a possibility
        to create related object of Category.
        """
        if ("category" in self.initial_data) and (
            "genre" in self.initial_data
        ):
            genre_slug = self.initial_data.getlist("genre")
            category_slug = self.initial_data.get("category")
            category = get_object_or_404(Category, slug=category_slug)
            title = Title.objects.create(
                **validated_data, category=category  # noqa
            )

            for slug in genre_slug:
                current_genre = get_object_or_404(Genre, slug=slug)
                Title2Genre.objects.create(
                    title=title, genre=current_genre  # noqa
                )
            return title

        if "genre" in self.initial_data:
            genre_slug = self.initial_data.get("genre")
            title = Title.objects.create(**validated_data)  # noqa

            for slug in genre_slug:
                current_genre = get_object_or_404(Genre, slug=slug)
                Title2Genre.objects.create(
                    title=title, genre=current_genre  # noqa
                )
            return title

        if "category" in self.initial_data:
            category_slug = self.initial_data.get("category")
            category = get_object_or_404(Category, slug=category_slug)
            title = Title.objects.update_or_create(
                **validated_data, category=category  # noqa
            )
            return title

        title = Title.objects.create(**validated_data)  # noqa
        return title

    def update(self, instance, validated_data):
        """Update method modified to introduce a possibility to
        PATCH related object of Category."""

        name = self.initial_data.get("name")
        year = self.initial_data.get("year")

        instance.name = name
        instance.year = year

        if "category" in self.initial_data:
            slug = self.initial_data.get("category")
            category = get_object_or_404(Category, slug=slug)
            instance.category = category
            instance.save(update_fields=("category", "name", "year"))
            return instance
        instance.save()
        return instance

    def get_rating(self, obj):
        try:
            current_rating = int(
                obj.title.aggregate(rating=Avg("score"))["rating"]
            )
            return current_rating
        except TypeError:
            return None

    def validate(self, attrs):
        """Validate method makes sure that given year
        does not go far in future. Same time the model constraint
        check assumes publication year is less than 2073.
        """
        if "year" in self.initial_data:
            claimed_year = int(self.initial_data.get("year"))
            max_allowed_year = datetime.now().year + 2

            if MINYEAR <= claimed_year <= max_allowed_year:
                return super().validate(attrs)
            raise serializers.ValidationError(
                "Year of the publication cannot be "
                "significantly grater than current year")
        return super().validate(attrs)


class ReviewSerializer(serializers.ModelSerializer):
    """Serializer to support GET operations."""
    author = serializers.SlugRelatedField(
        slug_field="username",
        queryset=CustomUser.objects.all(),
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        fields = "__all__"
        read_only_fields = ("author", "title", "pub_date")
        model = Review


class ReviewSerializerCreate(serializers.ModelSerializer):
    """Serializer to support POST operations."""
    author = serializers.SlugRelatedField(
        slug_field="username",
        queryset=CustomUser.objects.all(),
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        fields = "__all__"
        read_only_fields = ("author", "title", "pub_date")
        model = Review

    def validate(self, attrs):
        """Validate method makes sure that user cannot POST review twice.
        """
        author = self.context["request"].user
        title = self.context["view"].kwargs["title_id"]
        if not (Review.objects.filter(title=title, author=author).exists()):
            return super().validate(attrs)
        raise serializers.ValidationError("Review already exist")


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        slug_field="username",
        queryset=CustomUser.objects.all(),
        default=serializers.CurrentUserDefault(),
    )

    class Meta:
        fields = "__all__"
        read_only_fields = ("author", "review", "pub_date")
        model = Comment
