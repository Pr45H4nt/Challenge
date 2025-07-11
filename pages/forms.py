from django import forms
from .models import Room

class RoomJoinForm(forms.Form):
    name = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100, widget=forms.PasswordInput, required=False)
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data['password']
        room = Room.objects.filter(name=cleaned_data['name']).first()
        if not room:
            raise forms.ValidationError(f"Room does not exist by the name {cleaned_data['name']}")
        
        if room.check_pass(password):
            cleaned_data['room'] = room
            return cleaned_data
        raise forms.ValidationError("Wrong Password. Check again")

    