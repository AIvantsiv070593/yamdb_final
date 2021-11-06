from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Category, CustomUser, Genre, Title, Review, Comment


IF_NONE = "-пусто-"


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = (
        "username",
        "email",
        "role",
        "bio",
        "is_active",
    )
    list_filter = (
        "username",
        "email",
        "role",
        "is_active",
    )
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "username",
                    "role",
                    "email",
                    "password",
                    "confirmation_code",
                    "bio",
                )
            },
        ),
        ("Permissions", {"fields": ("is_staff", "is_active", "is_superuser")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "role",
                    "email",
                    "password1",
                    "password2",
                    "bio",
                    "is_staff",
                    "is_active",
                    "is_superuser",
                ),
            },
        ),
    )
    search_fields = ("email",)
    ordering = ("email",)


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "year", "category", "description")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "slug")


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ("pk", "name", "slug")


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "author", "pub_date", "score", "title")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = IF_NONE


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("pk", "text", "author", "pub_date", "review")
    search_fields = ("text",)
    list_filter = ("pub_date",)
    empty_value_display = IF_NONE
