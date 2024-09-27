from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import *


class ProfileInline(admin.StackedInline):
    model = Author


class UserAdmin(UserAdmin):
    model = User
    fieldsets = [("Main Information", {"fields": ("username", "password", "email")})]
    inlines = [ProfileInline]


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ["url", "username", "is_active"]
    search_fields = ["url"]





admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
admin.site.register(Post)
admin.site.register(Inbox)
