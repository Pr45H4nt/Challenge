from rest_framework.permissions import BasePermission
from rest_framework import exceptions
from pages.models import Room, Session

class IsMember(BasePermission):
    message = "the user is not the member"

    def has_object_permission(self, request, view, obj):
        return request.user.is_authenticated and request.user not in obj.members.all()

    

class IsAdmin(BasePermission):
    message = "the user is not the admin"
    
    def has_object_permission(self, request, view, obj):
        room = getattr(obj, 'room', obj)
        admin = getattr(room, 'admin', None)
        return request.user.is_authenticated and request.user == admin

    
class ActiveSession(BasePermission):
    message = "cannot modify in old sessions"

    def has_object_permission(self, request, view, obj):
        session = getattr(obj, 'session', obj)
        return session.is_active