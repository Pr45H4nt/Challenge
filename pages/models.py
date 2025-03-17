from django.db import models
from authapp.models import CustomUser
from django.contrib.auth.hashers import make_password , check_password
from datetime import date
from django.core.exceptions import ValidationError

# Create your models here.

class Room(models.Model):
    name = models.CharField(max_length=100, unique=True)
    bio = models.TextField(blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null= True)
    members = models.ManyToManyField(CustomUser, related_name='members_rooms')
    created_on = models.DateTimeField(auto_now_add=True)
    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='admin_rooms')

    def hash_pass(self):
        if self.password:
            hashed_pass = make_password(self.password)
            self.password = hashed_pass

    def save(self):
        self.hash_pass()
        return super().save()
    
    def check_pass(self, given_pass):
        if self.password:
            return check_password(self.password, given_pass)
        return True

    def __str__(self):
        return f"{self.name}"

class Todo(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='todos')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='todos')
    task = models.TextField()
    completed = models.BooleanField(default=False)
    deadline = models.DateField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task[:10]}...by {self.user}"
    
    def clean(self):
        if self.deadline < date.today():
            raise ValidationError({"deadline": "The deadline cannot be in the past."})
        return super().clean()
    
    @property
    def is_due(self):
        return not self.completed and self.deadline < date.today()

