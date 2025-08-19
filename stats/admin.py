from django.contrib import admin
from .models import Notice, NoticeReadStatus

# Register your models here.

class NoticeAdmin(admin.ModelAdmin):
    model = Notice
    list_display = ['room', 'author', 'title', 'is_pinned', 'created_on', 'is_posted_today']
    search_fields = ['room', 'author', 'title', 'content', 'created_on']

class NoticeReadAdmin(admin.ModelAdmin):
    model = NoticeReadStatus
    list_display = ['notice', 'user', 'read_on']


admin.site.register(Notice, NoticeAdmin)
admin.site.register(NoticeReadStatus)

