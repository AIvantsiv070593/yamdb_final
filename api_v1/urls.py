from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt

from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import UsersViewSet, send_mail_verify, MyTokenObtainPairView
from . import views

LIST_METHODS = {"get": "list", "post": "create"}

DEL_METHOD = {"delete": "destroy"}

category_list = views.CategoryViewSetList.as_view(LIST_METHODS)
category_detail = views.CategoryViewSetDetail.as_view(DEL_METHOD)
genre_list = views.GenreViewSetList.as_view(LIST_METHODS)
genre_detail = views.GenreViewSetDetail.as_view(DEL_METHOD)

router_v1 = DefaultRouter()
router_v1.register("users", UsersViewSet, basename="users")
router_v1.register("titles", views.TitleViewSet, basename="title")
router_v1.register(
    r"titles/(?P<title_id>\d+)/reviews",
    views.ReviewViewSet,
    basename="Review",
)
router_v1.register(
    r"titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments",
    views.CommentViewSet,
    basename="Comment",
)

urlpatterns = [
    path("auth/email", csrf_exempt(send_mail_verify)),
    path(
        "auth/token",
        MyTokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "token/refresh", TokenRefreshView.as_view(), name="token_refresh"
    ),
    path("categories/", category_list, name="category_list"),
    path(
        "categories/<slug:slug>/", category_detail, name="category_detail"
    ),
    path("genres/", genre_list, name="genres_list"),
    path("genres/<slug:slug>/", genre_detail, name="genres_detail"),
    path("", include(router_v1.urls)),
]
