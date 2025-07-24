from .models import Session, Room, Todo
from django.shortcuts import HttpResponse
from django.core.exceptions import PermissionDenied



class MemberRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        room_inst = None

        room_id = self.kwargs.get('room_id')
        session_id = self.kwargs.get('session_id')
        task_id = self.kwargs.get('task_id')

        if room_id:
            room_inst = Room.objects.filter(id=room_id).first()


        elif session_id:
            session_inst = Session.objects.filter(id = session_id).first()
            if session_inst:
                room_inst = session_inst.room

        elif task_id:
            todo = Todo.objects.filter(id=task_id).first()
            if todo:
                room_inst = todo.session.room

        if room_inst:
            if not room_inst.members.filter(id=self.request.user.id):
                return HttpResponse("403: You are not a member of this room", status=403)


        return super().dispatch(request, *args, **kwargs)

class AdminPermRequired:
    def check_admin(self, request, **kwargs):
        room_inst = None

        room_id = kwargs.get('room_id')
        session_id = kwargs.get('session_id')
        task_id = kwargs.get('task_id')

        if room_id:
            room_inst = Room.objects.filter(id=room_id).first()


        elif session_id:
            session_inst = Session.objects.filter(id = session_id).first()
            if session_inst:
                room_inst = session_inst.room

        elif task_id:
            todo = Todo.objects.filter(id=task_id).first()
            if todo:
                room_inst = todo.session.room
        
        if room_inst:
            if room_inst.admin==request.user:
                return True
            
        return False



    
    def dispatch(self, request, *args, **kwargs):
        if not self.check_admin(request,**kwargs):
            return HttpResponse("403: You are not the admin of this room", status=403)


        return super().dispatch(request, *args, **kwargs)
    

class NotDemoUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if self.request.user.username == 'demouser':
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

