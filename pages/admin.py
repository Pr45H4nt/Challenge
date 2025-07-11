from django.contrib import admin
from .models import Todo, Room, Session

# Register your models here.
class TodoAdmin(admin.ModelAdmin):
    list_display = [
        'user','session__room','session', 'task'
    ]
    list_filter = ['user']
    search_fields = ['user__username','task', 'room__name']

class RoomAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'admin', 'created_on'
    ]
    search_fields = ['name', 'admin__username']

admin.site.register(Session)
admin.site.register(Todo, TodoAdmin)
admin.site.register(Room, RoomAdmin)