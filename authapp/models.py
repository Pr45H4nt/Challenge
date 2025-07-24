from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class CustomUser(AbstractUser):
    age = models.PositiveIntegerField(null=True, blank=True)
    last_online = models.DateTimeField(null=True, blank=True)  # Store last online time
    def __str__(self):
        return  str(self.username)
    
    @property
    def total_hours(self):
        tasks = self.todos.all()
        hour = 0
        for task in tasks:
            hour += task.total_hours
        return hour




class Profile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    bio = models.CharField(max_length=300, blank=True)

    def __str__(self):
        return str(self.bio)
    