from django.contrib import admin
from .models import Todo, Room, Session , TrackTodo, SessionRanking, RoomRanking, RoomMembership , \
SystemStatus


# Register your models here.
class TodoAdmin(admin.ModelAdmin):
    list_display = [
        'user','session__room','session', 'task'
    ]
    list_filter = ['user']
    search_fields = ['user__username','task', 'room__name']

class MembershipInline(admin.TabularInline):
    model = RoomMembership
    extra = 1

class RoomAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'admin', 'created_on'
    ]
    search_fields = ['name', 'admin__username']
    inlines = [MembershipInline]


class TrackTodoAdmin(admin.ModelAdmin):
    list_display = [
        'todo', 'day', 'hours', 'added_on_time','todo__session', 'todo__user'
    ]
    search_fields = [
        'todo', 'day', 'hours'
    ]

class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'room', 'joined_on']
    list_filter = ['room']

    search_fields = [
        'user__username', 'room__name'
    ]



admin.site.register(Session)
admin.site.register(Todo, TodoAdmin)
admin.site.register(Room, RoomAdmin)
admin.site.register(TrackTodo, TrackTodoAdmin)
admin.site.register(SessionRanking)
admin.site.register(RoomRanking)
admin.site.register(RoomMembership, MembershipAdmin)

admin.site.register(SystemStatus)
