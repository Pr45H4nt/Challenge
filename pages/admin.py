from django.contrib import admin
from .models import Todo, Room

# Register your models here.
class TodoAdmin(admin.ModelAdmin):
    list_display = [
        'user','room', 'action'
    ]
    list_filter = ['user']
    search_fields = ['user__username','action', 'room__name']

class RoomAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'admin', 'created_on'
    ]
    search_fields = ['name', 'admin__username']

admin.site.register(Todo, TodoAdmin)
admin.site.register(Room, RoomAdmin)