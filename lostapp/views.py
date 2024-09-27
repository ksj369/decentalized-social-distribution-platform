import base64
import json
import logging
from functools import wraps
from urllib.parse import urljoin, unquote
from uuid import UUID

import requests
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.paginator import Paginator
from django.core.validators import validate_email
from django.db import IntegrityError
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import View
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import *
from django.contrib.auth.decorators import login_required
logger = logging.getLogger(__name__)


def index(request):
    fetch_github()
    context = {}
    if request.user.is_authenticated:
        # follow_requests = Inbox.objects.filter(author=request.user.author, type=Inbox.Type.FOLLOW)
        follow_requests = Inbox.objects.filter(author=request.user.author)
        context["follow_requests"] = follow_requests
    return render(request, "home.html", context)


def signup(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        display_name = request.POST["display_name"]
        github = request.POST["github"]

        # Validate email format
        try:
            validate_email(email)
        except ValidationError:
            # Render the signup page with an error message
            return render(
                request,
                "registration/signup.html",
                {"error_message": "Invalid email format."},
            )

        # Check if the email is already associated with an existing account
        if User.objects.filter(email=email).exists():
            # Render the signup page with an error message
            return render(
                request,
                "registration/signup.html",
                {
                    "error_message": "Email is already associated with an existing account."
                },
            )

        # Check if the username is already taken
        if User.objects.filter(username=username).exists():
            # Render the signup page with an error message
            return render(
                request,
                "registration/signup.html",
                {"error_message": "Username is already taken."},
            )

        # # Check if the display name is already taken
        # if Author.objects.filter(display_name=display_name).exists():
        #     # Render the signup page with an error message
        #     return render(request, 'registration/signup.html', {'error_message': 'Display name is already taken.'})

        # Check if profile image is provided
        if "profile_image" in request.FILES:
            profile_image = request.FILES["profile_image"]
        else:
            # Define the path to the default image
            profile_image = "../media/default.jpg"

        try:
            # Create a new User instance
            user = User.objects.create_user(
                username=username, email=email, password=password
            )

            # Create a new Author instance
            author = Author.objects.create(
                user=user,
                display_name=display_name,
                github=github,
                profile_image=profile_image,
            )

            # Redirect to the login page
            return redirect("login")

        except IntegrityError:
            # Render the signup page with an error message
            return render(
                request,
                "registration/signup.html",
                {"error_message": "An error occurred. Please try again."},
            )

    return render(request, "registration/signup.html")


def author_profile(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    return render(request, "authors/profile.html", {"author": author})


def send_follow_request(request):
    if request.method == "POST":
        target_author_id = request.POST.get("author_id")
        target_author = get_object_or_404(Author, id=target_author_id)
        current_user_profile = request.user.author

        if (
            current_user_profile != target_author
        ):  # Ensure the user is not trying to follow themselves
            target_author.pending_follow_requests.add(current_user_profile)
            return JsonResponse(
                {"status": "success", "message": "Follow request sent successfully"}
            )
        else:
            return JsonResponse(
                {
                    "status": "error",
                    "message": "You cannot send a follow request to yourself",
                }
            )


@extend_schema(
    exclude=True,
)
@api_view(["GET"])
def fetch_pending_follow_requests(request):
    if request.method == "GET" and request.user.is_authenticated:
        current_user = request.user.author
        current_user_profile = get_object_or_404(Author, id=current_user.id)
        pending_requests = current_user_profile.pending_follow_requests.all()
        # Serialize pending requests data as needed
        pending_requests_data = [
            {
                "authorId": current_user.id,
                "actor": pending.id,
                "displayName": pending.display_name,
                "profileImage": pending.profile_image.url,
                "github": pending.github,
                "date_joined": pending.date_joined.strftime("%Y-%m-%d %H:%M:%S"),
            }
            for pending in pending_requests
        ]

        return Response(pending_requests_data)
    else:
        return None


class SinglePostView(View):
    """Class for handling requests for single posts."""

    def get(self, request, author_id, post_id):
        post = get_object_or_404(Post, id=post_id, author_id=author_id)
        return render(
            request,
            "single_post/index.html",
        )


def author_list(request):
    return render(request, "authors/author_list.html")


def post_create(request, author_id):
    """Function for rendering post creation page."""
    return render(request, "posts/create_post.html", context={"author_id": author_id})


def post_edit(request, author_id, post_id):
    """Function for rendering edit post page. Will not allow user to
    edit posts from other users.
    """
    # Only allow editing own posts.
    post = get_object_or_404(Post, id=post_id, author_id=author_id)

    if request.user.author.id != post.author_id:
        return HttpResponse("You are not allowed to edit this post.", status=403)

    return render(request, "posts/edit_post.html")


def profile_change(request, author_id):
    """API function for saving change in user profile."""
    author = get_object_or_404(Author, id=author_id)
    if request.method == "POST":
        # Overwrite fields only if input provided.
        if request.POST.get("display_name"):
            author.display_name = request.POST.get("display_name")
        if request.POST.get("github"):
            author.github = request.POST.get("github")

        # Add author_id before picture name to make sure not overwrite same images
        # for different users in case the picture has the same name.
        new_profile_image = request.FILES.get("profile_image")
        if new_profile_image:
            author.profile_image = SimpleUploadedFile(
                f"{author_id}-{new_profile_image.name}", new_profile_image.read()
            )
        author.save()

        # Redirect to profile page
        return redirect(f"/authors/{author_id}")


def edit_profile(request):
    """Function for rendering edit profile page."""
    author = get_object_or_404(Author, id=request.user.author.id)
    return render(request, "authors/edit_profile.html", {"author": author})


def display_post_image(request, author_id, post_id):
    post = get_object_or_404(Post, id=post_id, author_id=author_id)
    format, imgstr = post.content.split(";base64,")
    if post.content_format == Post.Format.IMAGE:
        image_decoded = base64.b64decode(imgstr)
        return HttpResponse(image_decoded, content_type="image/jpg")


class CommentsView(View):
    """Class for handling requests for comments."""

    def post(self, request, author_id, post_id):
        post = get_object_or_404(Post, id=post_id)
        comment_content = request.POST.get("comment_content", "")
        if comment_content:
            Comment.objects.create(
                post=post,
                author=request.user.author,
                comment=comment_content,
            )
            return HttpResponseRedirect(
                reverse("lostapp:single_post", args=[author_id, post_id]), status=303
            )
        else:
            return HttpResponse("Error adding comment", status=400)

    def get(self, request, author_id, post_id):
        post = get_object_or_404(Post, id=post_id)
        comments_list = post.comments.all().order_by("-published")
        page = request.GET.get("page", 1)
        size = request.GET.get("size", 10)
        paginator = Paginator(comments_list, size)
        page_object = paginator.get_page(page)
        host = settings.HOSTNAME
        comments_data = []

        for comment in page_object:
            common_url = urljoin(
                host, reverse("lostapp:author", args=[comment.author.id])
            )
            comments_data.append(
                {
                    "type": "comment",
                    "author": {
                        "type": "author",
                        "id": common_url,
                        "url": common_url,
                        "host": host,
                        "displayName": comment.author.display_name,
                        "github": comment.author.github,
                        "profileImage": (
                            comment.author.profile_image.url
                            if comment.author.profile_image
                            else ""
                        ),
                    },
                    "comment": comment.comment,
                    "contentType": comment.contentType,
                    "published": comment.published.isoformat(),
                    "id": urljoin(
                        host,
                        reverse("lostapp:comments", args=[post.author_id, post_id])
                        + str(comment.id),
                    ),
                }
            )

        json_data = {
            "type": "comments",
            "page": page,
            "size": size,
            "post": urljoin(
                host, reverse("lostapp:single_post", args=[post.author_id, post_id])
            ),
            "id": urljoin(
                host, reverse("lostapp:comments", args=[post.author_id, post_id])
            ),
            "comments": comments_data,
        }

        return JsonResponse(json_data)


@extend_schema(
    tags=["Local", "Remote"],
    methods=["GET"],
    request=None,
    responses={200: AuthorSerializer(many=True)},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "authors",
                "items": [
                    {
                        "type": "author",
                        "id": "string",
                        "url": "string",
                        "host": "string",
                        "displayName": "string",
                        "github": "string",
                        "profileImage": "string",
                    }
                ],
            },
        )
    ],
)
@api_view(["GET"])
def authors(request):
    authors_list = Author.objects.filter(is_approved=True)
    serializer = AuthorSerializer(authors_list, many=True)
    specification_data = {"type": "authors", "items": serializer.data}
    return Response(specification_data)


@extend_schema(
    tags=["Local", "Remote"],
    methods=["GET"],
    request=None,
    responses={200: AuthorSerializer},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "author",
                "id": "string",
                "url": "string",
                "host": "string",
                "displayName": "string",
                "github": "string",
                "profileImage": "string",
            },
        )
    ],
)
@extend_schema(
    tags=["Local"],
    methods=["PUT"],
    request=AuthorSerializer,
    responses={200: AuthorSerializer},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "author",
                "id": "string",
                "url": "string",
                "host": "string",
                "displayName": "string",
                "github": "string",
                "profileImage": "string",
            },
        )
    ],
)
@api_view(["GET", "PUT"])
def single_author(request, author_id):
    if request.method == "GET":
        author = Author.objects.get(id=author_id)
        if author.is_remote:
            node = author.related_node
            userpass = node.username + ":" + node.password
            encoded = base64.b64encode(userpass.encode()).decode()
            response = requests.get(
                f"{node.url}api/authors/{author_id}",
                headers={"Authorization": "Basic" + " " + encoded},
            )
            if response.status_code == 200:
                serializer = AuthorSerializer(author)
                return Response(serializer.data)
            else:
                return HttpResponse(status=response.status_code)
        serializer = AuthorSerializer(author)
        return Response(serializer.data)
    elif request.method == "PUT":
        author = Author.objects.get(id=author_id)
        serializer = AuthorSerializer(
            author, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.data)


@extend_schema(
    tags=["Local", "Remote"],
    request=None,
    responses={200: AuthorSerializer},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "followers",
                "items": [
                    {
                        "type": "author",
                        "id": "string",
                        "url": "string",
                        "host": "string",
                        "displayName": "string",
                        "github": "string",
                        "profileImage": "string",
                    }
                ],
            },
        )
    ],
)
@api_view(["GET"])
def author_followers(request, author_id):
    author = Author.objects.get(id=author_id)
    if author.is_remote:
        node = author.related_node
        userpass = node.username + ":" + node.password
        encoded = base64.b64encode(userpass.encode()).decode()
        response = requests.get(
            f"{node.url}api/authors/{author_id}/followers",
            headers={"Authorization": "Basic" + " " + encoded},
        )
        if response.status_code == 200:
            remote_author_followers_data = response.json()
            return Response(remote_author_followers_data)
        else:
            return HttpResponse(status=response.status_code)
    else:
        followers = author.follows.all()
        serializer = AuthorSerializer(followers, many=True)
        data = {"type": "followers", "items": serializer.data}
        return Response(data)

     
@extend_schema(
    exclude=True,
)
@api_view(["GET"])
def check_follow_status(request,author_id,follower_id):
    if request.method == "GET":
        
        author = Author.objects.get(id=author_id)
        follower = Author.objects.get(id=follower_id)
        if author.followers.filter(id=follower.id).exists():
            return HttpResponse(status=200)
        else:
            return HttpResponse(status=202)

@extend_schema(
    exclude=True,
)
@api_view(["PUT", "DELETE"])
def pending_follow_request(request, author_id, follower_id):
    author = get_object_or_404(Author, id=author_id)
    logger.info(f"Author: {author}")

    author = get_object_or_404(Author, id=request.user.author.id)
    follower = get_object_or_404(Author, id=follower_id)
    if request.method == "PUT":

        # Add the author to followers and add the follower id to the author's following

        author.followers.add(follower)
        follower.follows.add(author)
        author.pending_follow_requests.remove(follower)
        Inbox.objects.filter(author_id=author_id, item=follower_id).delete()
        return HttpResponse(status=201)

    elif request.method == "DELETE":

        # Remove the pending request
        author.pending_follow_requests.remove(follower)
        Inbox.objects.filter(author_id=author_id, item=follower_id).delete()
        return HttpResponse(status=204)


# TODO: REMOTE AFTER FOLLOWING IS FINISHED
@extend_schema(
    tags=["Local", "Remote"],
    methods=["GET"],
    request=None,
    responses={200: FollowSerializer, 404: None},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "Follow",
                "summary": "string",
                "actor": {
                    "type": "author",
                    "id": "string",
                    "url": "string",
                    "host": "string",
                    "displayName": "string",
                    "github": "string",
                    "profileImage": "string",
                },
                "object": {
                    "type": "author",
                    "id": "string",
                    "url": "string",
                    "host": "string",
                    "displayName": "string",
                    "github": "string",
                    "profileImage": "string",
                },
            },
        )
    ],
)
@extend_schema(
    tags=["Local", "Remote"],
    methods=["PUT"],
    request=None,
    responses={201: None},
)
@extend_schema(
    tags=["Local"],
    methods=["DELETE"],
    request=None,
    responses={204: None},
)
@api_view(["GET", "PUT", "DELETE"])
def single_follower(request, author_id, follower_id):
    author = get_object_or_404(Author, id=author_id)
    logger.info(f"Author: {author}")
    print("here:",follower_id)
    # follower_uuid = unquote(follower_id).split("/")[-1]
    # logger.info(f"Follower UUID: {follower_uuid}")
    follower_uuid = follower_id

    if request.method == "GET":
        follower = get_object_or_404(Author, id=follower_uuid)
        if author.followers.filter(id=follower.id).exists():
            response_data = {
                "type": "Follow",
                "summary": f"{follower.display_name} follows {author.display_name}",
                "actor": AuthorSerializer(follower).data,
                "object": AuthorSerializer(author).data,
            }
            return JsonResponse(response_data)
        else:
            return HttpResponse("Follower does not follow author", status=404)

    elif request.method == "PUT":
        if request.user.is_authenticated:
            follower = Author.objects.get(id=follower_uuid)
            if not follower:
                json = request.data
                follower = Author.objects.create(
                    id=follower_uuid,
                    host=json.get("host"),
                    display_name=json.get("displayName"),
                    profile_image=json.get("profileImage"),
                    github=json.get("github"),
                    date_joined=None,
                    is_approved=False,
                )
            # author.followers.add(follower)
            response_data = {
                "type": "Follow",
                "summary": f"{follower.display_name} follows {author.display_name}",
                "actor": AuthorSerializer(follower).data,
                "object": AuthorSerializer(author).data,
            }
            # author.pending_follow_requests.add(follower)
            return HttpResponse(status=201)

    elif request.method == "DELETE":
        follower = get_object_or_404(Author, id=follower_uuid)
        print(follower)
        author.follows.remove(follower)
        follower.followers.remove(author)
        return HttpResponse(status=204)


@extend_schema(
    tags=["Local", "Remote"],
    methods=["GET"],
    request=None,
    responses={200: PostSerializer},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "post",
                "title": "string",
                "id": "string",
                "source": "string",
                "origin": "string",
                "description": "string",
                "contentType": "string",
                "content": "string",
                "author": {
                    "type": "author",
                    "id": "string",
                    "url": "string",
                    "host": "string",
                    "displayName": "string",
                    "github": "string",
                    "profileImage": "string",
                },
                "count": "integer",
                "comments": "string",
                "published": "datetime",
                "visibility": "string",
            },
        )
    ],
)
@extend_schema(
    tags=["Local"],
    methods=["PUT"],
    request=PostSerializer,
    responses={303: PostSerializer},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "post",
                "title": "string",
                "id": "string",
                "source": "string",
                "origin": "string",
                "description": "string",
                "contentType": "string",
                "content": "string",
                "author": {
                    "type": "author",
                    "id": "string",
                    "url": "string",
                    "host": "string",
                    "displayName": "string",
                    "github": "string",
                    "profileImage": "string",
                },
                "count": "integer",
                "comments": "string",
                "published": "datetime",
                "visibility": "string",
            },
        ),
    ],
)
@extend_schema(
    tags=["Local"],
    methods=["DELETE"],
    request=None,
    responses={204: None},
)
@api_view(["GET", "DELETE", "PUT"])
def single_post(request, author_id, post_id):
    post = get_object_or_404(Post, id=post_id, author_id=author_id)
    author = get_object_or_404(Author, id=author_id)
    if request.method == "GET":
        if author.is_remote:
            node = author.related_node
            userpass = node.username + ":" + node.password
            encoded = base64.b64encode(userpass.encode()).decode()
            response = requests.get(
                f"{author.host}api/authors/{author_id}/posts/{post_id}/",
                headers={"Authorization": "Basic" + " " + encoded},
            )
            if response.status_code == 200:
                remote_author_post_data = response.json()
                for post_data in remote_author_post_data:
                    """uuid = author_data.get("id").split('/')[-1]
                    author, created = Author.objects.get_or_create(
                        id=uuid,
                        defaults={
                            'host': author_data.get("host"),
                            'display_name': author_data.get("displayName"),
                            'profile_image': author_data.get("profileImage"),
                            'github': author_data.get("github"),
                            'date_joined': None,
                            'is_approved': True,
                            'is_remote': True,
                        }
                    )
                    remote_authors_list.append(author)"""
                return Response(response.status_code)
            else:
                return Response(response.status_code)
        else:
            serializer = PostSerializer(post)
            return Response(serializer.data)
    if request.method == "DELETE":
        post.delete()
        Inbox.objects.filter(item=post_id).delete()
        return Response(status=204)
    if request.method == "PUT":
        serializer = PostSerializer(post, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=303)
        return Response(serializer.errors)


# TODO: MAKE IT WORK ONLY AFTER LOCAL FOLLOWS REMOTE AUTHOR
@extend_schema(
    tags=["Local", "Remote"],
    methods=["GET"],
    request=None,
    responses={200: PostSerializer(many=True)},
    examples=[
        OpenApiExample(
            name="",
            value=[
                {
                    "type": "post",
                    "title": "string",
                    "id": "string",
                    "source": "string",
                    "origin": "string",
                    "description": "string",
                    "contentType": "string",
                    "content": "string",
                    "author": {
                        "type": "author",
                        "id": "string",
                        "url": "string",
                        "host": "string",
                        "displayName": "string",
                        "github": "string",
                        "profileImage": "string",
                    },
                    "count": "integer",
                    "comments": "string",
                    "published": "datetime",
                    "visibility": "string",
                }
            ],
        )
    ],
)
@extend_schema(
    tags=["Local"],
    methods=["POST"],
    request=PostSerializer,
    responses={201: PostSerializer},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "post",
                "title": "string",
                "id": "string",
                "source": "string",
                "origin": "string",
                "description": "string",
                "contentType": "string",
                "content": "string",
                "author": {
                    "type": "author",
                    "id": "string",
                    "url": "string",
                    "host": "string",
                    "displayName": "string",
                    "github": "string",
                    "profileImage": "string",
                },
                "count": "integer",
                "comments": "string",
                "published": "datetime",
                "visibility": "string",
            },
        ),
    ],
)
@api_view(["GET", "POST"])
def posts(request, author_id):
    if request.method == "GET":
        author = get_object_or_404(Author, id=author_id)
        if author.is_remote:
            node = author.related_node
            userpass = node.username + ":" + node.password
            encoded = base64.b64encode(userpass.encode()).decode()
            response = requests.get(
                f"{author.host}api/authors/{author_id}/posts/",
                headers={"Authorization": "Basic" + " " + encoded},
            )
            if response.status_code == 200:
                remote_author_posts_data = response.json()
                return Response(remote_author_posts_data)
            else:
                return Response(response.status_code)
        else:
            posts_public = Post.objects.filter(visibility=1)
            posts_public = posts_public.filter(author_id=author_id)
            if request.user.is_authenticated:
                if request.user.author.id == author_id:
                    posts = Post.objects.filter(author=request.user.author)
                    post_list = posts_public | posts
                    post_list = post_list.order_by("-date_posted")
                    serializer = PostSerializer(post_list, many=True)
                    return Response(serializer.data)
                else:
                    current_follows = request.user.author.follows.all()
                    friends = current_follows.filter(follows=request.user.author)
                    posts_friend = Post.objects.filter(author__in=friends)
                    posts_friend.filter(visibility=3)
                    post_list = posts_public | posts_friend
                    post_list = post_list.order_by("-date_posted")
                    serializer = PostSerializer(post_list, many=True)
                    return Response(serializer.data)
            elif request.user.is_anonymous:
                posts_public = posts_public.order_by("-date_posted")
                serializer = PostSerializer(posts_public, many=True)
                return Response(serializer.data)

    if request.method == "POST":
        author = get_object_or_404(Author, id=author_id)
        data = request.data
        # create post
        post = Post.objects.create(
            title=data.get("title"),
            description=data.get("description"),
            author=author,
            content_format=ContentTypeField().to_internal_value(
                data.get("contentType")
            ),
            content=data.get("content"),
            date_posted=(
                data.get("published") if data.get("published") else timezone.now()
            ),
            visibility={"PUBLIC": 1, "UNLISTED": 2, "FRIENDS": 3}.get(
                data.get("visibility")
            ),
        )
        post.origin = post.source = (
            f"{request.scheme}://{request.get_host()}"
            + reverse("lostapp:lostapp_api:single_post", args=[author_id, post.id])
        )
        post.save()
        serializer = PostSerializer(post)
        return Response(serializer.data, status=201)


@extend_schema(
    exclude=True,
)
@api_view(["GET"])
def all_posts(request):
    if request.method == "GET":
        posts_public = Post.objects.filter(visibility=Post.Visibility.PUBLIC)
        if request.user.is_authenticated:
            author = Author.objects.get(id=request.user.author.id)
            post_list = posts_public

            # Add friends only posts to stream.
            for friend in author.get_friends():
                friend_posts = Post.objects.filter(
                    visibility=Post.Visibility.FRIENDS, author=friend
                )
                post_list |= friend_posts

            post_list = post_list.order_by("-date_posted")
            serializer = PostSerializer(post_list, many=True)
            return Response(serializer.data)

        elif request.user.is_anonymous:
            posts_public = posts_public.order_by("-date_posted")
            serializer = PostSerializer(posts_public, many=True)
            return Response(serializer.data)


# TODO: REMOTE
@extend_schema(
    tags=["Local", "Remote"],
    methods=["GET"],
    request=None,
    responses={200: str},
)
@api_view(["GET"])
def image_post(request, author_id, post_id):
    post = Post.objects.get(id=post_id)
    if post.content_format == Post.Format.IMAGE:
        image_format, img_str = post.content.split(";base64,")
        image_decoded = base64.b64decode(img_str)
        return HttpResponse(image_decoded, content_type="image/jpg")
    else:
        return JsonResponse({"error": "Post is not an image"}, status=404)


# TODO: REMOTE
@extend_schema(
    tags=["Local", "Remote"],
    methods=["GET"],
    request=None,
    responses={200: CommentSerializer(many=True)},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "comments",
                "page": "integer",
                "size": "integer",
                "post": "string",
                "id": "string",
                "comments": [
                    {
                        "type": "comment",
                        "author": {
                            "type": "author",
                            "id": "string",
                            "url": "string",
                            "host": "string",
                            "displayName": "string",
                            "github": "string",
                            "profileImage": "string",
                        },
                        "comment": "string",
                        "contentType": "text/markdown",
                        "published": "datetime",
                        "id": "string",
                    }
                ],
            },
        )
    ],
)
@extend_schema(
    tags=["Local"],
    methods=["POST"],
    request=CommentSerializer,
    responses={201: CommentSerializer},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "comment",
                "author": {
                    "type": "author",
                    "id": "string",
                    "url": "string",
                    "host": "string",
                    "displayName": "string",
                    "github": "string",
                    "profileImage": "string",
                },
                "comment": "string",
                "contentType": "text/markdown",
                "published": "datetime",
                "id": "string",
            },
        ),
    ],
)
@api_view(["GET", "POST"])
def comments(request, author_id, post_id):
    if request.method == "GET":
        post = Post.objects.get(id=post_id)
        comments = post.comments.all()
        serializer = CommentSerializer(comments, many=True)

        paginator = Paginator(comments, 5)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        return Response(
            {
                "type": "comment",
                "page": page_obj.number,
                "size": paginator.per_page,
                "comments": serializer.data,
            }
        )
    if request.method == "POST":
        post = Post.objects.get(id=post_id)
        json = request.data
        author = Author.objects.get(id=json.get("author"))
        comment = Comment.objects.create(
            post=post,
            author=author,
            comment=json.get("comment"),
            contentType=json.get("contentType"),
        )
        comment.save()
        serializer = CommentSerializer(comment)
        return Response(serializer.data, status=201)


@extend_schema(
    tags=["Local"],
    methods=["GET"],
    request=None,
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "inbox",
                "author": "string",
                "items": [
                    {
                        "type": "post",
                        "title": "string",
                        "id": "string",
                        "source": "string",
                        "origin": "string",
                        "description": "string",
                        "contentType": "string",
                        "content": "string",
                        "author": {
                            "type": "author",
                            "id": "string",
                            "url": "string",
                            "host": "string",
                            "displayName": "string",
                            "github": "string",
                            "profileImage": "string",
                        },
                        "count": "integer",
                        "comments": "string",
                        "published": "datetime",
                        "visibility": "string",
                    },
                    {
                        "summary": "string",
                        "type": "Like",
                        "author": {
                            "type": "author",
                            "id": "string",
                            "url": "string",
                            "host": "string",
                            "displayName": "string",
                            "github": "string",
                            "profileImage": "string",
                        },
                        "object": "string",
                    },
                    {
                        "type": "Follow",
                        "summary": "string",
                        "actor": {
                            "type": "author",
                            "id": "string",
                            "url": "string",
                            "host": "string",
                            "displayName": "string",
                            "github": "string",
                            "profileImage": "string",
                        },
                        "object": {
                            "type": "author",
                            "id": "string",
                            "url": "string",
                            "host": "string",
                            "displayName": "string",
                            "github": "string",
                            "profileImage": "string",
                        },
                    },
                    {
                        "type": "comment",
                        "author": {
                            "type": "author",
                            "id": "string",
                            "url": "string",
                            "host": "string",
                            "displayName": "string",
                            "github": "string",
                            "profileImage": "string",
                        },
                        "comment": "string",
                        "contentType": "text/markdown",
                        "published": "datetime",
                        "id": "string",
                    },
                ],
            },
        )
    ],
)
@extend_schema(
    tags=["Local", "Remote"],
    methods=["POST"],
    responses={201: None},
)
@extend_schema(
    tags=["Local"],
    methods=["DELETE"],
    request=None,
    responses={204: None},
)
@api_view(["GET", "POST", "DELETE"])
def inbox(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    if request.method == "GET":
        inbox_items = Inbox.objects.filter(author=author)
        inbox_posts = inbox_items.filter(type=Inbox.Type.POST)
        inbox_comments = inbox_items.filter(type=Inbox.Type.COMMENT)
        inbox_likes = inbox_items.filter(type=Inbox.Type.LIKE)
        inbox_follows = inbox_items.filter(type=Inbox.Type.FOLLOW)
        serialized_items = []

        for item in inbox_posts:
            post = Post.objects.get(id=item.item)
            serialized_items.append(PostSerializer(post).data)

        for item in inbox_comments:
            comment = Comment.objects.get(id=item.item)
            serialized_items.append(CommentSerializer(comment).data)

        for item in inbox_follows:
            sender = get_object_or_404(Author, id=item.item)
            serializer = FollowSerializer(sender, context={"reciever": author})
            serialized_items.append(serializer.data)

        for item in inbox_likes:
            like = Like.objects.get(id=item.item)
            serialized_items.append(LikeSerializer(like).data)

        return Response(
            {"type": "inbox", "author": author.id, "items": serialized_items}
        )

    elif request.method == "POST":
        # if not basic_auth(request):
        #     return HttpResponse("Unauthorized", status=401)
        data = request.data
        item_type = data.get("type")

        if item_type == "post":
            post_id = data.get("id").split("/")[-1]
            post = Post.objects.get(id=post_id)
            if not post:
                author_json = data.get("author")
                post_author_id = author_json.get("id").split("/")[-1]
                post_author = Author.objects.get(id=post_author_id)
                if not post_author:
                    post_author = Author.objects.create(
                        id=post_author_id,
                        host=author_json.get("host"),
                        display_name=author_json.get("displayName"),
                        profile_image=author_json.get("profileImage"),
                        github=author_json.get("github"),
                        date_joined=None,
                        is_approved=False,
                    )
                post = Post.objects.create(
                    id=post_id,
                    title=data.get("title"),
                    origin=data.get("origin"),
                    source=data.get("id"),
                    description=data.get("description"),
                    author=post_author,
                    content_format=ContentTypeField().to_internal_value(
                        data.get("contentType")
                    ),
                    content=data.get("content"),
                    published=data.get("published"),
                    visibility={"PUBLIC": 1, "UNLISTED": 2, "FRIENDS": 3}.get(
                        data.get("visibility")
                    ),
                )
                comments_response = requests.get(data.get("comments"))
                if comments_response.status_code == 200:
                    comments = comments_response.json().get("comments")
                    for comment in comments:
                        comment_author_json = comment.get("author")
                        comment_author_id = comment_author_json.get("id").split("/")[-1]
                        comment_author = Author.objects.get(id=comment_author_id)
                        if not comment_author:
                            comment_author = Author.objects.create(
                                id=comment_author_id,
                                host=comment_author_json.get("host"),
                                display_name=comment_author_json.get("displayName"),
                                profile_image=comment_author_json.get("profileImage"),
                                github=comment_author_json.get("github"),
                                date_joined=None,
                                is_approved=False,
                            )
                        comment_id = comment.get("id").split("/")[-1]
                        Comment.objects.create(
                            id=comment_id,
                            post=post,
                            author=comment_author,
                            comment=comment.get("comment"),
                            contentType=ContentTypeField().to_internal_value(
                                comment.get("contentType")
                            ),
                            published=comment.get("published"),
                        )

            if not Inbox.objects.filter(author=author, item=post.id).exists():
                Inbox.objects.create(author=author, type=Inbox.Type.POST, item=post.id)
            return Response(status=201)

        elif item_type == "comment":
            comment_id = data.get("id").split("/")[-1]
            comment = Comment.objects.get(id=comment_id)
            if not comment:
                author_json = data.get("author")
                comment_author_id = author_json.get("id").split("/")[-1]
                comment_author = Author.objects.get(id=comment_author_id)
                if not comment_author:
                    comment_author = Author.objects.create(
                        id=comment_author_id,
                        host=author_json.get("host"),
                        display_name=author_json.get("displayName"),
                        profile_image=author_json.get("profileImage"),
                        github=author_json.get("github"),
                        date_joined=None,
                        is_approved=False,
                    )
                post_id = data.get("post").split("/")[-1]
                post = Post.objects.get(id=post_id)
                if not post:
                    post_json = requests.get(data.get("post")).json()
                    post_author_json = post_json.get("author")
                    post_author_id = post_author_json.get("id").split("/")[-1]
                    post_author = Author.objects.get(id=post_author_id)
                    if not post_author:
                        post_author = Author.objects.create(
                            id=post_author_id,
                            host=post_author_json.get("host"),
                            display_name=post_author_json.get("displayName"),
                            profile_image=post_author_json.get("profileImage"),
                            github=post_author_json.get("github"),
                            date_joined=None,
                            is_approved=False,
                        )
                    post = Post.objects.create(
                        id=post_id,
                        title=post_json.get("title"),
                        origin=post_json.get("origin"),
                        source=post_json.get("id"),
                        description=post_json.get("description"),
                        author=post_author,
                        content_format=ContentTypeField().to_internal_value(
                            post_json.get("contentType")
                        ),
                        content=post_json.get("content"),
                        published=post_json.get("published"),
                        visibility={"PUBLIC": 1, "UNLISTED": 2, "FRIENDS": 3}.get(
                            post_json.get("visibility")
                        ),
                    )
                comment = Comment.objects.create(
                    id=comment_id,
                    post=post,
                    author=comment_author,
                    comment=data.get("comment"),
                    contentType=ContentTypeField().to_internal_value(
                        data.get("contentType")
                    ),
                    published=data.get("published"),
                )
            Inbox.objects.create(
                author=author, type=Inbox.Type.COMMENT, item=comment.id
            )
            return Response(status=201)

        elif item_type == "Like":
            liker_id = data.get("author").get("id").split("/")[-1]
            liker = Author.objects.get(id=liker_id)
            if not liker:
                liker = Author.objects.create(
                    id=liker_id,
                    host=data.get("author").get("host"),
                    display_name=data.get("author").get("displayName"),
                    profile_image=data.get("author").get("profileImage"),
                    github=data.get("author").get("github"),
                    date_joined=None,
                    is_approved=False,
                )
            post_id = data.get("object").split("/")[-1]
            post = Post.objects.get(id=post_id)
            like = Like.objects.get(author=liker, post=post)
            if not like:
                like = Like.objects.create(author=liker, post=post)
            Inbox.objects.create(author=author, type=Inbox.Type.LIKE, item=like.id)
            return Response(status=201)

        elif item_type == "Follow":
            sender_id = data.get("actor").get("id").split("/")[-1]
            sender = Author.objects.get(id=sender_id)
            if not sender:
                sender = Author.objects.create(
                    id=sender_id,
                    host=data.get("actor").get("host"),
                    display_name=data.get("actor").get("displayName"),
                    profile_image=data.get("actor").get("profileImage"),
                    github=data.get("actor").get("github"),
                    date_joined=None,
                    is_approved=False,
                )
            
            # print("hereeeeeeeeeeeee",sender.host,sender.display_name, author.host,author.host==sender.host)
            # if sender.host != author.host:
            #    # author.followers.add(sender)
            #     sender.follows.add(author)
            #     #sender.pending_follow_requests.remove(author)
            #     # Inbox.objects.filter(author_id=author_id, item=follower_id).delete()
            # else:
            author.pending_follow_requests.add(sender)
            if sender.host != author.host:
                sender.follows.add(author)



            author.save()
            if not Inbox.objects.filter(author=author, item=sender.id).exists():
                Inbox.objects.create(
                    author=author, type=Inbox.Type.FOLLOW, item=sender.id
                )
            return Response(status=201)

    elif request.method == "DELETE":
        Inbox.objects.filter(author_id=author_id).delete()
        return Response(status=204)


@extend_schema(
    tags=["Local", "Remote"],
    methods=["GET"],
    request=None,
    responses={200: LikeSerializer(many=True)},
    examples=[
        OpenApiExample(
            name="",
            value=[
                {
                    "summary": "string",
                    "type": "Like",
                    "author": {
                        "type": "author",
                        "id": "string",
                        "url": "string",
                        "host": "string",
                        "displayName": "string",
                        "github": "string",
                        "profileImage": "string",
                    },
                    "object": "string",
                }
            ],
        )
    ],
)
@extend_schema(
    methods=["POST"],
    exclude=True,
)
@api_view(["POST", "GET"])
def likes(request, author_id, post_id, comment_id=None):
    if request.method == "POST":
        if comment_id:
            obj = get_object_or_404(Comment, id=comment_id)
            if obj.author == request.user.author:
                return HttpResponse("You can't like your own comment", status=403)
            dup_obj = Like.objects.filter(author=request.user.author, comment=obj)
            duplicate_check = dup_obj.exists()
            if not duplicate_check:
                like, created = Like.objects.get_or_create(
                    author=request.user.author, comment=obj
                )
        else:
            obj = get_object_or_404(Post, id=post_id)
            if obj.author == request.user.author:
                return HttpResponse("You can't like your own post", status=403)
            dup_obj = Like.objects.filter(author=request.user.author, post=obj)
            duplicate_check = dup_obj.exists()
            if not duplicate_check:
                like, created = Like.objects.get_or_create(
                    author=request.user.author, post=obj
                )

        if not duplicate_check:
            serializer = LikeSerializer(like)
            return Response({"like": serializer.data}, status=201)
        else:
            return HttpResponse("You've already liked this post/comment", status=400)

    elif request.method == "GET":
        if comment_id:
            obj = get_object_or_404(Comment, id=comment_id)
            likes = obj.likes.all()
        else:
            obj = get_object_or_404(Post, id=post_id)
            likes = obj.likes.all()
        serializer = LikeSerializer(likes, many=True)
        return Response(serializer.data)


@extend_schema(
    tags=["Local", "Remote"],
    methods=["GET"],
    request=None,
    responses={200: LikeSerializer(many=True)},
    examples=[
        OpenApiExample(
            name="",
            value={
                "type": "liked",
                "items": [
                    {
                        "summary": "string",
                        "type": "Like",
                        "author": {
                            "type": "author",
                            "id": "string",
                            "url": "string",
                            "host": "string",
                            "displayName": "string",
                            "github": "string",
                            "profileImage": "string",
                        },
                        "object": "string",
                    }
                ],
            },
        )
    ],
)
@api_view(["GET"])
def liked(request, author_id):
    author = get_object_or_404(Author, id=author_id)
    if author.is_remote:
        response = requests.get(f"{author.host}api/authors/{author_id}/liked/")
        if response.status_code == 200:
            remote_author_liked = response.json()
            return Response(remote_author_liked)
        else:
            return HttpResponse(status=response.status_code)
    else:
        likes = Like.objects.filter(author=author)
        serializer = LikeSerializer(likes, many=True)

        json_data = {
            "type": "liked",
            "items": serializer.data,
        }
        return Response(json_data)


def fetch_github():

    for author in Author.objects.filter(is_remote=False):
        github_username = author.get_github_username() if author.github else None
        if github_username:
            url = f"https://api.github.com/users/{github_username}/events/public"
            github_response = requests.get(url)
            if github_response.status_code == 200:
                activities = github_response.json()
                for activity in activities:
                    title = f"{author.display_name}'s github activity"
                    time = activity["created_at"]
                    activity_id = activity["id"]
                    # Use this for testing (puts entire json into content)
                    # content = activity
                    content = f"id: **{activity_id}**; **{activity['type']}** made by [**{activity['actor']['login']}**](https://github.com/{github_username}) at **{time}**"

                    if not Post.objects.filter(
                        content__contains=activity_id, author=author
                    ).exists():
                        # post = Post.objects.create(
                        #     title=title,
                        #     content=content,
                        #     author=author,
                        #     visibility=Post.Visibility.PUBLIC,
                        #     content_format=Post.Format.MARKDOWN,
                        #     date_posted=time,
                        #     description=content,
                        # )
                        # post.origin = post.source = author.host + reverse(
                        #     "lostapp:lostapp_api:single_post",
                        #     args=[author.id, post.id],
                        # ).lstrip("/")
                        # post.save()
                        response = requests.post(
                            f"{author.host}api/authors/{author.id}/posts/",
                            json={
                                "title": title,
                                "content": content,
                                "contentType": "text/markdown",
                                "published": time,
                                "visibility": "PUBLIC",
                                "description": content,
                            },
                        )
