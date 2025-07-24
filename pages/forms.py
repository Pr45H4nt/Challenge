from django import forms
from .models import Room
from django.contrib.auth.hashers import make_password 

class RoomJoinForm(forms.Form):
    name = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100, widget=forms.PasswordInput, required=False)
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data['password']
        room = Room.objects.filter(name=cleaned_data['name']).first()
        if not room:
            raise forms.ValidationError(f"Room does not exist by the name {cleaned_data['name']}")
        
        print('This is the pass: ', password)
        if room.check_pass(password):
            cleaned_data['room'] = room
            return cleaned_data
        raise forms.ValidationError("Wrong Password. Check again")

    
class ChangeRoomPasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, required=False)
    new_password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned_data = super().clean()
        new = cleaned_data.get("new_password")
        confirm = cleaned_data.get("confirm_password")

        if new != confirm:
            self.add_error('confirm_password', 'Passwords do not match.')
