from django.shortcuts import render 
from django.views.generic import TemplateView , CreateView, FormView, DetailView
from . models import Room
from django.urls import reverse_lazy
from .forms import RoomJoinForm


# Create your views here.

class Homeview(TemplateView):
    template_name = "home.html"


class RoomCreateView(CreateView):
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
    


class RoomJoinView(FormView):
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
        print(room)
        return reverse_lazy('room', kwargs = {'room_id': room.id})
    

    

class RoomView(DetailView):
    template_name = 'room.html'
    context_object_name = 'room'
    model = Room
    pk_url_kwarg = 'room_id'

    
