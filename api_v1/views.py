from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.crypto import get_random_string

from rest_framework import filters, viewsets, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import (
    AllowAny,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from api_yamdb import settings
from . import serializers
from .filters import TitleFilter
from .models import Category, CustomUser, Genre, Title, Review
from .permissions import (
    IsAdminPermission,
    IsOwner,
    ReadOnly,
)


@api_view(["POST"])
@permission_classes([AllowAny])
def send_mail_verify(self):
    """Send an email with a randomly generated confirmation_code.
    """
    code = get_random_string(length=12)
    user = get_object_or_404(CustomUser, email=self.data["email"])
    user.confirmation_code = code
    user.save()
    message = "Код для получения JWT token " + code
    user.email_user(
        "Confirmation_code_APITOKEN",
        message,
        settings.DEFAULT_FROM_EMAIL,
    )
    return HttpResponse("Код сгенерирован и успешно отправлен!")


class UsersViewSet(viewsets.ModelViewSet):
    """A ViewSet for viewing all users instances.
    """
    serializer_class = serializers.CustomUserSerializer
    permission_classes = [IsAuthenticated, IsAdminPermission]
    filter_backends = (filters.SearchFilter,)
    search_fields = [
        "email",
    ]
    queryset = CustomUser.objects.all()
    lookup_field = "username"

    @action(
        detail=False,
        methods=["GET", "PATCH"],
        permission_classes=[IsAuthenticated],
    )
    def me(self, request):
        """Get and Edit current user.
        """
        instance = self.request.user
        if request.method == "PATCH":
            if "role" in request.data and not(request.user.is_admin()):
                raise PermissionDenied("Только Admin может менять ROLE.")
            serializer = serializers.MyCustomSerializer(
                instance,
                data=request.data,
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class MyTokenObtainPairView(TokenObtainPairView):
    """The infra to support token generation.
    """
    serializer_class = serializers.MyTokenObtainPairSerializer


class GetPostPlaceholder(viewsets.GenericViewSet,
                         mixins.ListModelMixin,
                         mixins.CreateModelMixin):
    """Class placeholder inherits mixins to supports only GET/POST methods."""
    pass


class DelPlaceholder(viewsets.GenericViewSet,
                     mixins.DestroyModelMixin):
    """Class placeholder inherits mixins to supports only DELETE method."""
    pass


class CategoryViewSetList(GetPostPlaceholder):
    """CategoryVSList supports only GET/POST methods.
    Modifications can be done by administrator only, while GET any.
    """
    http_method_names = ["get", "post"]
    queryset = Category.objects.all()  # noqa
    serializer_class = serializers.CategorySerializer

    lookup_field = "slug"
    permission_classes = [IsAdminPermission | ReadOnly]

    filter_backends = (filters.SearchFilter,)
    search_fields = [
        "name",
    ]


class CategoryViewSetDetail(DelPlaceholder):
    """CategoryVSDetail supports only DELETE method.
    Modifications can be done by administrator only.
    """
    http_method_names = [
        "delete",
    ]
    serializer_class = serializers.CategorySerializer
    lookup_field = "slug"
    permission_classes = [IsAdminPermission]
    queryset = Category.objects.all()  # noqa

    filter_backends = (filters.SearchFilter,)
    search_fields = [
        "name",
    ]


class GenreViewSetList(GetPostPlaceholder):
    """GenreVSList supports only GET/POST methods.
    Modifications can be done by administrator only, while GET any.
    """
    http_method_names = ["get", "post"]
    queryset = Genre.objects.all()  # noqa
    serializer_class = serializers.GenreSerializer

    lookup_field = "slug"
    permission_classes = [IsAdminPermission | ReadOnly]

    filter_backends = (filters.SearchFilter,)
    search_fields = [
        "name",
    ]


class GenreViewSetDetail(DelPlaceholder):
    """GenreVSDetail supports only DELETE method.
    Modifications can be done by administrator only.
    """
    http_method_names = [
        "delete",
    ]
    queryset = Genre.objects.all()  # noqa
    serializer_class = serializers.GenreSerializer

    lookup_field = "slug"
    permission_classes = [IsAdminPermission]
    filter_backends = (filters.SearchFilter,)
    search_fields = [
        "name",
    ]


class TitleViewSet(viewsets.ModelViewSet):
    """Basic functionality introduced with a
    method-depending serializer selector."""
    queryset = Title.objects.all()  # noqa

    permission_classes = [IsAdminPermission | ReadOnly]
    filterset_class = TitleFilter  # noqa

    def get_serializer_class(self):
        """Following added to assign a different serializer
        depending on request method.
        """
        if self.action == "list":
            return serializers.TitleSerializerList
        return serializers.TitleSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Basic functionality introduced with a
    method-depending serializer selector and permissions depending action.
    """
    permission_classes_by_action = {
        "create": [IsAuthenticated],
        "list": [IsAuthenticatedOrReadOnly],
        "partial_update": [IsOwner],
        "destroy": [IsOwner],
    }
    search_fields = ["title__title_id"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_queryset(self):
        queryset = Review.objects.filter(title=self.kwargs["title_id"])
        title_id = self.request.query_params.get("title", None)
        if title_id is not None:
            title = get_object_or_404(Title, id=title_id)
            return Review.objects.filter(title=title.title_id)
        return queryset

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs["title_id"])
        serializer.save(author=self.request.user, title_id=title.id)

    def get_serializer_class(self):
        """Following added to assign a different serializer
        depending on request method.
        """
        if self.action == "create":
            return serializers.ReviewSerializerCreate
        return serializers.ReviewSerializer

    def get_permissions(self):
        try:
            return [
                permission()
                for permission in self.permission_classes_by_action[
                    self.action
                ]
            ]
        except KeyError:
            return [permission() for permission in self.permission_classes]


class CommentViewSet(viewsets.ModelViewSet):
    """Basic functionality introduced with a
    method-depending serializer selector and permissions depending action.
    """
    serializer_class = serializers.CommentSerializer
    permission_classes = [IsAdminPermission | IsAuthenticatedOrReadOnly]
    permission_classes_by_action = {
        "create": [IsAuthenticated],
        "list": [IsAuthenticatedOrReadOnly],
        "partial_update": [IsOwner],
        "destroy": [IsOwner],
    }

    def get_queryset(self):
        review = get_object_or_404(Review, pk=self.kwargs.get('review_id'))
        queryset = review.comments.all()
        return queryset

    def perform_create(self, serializer):
        review = get_object_or_404(Review, id=self.kwargs.get('review_id'))
        serializer.save(author=self.request.user, review=review)

    def get_permissions(self):
        try:
            return [
                permission()
                for permission in self.permission_classes_by_action[
                    self.action
                ]
            ]
        except KeyError:
            return [permission() for permission in self.permission_classes]
