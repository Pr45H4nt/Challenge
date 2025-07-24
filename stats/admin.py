from django.contrib import admin
from .models import Notice

# Register your models here.

class NoticeAdmin(admin.ModelAdmin):
    model = Notice
    list_display = ['room', 'author', 'title', 'is_pinned', 'created_on', 'is_posted_today']
    search_fields = ['room', 'author', 'title', 'content', 'created_on']


admin.site.register(Notice, NoticeAdmin)

