from django.views.generic import CreateView
from .models import Todo
from django.urls import reverse_lazy
from .models import Room


class TodoCreateView(CreateView):
    template_name = 'addtodo.html'
    model = Todo
    success_url = reverse_lazy('home')
    fields = ['task', 'room', 'deadline']

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
    
    def get_form(self, form_class = None):
        form = super().get_form(form_class)
        if form.fields.get('room'):
            form.fields['room'].queryset = Room.objects.filter(members = self.request.user)
        return form
    
class TodoCreateFromRoomView(TodoCreateView):
    fields = ['task', 'deadline']

    def form_valid(self, form):
        form.instance.room = Room.objects.get(id = self.kwargs.get('room_id'))
        return super().form_valid(form)
    
    def get_success_url(self):
        room_id = self.kwargs.get('room_id')
        return reverse_lazy('room', kwargs = {'room_id': room_id})
    



    


