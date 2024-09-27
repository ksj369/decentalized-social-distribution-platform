from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from ..views import *
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

app_name = "lostapp_api"
urlpatterns = [
    path("authors/", authors, name="profile_list"),
    path("authors/<uuid:author_id>/", single_author, name="author"),
    path("authors/<uuid:author_id>/followers/", author_followers, name="followers"),
    path("authors/<uuid:author_id>/check_follow_status/<uuid:follower_id>", check_follow_status, name="check_follow_status"),
    path(
        "authors/<uuid:author_id>/followers/<uuid:follower_id>",
        single_follower,
        name="following",
    ),
    path(
        "authors/<uuid:author_id>/posts/<uuid:post_id>/",
        single_post,
        name="single_post",
    ),
    path("authors/<uuid:author_id>/posts/", posts, name="posts"),
    path("authors/posts/all", all_posts, name="all_posts"),
    path(
        "authors/pending_follow_requests/",
        fetch_pending_follow_requests,
        name="fetch_pending_follow_requests",
    ),
    path(
        "authors/<uuid:author_id>/posts/<uuid:post_id>/image/",
        image_post,
        name="post_image",
    ),
    path(
        "authors/<uuid:author_id>/posts/<uuid:post_id>/comments/",
        comments,
        name="comments",
    ),
    path("authors/<uuid:author_id>/posts/<uuid:post_id>/likes/", likes, name="likes"),
    path(
        "authors/<uuid:author_id>/posts/<uuid:post_id>/comments/<uuid:comment_id>/likes/",
        likes,
        name="comment_likes",
    ),
    path("authors/<uuid:author_id>/liked/", liked, name="liked"),
    path("authors/<uuid:author_id>/inbox/", inbox, name="inbox"),
    path(
        "authors/<uuid:author_id>/request/<path:follower_id>",
        pending_follow_request,
        name="pending_follow_request",
    ),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    # Optional UI:
    path(
        "schema/swagger-ui/",
        SpectacularSwaggerView.as_view(url_name="lostapp:lostapp_api:schema"),
        name="swagger-ui",
    ),
    path(
        "schema/redoc/",
        SpectacularRedocView.as_view(url_name="lostapp:lostapp_api:schema"),
        name="redoc",
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
