from django.db import models
from authapp.models import CustomUser

# Create your models here.

class Room(models.Model):
    name = models.CharField(max_length=100)
    members = models.ManyToManyField(CustomUser, related_name='members_rooms')
    created_on = models.DateTimeField(auto_now_add=True)
    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='admin_rooms')

    def __str__(self):
        return f"{self.name}"

class Todo(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='todos')
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='todos')
    action = models.TextField()
    deadline = models.DateField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action[:10]}...by {self.user}"

