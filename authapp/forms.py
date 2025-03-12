from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
from django import forms


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = UserCreationForm.Meta.fields + ('age',)

class PassChangeForm(forms.Form):
    old_password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    pass1 = forms.CharField(widget=forms.PasswordInput, min_length=8)
    pass2 = forms.CharField(widget=forms.PasswordInput, min_length=8)