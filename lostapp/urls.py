from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import *

app_name = "lostapp"
urlpatterns = [
    path("signup/", signup, name="signup"),
    path("authors/<uuid:author_id>/", author_profile, name="author"),
    path("", index, name="index"),
    path(
        "authors/<uuid:author_id>/posts/<uuid:post_id>/",
        SinglePostView.as_view(),
        name="single_post",
    ),
    path("authors/<uuid:author_id>/posts/create/", post_create, name="post_create"),
    path(
        "authors/<uuid:author_id>/posts/<uuid:post_id>/edit/",
        post_edit,
        name="single_post_edit",
    ),
    path(
        "authors/<uuid:author_id>/posts/<uuid:post_id>/comments/",
        CommentsView.as_view(),
        name="comments",
    ),
    path(
        "authors/<uuid:author_id>/posts/<uuid:post_id>/comments/<uuid:comment_id>/",
        CommentsView.as_view(),
        name="single_comments",
    ),
    path("edit_profile/", edit_profile, name="edit_profile"),
    path(
        "authors/<uuid:author_id>/profile_change/",
        profile_change,
        name="profile_change",
    ),
    path(
        "authors/<uuid:author_id>/posts/<uuid:post_id>/image/",
        display_post_image,
        name="post_image",
    ),


    path("api/", include("lostapp.api.urls")),
    path("authors/", author_list, name="author_list"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
