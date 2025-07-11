from django.views.generic import CreateView , DetailView , FormView
from .models import Todo, Room, Session
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin as LRM
from django.shortcuts import get_object_or_404 , redirect
from django.utils import timezone

class TodoCreateView(LRM,CreateView):
    template_name = 'addtodo.html'
    model = Todo
    success_url = reverse_lazy('home')
    fields = ['task', 'session', 'deadline']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        if form.fields.get('room'):
            form.fields['room'].queryset = Room.objects.filter(members = self.request.user)
        return form
    
class TodoCreateFromSession(TodoCreateView):
    fields = ['task', 'deadline']

    def form_valid(self, form):
        form.instance.session = Session.objects.get(id = self.kwargs.get('session_id'))
        return super().form_valid(form)
    
    def get_success_url(self):
        session_id = self.kwargs.get('session_id')
        return reverse_lazy('session', kwargs = {'session_id': session_id})
    

def toggletask(request, task_id):
    task = get_object_or_404(Todo, id = task_id)
    if task.user == request.user:
        task.completed = not task.completed
        task.save()
    
    return redirect(request.META.get('HTTP_REFERER', 'home'))

class SessionCreate(CreateView):
    model = Session
    fields = ['name', 'finish_date']
    template_name = 'createsession.html'

    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        form.instance.room = Room.objects.get(id=self.kwargs.get('room_id'))
        return form
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.object:
            self.object.members.add(self.request.user)
        return response
    
    def get_success_url(self):
        session_id = self.object.id
        return reverse_lazy('session', kwargs = {'session_id': session_id})
    

class SessionView(DetailView):
    model = Session
    pk_url_kwarg = 'session_id'
    context_object_name = 'session'

    def get_template_names(self):
        if not self.get_object().is_active:
            return ['oldsession.html']
        return ['session.html']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tasks'] = Todo.objects.filter(session=self.object)
        context['my_tasks'] = Todo.objects.filter(session = self.object, user = self.request.user)
        return context


def joinsession(request, session_id):
    session_obj = Session.objects.get(id=session_id)
    room_members = session_obj.room.members.all()
    if request.user in room_members:
        session_obj.members.add(request.user)
        session_obj.save()
    return redirect(reverse('session', kwargs={'session_id': session_obj.id}))
    
    

    
def start_session(request, session_id):
    session = Session.objects.get(id=session_id)
    if session.room.admin == request.user:
        session.start_date = timezone.now()
        print(session.start_date)
        session.save()

    return redirect(reverse('session', kwargs={'session_id': session.id}))

def end_session(request, session_id):
    session = Session.objects.get(id=session_id)
    if session.start_date:
        if session.room.admin == request.user:
            session.finish_date = timezone.now().date()
            session.save()
    return redirect(reverse('room', kwargs={'room_id': session.room.id}))


