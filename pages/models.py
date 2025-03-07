from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Room(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(User, related_name='members_rooms')
    created_on = models.DateTimeField(auto_now_add=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_rooms')


class Todo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='todos')
    action = models.TextField()
    deadline = models.DateField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action[:10]}...by {self.user}"

