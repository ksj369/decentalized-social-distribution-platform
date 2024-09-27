import uuid
from django.db.models.signals import post_save, pre_save
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.dispatch import receiver
from django.db.models.signals import post_delete
import logging
import requests
import base64

logger = logging.getLogger(__name__)

class Node(models.Model):
    url = models.URLField(unique=True)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.url

    def save(self, *args, **kwargs):
        # Make sure url ends with slash.
        if not self.url.endswith("/"):
            self.url += "/"
        super().save(*args, **kwargs)

@receiver(post_save, sender=Node)
def update_remote_authors(sender, instance, created, **kwargs):
    if instance.is_active:
        fetch_and_update_authors(instance)
    else:
        Author.objects.filter(related_node=instance).delete()


def fetch_and_update_authors(node):
    userpass = f"{node.username}:{node.password}"
    encoded = base64.b64encode(userpass.encode()).decode()
    response = requests.get(f"{node.url}api/authors/", headers={'Authorization': 'Basic' + ' ' + encoded})
    if response.status_code == 200:
        remote_authors = response.json()
        for author_data in remote_authors["items"]:
            uuid = author_data.get("id").split('/')[-1]
            if not Author.objects.filter(id=uuid).exists():
                Author.objects.update_or_create(
                    id=uuid,
                    defaults={
                        'host': author_data.get("host"),
                        'display_name': author_data.get("displayName"),
                        'profile_image': author_data.get("profileImage"),
                        'github': author_data.get("github"),
                        'date_joined': None,
                        'is_approved': True,
                        'is_remote': True,
                        'related_node': node
                    }
                )
            else:
                author = Author.objects.get(id=uuid)
                if author.is_remote == True:
                    Author.objects.update_or_create(
                        id=uuid,
                        defaults={
                            'host': author_data.get("host"),
                            'display_name': author_data.get("displayName"),
                            'profile_image': author_data.get("profileImage"),
                            'github': author_data.get("github"),
                            'date_joined': None,
                            'is_approved': True,
                            'is_remote': True,
                            'related_node': node
                        }
                    )
                else:
                    pass



class Author(models.Model):
    """
    Model for an author

    Extends an existing user model instance

    Attributes:
    user: points to the user model an instance of Author extends
    follows: points to many other Author instances
    display_name: displayed name of the Author instance
    profile image: stored image of the Author instance in the 'media' folder
    github: github link of the Author instance
    date joined: records the date when the instance was initialized
    """
    related_node = models.ForeignKey(Node, on_delete=models.CASCADE, blank=True, null=True)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    host = models.CharField(max_length=255, default=settings.HOSTNAME)
    follows = models.ManyToManyField(
        "self",
        related_name="followed_by",
        symmetrical=False,
        blank=True,
    )
    followers = models.ManyToManyField(
        "self",
        related_name="following",
        symmetrical=False,
        blank=True,
    )
    pending_follow_requests = models.ManyToManyField(
        "self",
        related_name="pending_followers",
        symmetrical=False,
        blank=True,
    )
    display_name = models.CharField(max_length=100)
    profile_image = models.ImageField(default="default.jpg", upload_to="profile_pics")
    github = models.CharField(max_length=100, blank=True)
    date_joined = models.DateTimeField(auto_now_add=True, null=True)
    is_approved = models.BooleanField(default=False)
    is_remote = models.BooleanField(default=False)

    def __str__(self):
        if self.user:
            return f"{self.user.username}, author #{self.id}"
        else:
            return f"Author #{self.id} (Remote author)"

    def __repr__(self):
        return f"{self.id}"

    def get_pending_follow_requests(self):
        """
        Retrieves pending follow requests for the author
        """
        return self.pending_follow_requests.all()

    def get_github_username(self):
        if self.github:
            # Assuming the url pattern of each author follows "https://github.com/somename"
            return self.github.split("/").pop()

    def get_friends(self):
        """Returns list of user's friends. Friends are considered to be users who follow a user and is followed by them."""
        friends = []
        follows_set = set(self.follows.all())
        for follower in self.followers.all():
            if follower in follows_set:
                friends.append(follower)
        return friends

class Post(models.Model):
    """
    Model for a social media post.

    Attributes:
    title: Title of post.
    source: Url of where the post was shared from.
    origin: Url of original post.
    description: A brief description of the post.
    author: Author of post.
    content_format: Type of content for post.
    content: Content of post.
    date_published: Date post was published.
    visibility: Visibility status of post.
    """

    class Visibility(models.IntegerChoices):
        PUBLIC = 1
        UNLISTED = 2
        FRIENDS = 3

    class Format(models.IntegerChoices):
        PLAIN_TEXT = 1
        MARKDOWN = 2
        IMAGE = 3

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    source = models.CharField(max_length=255, blank=True)
    origin = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    author = models.ForeignKey(Author, on_delete=models.CASCADE, related_name='posts')
    content_format = models.IntegerField(choices=Format, default=Format.PLAIN_TEXT)
    content = models.TextField()
    date_posted = models.DateTimeField(default=timezone.now)
    visibility = models.IntegerField(choices=Visibility, default=Visibility.PUBLIC)
    is_remote = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.visibility} post: {self.title} id:{self.id} by {self.author} on {self.date_posted}"

    def __repr__(self):
        return f"{self.Visibility(self.visibility).name.capitalize()}_{self.id}"


class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    comment = models.TextField()
    contentType = models.CharField(max_length=100, default="text/markdown")
    published = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment {self.comment} by {self.author.display_name}"


class Inbox(models.Model):
    class Type(models.IntegerChoices):
        POST = 1
        COMMENT = 2
        FOLLOW = 3
        LIKE = 4

    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    type = models.IntegerField(choices=Type)
    item = models.UUIDField()

    def __str__(self):
        return f"{self.author} {self.Type(self.type).name.capitalize()} {self.item}"


class Like(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    author = models.ForeignKey(Author, on_delete=models.CASCADE)
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="likes", null=True, blank=True
    )
    comment = models.ForeignKey(
        Comment, on_delete=models.CASCADE, related_name="likes", null=True, blank=True
    )

    def __str__(self):
        if self.post:
            return f"{self.author.display_name} likes {self.post.id}"
        else:
            return f"{self.author.display_name} likes {self.comment.id}"




