from django.shortcuts import render 
from django.views.generic import TemplateView , CreateView, FormView, DetailView, ListView, UpdateView
from . models import Room, Session, CustomUser
from django.urls import reverse_lazy
from .forms import RoomJoinForm, ChangeRoomPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import date
from .mixins import MemberRequiredMixin, AdminPermRequired, NotDemoUserMixin
from stats.models import Notice
from django.views import View
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect


class Homeview(TemplateView):
    template_name = "home.html"


class RoomCreateView(LoginRequiredMixin,CreateView):
    model = Room
    template_name = 'room/roomcreate.html'
    fields = ['name','bio','password']

    def form_valid(self, form):
        form.instance.admin = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('room', kwargs={'room_id': self.object.id})
    


class RoomJoinView(LoginRequiredMixin, NotDemoUserMixin,FormView):
    template_name = 'room/joinroom.html'
    form_class = RoomJoinForm

    def form_valid(self, form):
        room = form.cleaned_data['room']
        self.room = room
        room.join_room(self.request.user)
        return super().form_valid(form)
    
    def get_success_url(self):
        room = self.room
        return reverse_lazy('room', kwargs = {'room_id': room.id})
    

    

class RoomView(LoginRequiredMixin,MemberRequiredMixin,DetailView):
    template_name = 'room/room.html'
    context_object_name = 'room'
    model = Room
    pk_url_kwarg = 'room_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_id = self.kwargs.get('room_id')
        context['active_sessions'] = Session.objects.filter(room_id=room_id, finished_at__isnull= True)
        context['old_sessions'] = Session.objects.filter(room_id=room_id, finished_at__lte=date.today())

        return context
    
class RoomSettingsView(LoginRequiredMixin,MemberRequiredMixin,DetailView):
    template_name = 'room/room_settings.html'
    context_object_name = 'room'
    model = Room
    pk_url_kwarg = 'room_id'



class RoomUpdateView(LoginRequiredMixin,NotDemoUserMixin, AdminPermRequired,UpdateView ):
    model = Room
    fields = ['name', 'bio']
    pk_url_kwarg = 'room_id'
    context_object_name = 'room'
    template_name = 'room/update_room_info.html'
    # template_name = 'room_update.html'
    
    def get_success_url(self):
        return reverse_lazy('room-settings', kwargs={'room_id':self.object.id})
    
class ChangeRoomPasswordView(LoginRequiredMixin,NotDemoUserMixin, AdminPermRequired,View):
    template_name = 'room/change_room_pass.html'

    def get(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        form = ChangeRoomPasswordForm()
        return render(request, self.template_name, {'form': form, 'room': room})

    def post(self, request, room_id):
        room = get_object_or_404(Room, id=room_id)
        form = ChangeRoomPasswordForm(request.POST)

        if form.is_valid():
            current = form.cleaned_data.get('current_password')
            new_pass = form.cleaned_data.get('new_password')


            if not room.check_pass(current):
                form.add_error('current_password', 'Current password is incorrect.')
                # return redirect('change-room-pass', room_id=room.id)
            else:
            # Save new password
                room.password = new_pass
                room.hash_pass()
                room.save()
                messages.success(request, "Password updated successfully.")
                return redirect('room', room_id=room.id)

        return render(request, self.template_name, {'form': form, 'room': room})



class SessionSettingsView(LoginRequiredMixin,MemberRequiredMixin,DetailView):
    template_name = 'session/session_settings.html'
    context_object_name = 'session'
    model = Session
    pk_url_kwarg = 'session_id'



class SessionUpdateView(LoginRequiredMixin,NotDemoUserMixin, AdminPermRequired,UpdateView ):
    model = Session
    fields = ['name', 'description']
    pk_url_kwarg = 'session_id'
    context_object_name = 'session'
    template_name = 'session/update_session_info.html'
    
    def get_success_url(self):
        return reverse_lazy('session-settings', kwargs={'session_id':self.object.id})
    


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sessions = Session.objects.filter(members = self.request.user).all()
        active_sessions = []
        past_sessions = []

        for i in sessions:
            if i.is_active:
                active_sessions.append(i)
            else:
                past_sessions.append(i)
        
        context['sessions'] = sessions
        context['active_sessions'] = active_sessions
        context['past_sessions'] = past_sessions
        return context
