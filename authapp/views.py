from django.shortcuts import render , redirect
from django.views.generic import CreateView, FormView , UpdateView , DetailView, TemplateView, View
from django.contrib.auth.views import LoginView
from django.contrib.auth import logout , login , update_session_auth_hash
from .models import CustomUser, Profile
from .forms import CustomUserCreationForm
from django.urls import reverse_lazy , reverse
from .forms import PassChangeForm
from pages.models import Todo, TrackTodo
from pages.mixins import NotDemoUserMixin
from pages.decorators import not_demo_user
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin as LRM
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
import json

# Create your views here.

class SignupView(FormView):
    template_name = 'signup.html'
    model = CustomUser
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('editprofile')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class Login(LoginView):
    template_name = 'login.html'

    def get_success_url(self):
        if Profile.objects.filter(user = self.request.user).exists():
            return reverse_lazy('home')
        return reverse_lazy('editprofile')

def logoutview(request):
    logout(request)
    home_url = reverse('home')

    return redirect(home_url)

@not_demo_user
@login_required
def passwordchangeview(request):
    context = {}
    if request.method == "POST":
        form = PassChangeForm(request.POST)
        if form.is_valid():
            old_pass = request.POST.get('old_password')
            pass1 = request.POST.get('new_password')
            pass2 = request.POST.get('confirm_password')
            if pass1 != pass2:
                context['error'] = "The new passwords don't match."
            elif not request.user.check_password(old_pass):
                context['error'] = "The entered password isn't correct"
            else:
                request.user.set_password(pass1)
                request.user.save()
                update_session_auth_hash(request, request.user)
                return redirect(reverse('home'))
    else:
        form = PassChangeForm()
    context['form'] = form
    return render(request, 'changepass.html', context)


class ProfileCreateView(LRM,CreateView):
    template_name = 'editprofile.html'
    model = Profile
    fields = ['bio']
    success_url = reverse_lazy('home')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

class ProfileUpdateView(NotDemoUserMixin,LRM,UpdateView):
    template_name = 'editprofile.html'
    model = Profile
    fields = ('bio',)
    success_url = reverse_lazy('home')

    def get_object(self, queryset = ...):
        return self.request.user.profile
    

@login_required
def profileview(request):
    if Profile.objects.filter(user= request.user).exists():
        view = ProfileUpdateView.as_view()
    else:
        view = ProfileCreateView.as_view()
    return view(request)


class DisplayProfileView(LRM,DetailView):
    template_name = 'profile.html'
    context_object_name = 'profile'

    def get_object(self, queryset = ...):
        profile = Profile.objects.filter(user__username = self.kwargs['username']).first()
        if not profile:
            user = get_object_or_404(CustomUser, username=self.kwargs['username'])
            profile = Profile.objects.create(user = user)
        return profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        incompleted = {}
        incompleted_todos = Todo.objects.filter(user = self.request.user).filter(completed= False)
        for i in incompleted_todos:
            incompleted[i.session.room] = incompleted.get(i.session.room, 0) + 1
        
        context['incompleted_todosroom'] = incompleted
        return context


class SettingsView(LRM, TemplateView):
    template_name = "settings.html"

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    

class DownloadUserData(LRM, View):
    def get(self, request):
        grouped_by = request.GET.get('group_by')
        
        if grouped_by != 'task':
            print('Not Grouped by task')
            records = TrackTodo.objects.filter(todo__user=request.user).select_related('todo')
            data = [
                {
                    'task': obj.todo.task,
                    'hours_added': obj.hours,
                    'added_on': obj.day.isoformat() if obj.day else None,
                    'task_created_on': obj.todo.created_on.isoformat() if obj.todo.created_on else None,
                    'task_completed_on': obj.todo.completed_on.isoformat() if obj.todo.completed_on else None
                }
                for obj in records
            ]
        
        else:
            print('Grouped by task')
            # Grouped by task
            todos = Todo.objects.filter(user=request.user).prefetch_related('tracking')
            data = []
            for todo in todos:
                trackings = [
                    {
                        'added_on': obj.day.isoformat() if obj.day else None,
                        'hours_added': obj.hours,
                    }
                    for obj in todo.tracking.all()
                ]
                data.append({
                    'task': todo.task,
                    'trackings': trackings
                })
        
        # wrap in user info
        output = {
            'user': request.user.username,
            'data': data
        }

        output_json = json.dumps(output, indent=4)
        response = HttpResponse(output_json, content_type='application/json; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="{request.user.username}_data.json"'
        return response


def demoaccountlogin(request):
    user = CustomUser.objects.get(username='demouser')
    login(request, user)
    return redirect('home')