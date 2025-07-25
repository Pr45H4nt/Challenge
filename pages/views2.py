from django.views.generic import CreateView , DetailView , DeleteView
from .models import Todo, Room, Session, TrackTodo, SessionRanking, CustomUser
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin as LRM
from django.shortcuts import get_object_or_404 , redirect, HttpResponse, render
from django.utils import timezone
from datetime import datetime
from django.http import HttpResponseRedirect , HttpResponseNotAllowed, JsonResponse
from .mixins import MemberRequiredMixin, AdminPermRequired, NotDemoUserMixin
from django.core.exceptions import PermissionDenied
from stats.models import Notice
from django.shortcuts import get_object_or_404
import json
from .decorators import not_demo_user
        



    
class TodoCreateFromSession(LRM,NotDemoUserMixin,MemberRequiredMixin, CreateView):
    fields = ['task',]
    template_name = 'session/addtodo.html'
    model = Todo
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.session = get_object_or_404(Session, id = self.kwargs.get('session_id'))
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def activity_notice(self):
        profile_link = reverse_lazy('profile', kwargs={'username':self.request.user.username})
        user = f"<a href={profile_link}>{self.request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': self.object.session.id})
        task = f"<a href={session_link}>{self.object.task}</a>"

        session = f"<a href={session_link}>{self.object.session.name}</a>"

        # actual content
        title = f"{user} created a new task"
        content = f"<strong>{user}</strong> added the task <em>{task}</em> to the <strong>{session}</strong> session."
        Notice.objects.create(room=self.object.session.room, title=title, content=content, is_html=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['session_id'] = self.kwargs.get('session_id')
        return context
    
    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        if form.fields.get('room'):
            form.fields['room'].queryset = Room.objects.filter(members = self.request.user)
        return form
    
    def get_success_url(self):
        self.activity_notice()
        session_id = self.kwargs.get('session_id')
        return reverse_lazy('session', kwargs = {'session_id': session_id})
    

class RemoveTodoView(LRM,NotDemoUserMixin, DeleteView ):
    model = Todo
    pk_url_kwarg = 'task_id'
    template_name = 'confirm.html'

    def get_object(self, queryset = None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = f"Do you really want to delete {self.get_object().task}"
        context['referer'] = self.request.META.get('HTTP_REFERER')
        return context
    
    def activity_notice(self):
        profile_link = reverse_lazy('profile', kwargs={'username':self.request.user.username})
        user = f"<a href={profile_link}>{self.request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': self.object.session.id})
        task = f"<a href={session_link}>{self.object.task}</a>"

        session = f"<a href={session_link}>{self.object.session.name}</a>"

        # actual content
        title = f"{user} deleted a task"
        content = f"<strong>{user}</strong> removed the task <em>{task}</em> from the <strong>{session}</strong> session."
        Notice.objects.create(room=self.object.session.room, title=title, content=content, is_html=True)

    
    def get_success_url(self):
        self.activity_notice()
        return self.request.POST.get('referer') or reverse_lazy('home')



def toggletask(request, task_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    task = get_object_or_404(Todo, id = task_id)

    def activity_notice(task):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': task.session.id})
        todo = f"<a href={session_link}>{task.task}</a>"

        session = f"<a href={session_link}>{task.session.name}</a>"

        # actual content
        title = f"{user} completed a task"
        content = f"<strong>{user}</strong> completed the task <em>{todo}</em> in the <strong>{session}</strong> session."
        Notice.objects.create(room=task.session.room, title=title, content=content, is_html=True)

    if task.user == request.user:
        task.completed = not task.completed
        task.save()
        if task.completed:
            activity_notice(task)
        
    
    return redirect(request.META.get('HTTP_REFERER') or reverse('home'))


class SessionCreate(LRM,NotDemoUserMixin,AdminPermRequired,CreateView):
    model = Session
    fields = ['name', 'description']
    template_name = 'session/createsession.html'

    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        form.instance.room = Room.objects.get(id=self.kwargs.get('room_id'))
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object:
            self.object.members.add(self.request.user)
        return response
    
    def activity_notice(self):
        profile_link = reverse_lazy('profile', kwargs={'username':self.request.user.username})
        user = f"<a href={profile_link}>{self.request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': self.object.id})

        session = f"<a href={session_link}>{self.object.name}</a>"

        # actual content
        title = f"{user} created a new session"
        content = f"<strong>{user}</strong> has created a new session: <em>{session}</em> 🎉"
        Notice.objects.create(room=self.object.room, title=title, content=content, is_html=True)

    def get_success_url(self):
        session_id = self.object.id
        self.activity_notice()
        return reverse_lazy('session', kwargs = {'session_id': session_id})
    

class SessionView(LRM,MemberRequiredMixin,DetailView):
    model = Session
    pk_url_kwarg = 'session_id'
    today = timezone.localdate()

    def dispatch(self, request, *args, **kwargs):
        if not self.get_object().is_active:
            return redirect('session-stats', self.kwargs.get('session_id'))
        return super().dispatch(request, *args, **kwargs)

    def get_template_names(self):
        return ['session/session_detail.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_tasks'] = Todo.objects.filter(session = self.object, user = self.request.user)
        context['other_members'] = self.object.members.exclude(id= self.request.user.id)
        context['today'] = self.today
        return context



    def post(self, *args, **kwargs):
        def time_to_hours(time_str):
            time_str = time_str.strip().lower()
            hours = 0
            minutes = 0

            # Split the string into parts like ['2h', '33m']
            parts = time_str.split()
            for part in parts:
                if 'h' in part:
                    hours += int(part.replace('h', ''))
                elif 'm' in part:
                    minutes += int(part.replace('m', ''))

            return round(hours + minutes / 60, 2)
        

        hours = self.request.POST.get('hours')
        hours = time_to_hours(hours)
        todo_id = self.request.POST.get('todo_id')
        if hours and todo_id:
            todo_inst = Todo.objects.filter(id=todo_id).first()
            if not todo_inst.completed:
                TrackTodo.objects.create(todo = todo_inst, day= self.today, hours = hours, hours_till_day= todo_inst.total_hours + hours )
                
                
            
        return HttpResponseRedirect(self.request.path) 
                

            


def joinsession(request, session_id):
    session_obj = Session.objects.get(id=session_id)
    room_members = session_obj.room.members.all()

    def activity_notice(session_obj):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})

        session = f"<a href={session_link}>{session_obj.name}</a>"

        # actual content
        title = f"{user} joined the session"
        content = f"<strong>{user}</strong> has joined the session <em>{session}</em>. Welcome!"
        Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)

    if request.user in room_members:
        session_obj.members.add(request.user)
        session_obj.save()
        activity_notice(session_obj)

    return redirect(reverse('session', kwargs={'session_id': session_obj.id}))
    
    

    
def start_session(request, session_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    session = Session.objects.get(id=session_id)

    def activity_notice(session_obj):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})

        session = f"<a href={session_link}>{session_obj.name}</a>"

        # actual content
        title = f"{user} started the session"
        content = f"<strong>{user}</strong> has started the session <em>{session}</em>. Let’s get going! 🚀"
        Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)

    if session.room.admin == request.user:
        session.start_date = timezone.now()
        print(session.start_date)
        session.save()
        activity_notice(session)

    return redirect(reverse('session', kwargs={'session_id': session.id}))

@not_demo_user
def end_session(request, session_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    def activity_notice(session_obj):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})

        session = f"<a href={session_link}>{session_obj.name}</a>"

        # actual content
        title = f"{user} ended the session"

        session_rankings = "<h4>📊 Session Rankings</h4><ul>"
        for item in session_obj.rankings.all():
            session_rankings += f"<li>{item.rank}. <strong>{item.user}</strong> — {item.total_hours} hours</li>"
        session_rankings += "</ul>"

        room_rankings = "<h4>🌐 Room Rankings</h4><ul>"
        for item in session_obj.room.rankings.all():
            room_rankings += f"<li>{item.rank}. <strong>{item.user}</strong> — {item.total_hours} hours</li>"
        room_rankings += "</ul>"

        content = f"""
        <strong>{user}</strong> has ended the session <em>{session}</em>. Congratulations to everyone!
        {session_rankings}
        {room_rankings}
        """

        Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)

    
    session = Session.objects.get(id=session_id)
    if session.start_date:
        if session.room.admin == request.user:
            session.finish_date = timezone.now().date()
            for task in session.todos.all():
                if not task.completed:
                    task.completed = True
                    task.completed_date = timezone.now().date()
                    task.save()
            session.save()
            session.room.updateRoomRankings()
            activity_notice(session)
    return redirect(reverse('room', kwargs={'room_id': session.room.id}))

@not_demo_user
def kick_from_room(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    def activity_notice(room_obj, user_id):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        room_link = reverse_lazy('room', kwargs={'room_id': room_obj.id})
        room = f"<a href={room_link}>{room_obj.name}</a>"

        kicked_user = get_object_or_404(CustomUser,id=user_id)
        # actual content
        title = f"{kicked_user} was removed from the room"
        content = f"<strong>{user}</strong>, the room admin, has removed <em>{kicked_user}</em> from the room."
        Notice.objects.create(room=room_obj, title=title,content=content, is_html=True)
    
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        room_id = data.get('room_id')
        user_id = data.get('user_id')
    else:
        room_id = request.POST.get('room_id')
        user_id = request.POST.get('user_id')
    
    room = get_object_or_404(Room,id=room_id)
    if room and request.user == room.admin:
        if room.admin.id != user_id:
            room.remove_member(user_id)
            activity_notice(room, user_id)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'You must first transfer the ownership'})
    else:
        return JsonResponse({'success': False, 'error': 'Permission denied'})


@not_demo_user
def kick_from_session(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    def activity_notice(session_obj, user_id):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})
        session = f"<a href={session_link}>{session_obj.name}</a>"

        kicked_user = get_object_or_404(CustomUser,id=user_id)
        # actual content
        title = f"{kicked_user} was removed from the {session} session"
        content = f"<strong>{user}</strong>, the room admin, has removed <em>{kicked_user}</em> from the <strong>{session}</strong> session."
        Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)

    
    if request.content_type == 'application/json':
        data = json.loads(request.body)
        session_id = data.get('session_id')
        user_id = data.get('user_id')
    else:
        session_id = request.POST.get('session_id')
        user_id = request.POST.get('user_id')

    session = get_object_or_404(Session, id=session_id)
    if session and session.room.admin == request.user:
        session.remove_member(user_id)
        activity_notice(session, user_id)
        return JsonResponse({'success': True})



@not_demo_user
def leave_session(request, session_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    def activity_notice(session_obj):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})
        session = f"<a href={session_link}>{session_obj.name}</a>"

        # actual content
        title = f"{user} has left the {session} session"
        content = f"<strong>{user}</strong> has left the <em>{session}</em> session."
        Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)

    if request.content_type == 'application/json':
        data = json.loads(request.body)
        session_id = data.get('session_id')
    else:
        session_id = request.POST.get('session_id')

    session = get_object_or_404(Session, id=session_id)
    if session and request.user in session.members.all:
        session.remove_member(request.user.id)
        activity_notice(session)
        return JsonResponse({'success': True})
    

@not_demo_user
def leave_room(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    def activity_notice(room_obj):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        # actual content
        title = f"{user} has left the room"
        content = f"<strong>{user}</strong> has left the room."
        Notice.objects.create(room=room_obj, title=title, content=content, is_html=True)

    
    room_id = request.POST.get('room_id')
    room = get_object_or_404(Room,id=room_id)
    if room:
        if room.admin != request.user:
            room.remove_member(request.user.id)
            activity_notice(room)
            return redirect('home')


@not_demo_user
def transfer_ownership(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    def activity_notice(room_obj, user_id):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        room_link = reverse_lazy('room', kwargs={'room_id': room_obj.id})
        room = f"<a href={room_link}>{room_obj.name}</a>"

        new_owner = get_object_or_404(CustomUser,id=user_id)
        # actual content
        title = "Owner Changed"
        content = f"<strong>{user}</strong>, the former room admin, has transferred ownership to <strong>{new_owner}</strong>."
        Notice.objects.create(room=room_obj, title=title, content=content, is_html=True)

    
    user_id = request.POST.get('new_admin')
    room_id = request.POST.get('room_id')
    new_admin = get_object_or_404(CustomUser,id=user_id)

    room = Room.objects.filter(id=room_id).first()
    if room and room.admin == request.user:
        room.transfer_admin(user_id)
        activity_notice(room, user_id)
        return redirect('room', room.id)
    
    


@not_demo_user
def delete_room(request):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])
    
    room_id = request.POST.get('room_id')
    room = get_object_or_404(Room,id=room_id)
    if room and room.admin == request.user:
        name = room.name
        room.delete()
        return redirect('home')




        