from django_filters import rest_framework as filters

from .models import Title


class TitleFilter(filters.FilterSet):
    """Filtering infra to support slug-based filtering for genre/category,
    as well as partial name match.
    """
    genre = filters.CharFilter(field_name="genre__slug", lookup_expr="iexact")
    category = filters.CharFilter(
        field_name="category__slug", lookup_expr="iexact"
    )
    year = filters.NumberFilter(field_name="year", lookup_expr="exact")
    name = filters.CharFilter(field_name="name", lookup_expr="icontains")

    class Meta:
        model = Title
        fields = ("category", "genre", "year")
