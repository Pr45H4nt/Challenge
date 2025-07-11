from django.shortcuts import render 
from django.views.generic import TemplateView , CreateView, FormView, DetailView
from . models import Room, Session
from django.urls import reverse_lazy
from .forms import RoomJoinForm
from django.contrib.auth.mixins import LoginRequiredMixin
from datetime import date



# Create your views here.

class Homeview(TemplateView):
    template_name = "home.html"


class RoomCreateView(LoginRequiredMixin,CreateView):
    model = Room
    template_name = 'roomcreate.html'
    fields = ['name','bio','password']

    def form_valid(self, form):
        form.instance.admin = self.request.user
        response = super().form_valid(form)
        self.object.members.add(self.request.user)
        return response
    
    def get_success_url(self):
        return reverse_lazy('room', kwargs={'room_id': self.object.id})
    


class RoomJoinView(LoginRequiredMixin,FormView):
    template_name = 'joinroom.html'
    form_class = RoomJoinForm

    def form_valid(self, form):
        room = form.cleaned_data['room']
        self.room = room
        room.members.add(self.request.user)
        room.save()
        return super().form_valid(form)
    
    def get_success_url(self):
        room = self.room
        # print(room)
        return reverse_lazy('room', kwargs = {'room_id': room.id})
    

    

class RoomView(LoginRequiredMixin,DetailView):
    template_name = 'room.html'
    context_object_name = 'room'
    model = Room
    pk_url_kwarg = 'room_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        room_id = self.kwargs.get('room_id')

        context['active_sessions'] = Session.objects.filter(room_id=room_id, finish_date__gt=date.today())
        context['old_sessions'] = Session.objects.filter(room_id=room_id, finish_date__lte=date.today())

        return context
    



    
