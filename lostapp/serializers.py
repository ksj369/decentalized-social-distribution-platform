from rest_framework import serializers
from .models import *


class AuthorSerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    host = serializers.CharField()
    displayName = serializers.CharField(source="display_name")
    github = serializers.CharField()
    profileImage = serializers.SerializerMethodField()

    def get_type(self, obj):
        return "author"

    def get_id(self, obj):
        if obj.is_remote:
            return f"{settings.HOSTNAME}authors/{obj.id}"
        else:
            return f"{obj.host}authors/{obj.id}"

    def get_url(self, obj):
        if obj.is_remote == True:
            return f"{settings.HOSTNAME}authors/{obj.id}"
        else:
            return f"{obj.host}authors/{obj.id}"

    def get_profileImage(self, obj):
        if obj.is_remote:
            if obj.profile_image is None or obj.profile_image == "":
                return f"{settings.HOSTNAME}media/default.jpg"
            else:
                return f"{obj.profile_image}"
        else:
            return f"{obj.host}{obj.profile_image.url.lstrip('/')}"

    def create(self, validated_data):
        return Author.objects.create(
            **validated_data, date_joined=None, is_approved=False
        )

    def update(self, instance, validated_data):
        instance.display_name = validated_data.get(
            "display_name", instance.display_name
        )
        instance.profile_image = validated_data.get(
            "profile_image", instance.profile_image
        )
        instance.github = validated_data.get("github", instance.github)
        instance.save()
        return instance


class LikeSerializer(serializers.Serializer):
    summary = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()
    author = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()

    def get_type(self, obj):
        return "Like"

    def get_summary(self, obj):
        return obj.__str__()

    def get_author(self, obj):
        return AuthorSerializer(obj.author).data

    def get_object(self, obj):
        if obj.post:
            return PostSerializer(obj.post).data["id"]
        else:
            return CommentSerializer(obj.comment).data["id"]

    def create(self, validated_data):
        return Like.objects.create(**validated_data)


class FollowSerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    summary = serializers.SerializerMethodField()
    actor = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()

    def get_type(self, obj):
        return "Follow"

    def get_summary(self, obj):
        actor_name = self.get_actor(obj)["displayName"]
        object_name = self.get_object(obj)["displayName"]
        return f"{actor_name} wants to follow {object_name}"

    def get_actor(self, obj):
        return AuthorSerializer(obj).data

    def get_object(self, obj):
        reciever = self.context.get("reciever")
        return AuthorSerializer(reciever).data


# class InboxSerializer(serializers.Serializer):
#     type = serializers.SerializerMethodField()
#     author = serializers.SerializerMethodField()
#     item = serializers.SerializerMethodField()
#
#     def get_type(self, obj):
#         return "inbox"
#
#     def get_author(self, obj):
#         return f"{settings.HOSTNAME}/authors/{obj.author_id}"
#
#     def get_item(self, obj):
#         return obj.item


class ContentTypeField(serializers.Field):
    def to_representation(self, value):
        content_format = {
            1: "text/plain",
            2: "text/markdown",
            3: "image/png",
        }
        return content_format.get(value)

    def to_internal_value(self, data):
        content_format_reverse = {
            "text/plain": 1,
            "text/markdown": 2,
            "image/png": 3,
        }
        return content_format_reverse.get(data)


class PostSerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    title = serializers.CharField()
    id = serializers.SerializerMethodField()
    source = serializers.SerializerMethodField()
    origin = serializers.SerializerMethodField()
    description = serializers.CharField()
    contentType = ContentTypeField(source="content_format")
    content = serializers.CharField()
    author = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()
    visibility = serializers.SerializerMethodField()

    def get_type(self, obj):
        return "post"

    def get_id(self, obj):
        return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}"

    def get_description(self, obj):
        return obj.content[:50]

    def get_source(self, obj):
        return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}"

    def get_origin(self, obj):
        return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.id}"

    def get_author(self, obj):
        return AuthorSerializer(obj.author).data

    def get_visibility(self, obj):
        if obj.visibility == 1:
            return "PUBLIC"
        elif obj.visibility == 2:
            return "UNLISTED"
        elif obj.visibility == 3:
            return "FRIENDS"

    def get_count(self, obj):
        return 0

    def get_published(self, obj):
        return obj.date_posted.isoformat()

    def create(self, validated_data):
        return Post.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.title = validated_data.get("title", instance.title)
        instance.content_format = validated_data.get(
            "content_format", instance.content_format
        )
        instance.content = validated_data.get("content", instance.content)
        instance.save()
        return instance


class CommentSerializer(serializers.Serializer):
    type = serializers.SerializerMethodField()
    author = AuthorSerializer()
    comment = serializers.CharField()
    contentType = serializers.SerializerMethodField()
    published = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    def get_type(self, obj):
        return "comment"

    def get_id(self, obj):
        return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.post.id}/comments"

    def get_contentType(self, obj):
        return obj.contentType

    def get_published(self, obj):
        return obj.published.isoformat()

    def get_id(self, obj):
        return f"{obj.author.host}authors/{obj.author.id}/posts/{obj.post.id}/comments/{obj.id}"

    def create(self, validated_data):
        return Comment.objects.create(**validated_data)
