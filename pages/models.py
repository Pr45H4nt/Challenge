from django.db import models
from authapp.models import CustomUser
from django.contrib.auth.hashers import make_password , check_password
from django.core.exceptions import ValidationError
import uuid
from django.utils import timezone
from datetime import datetime

# Create your models here.

class Room(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
    
class Session(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='sessions')
    name = models.CharField(max_length=250)
    start_date = models.DateTimeField(null=True,blank=True)
    finish_date = models.DateField(null=True, blank=True)
    members = models.ManyToManyField(CustomUser, related_name='sessions', null=True)
    
    def clean(self):
        if Session.objects.filter(name=self.name, room = self.room).exclude(id=self.id).exists():
            raise ValidationError({"name": "The name should be unique in a room!"})
        if self.finish_date and self.finish_date < timezone.now().date():
            raise ValidationError({'finish_date': "Finish date can't be in the past!"})
        
        objects = Session.objects.filter(room=self.room).exclude(id=self.id)
        for object in objects:
            if object.is_active:
                raise ValidationError(
                    "There is already an active session in this room. "
                    "Please end the current active session before creating a new one."
                )
        return super().clean()
    
    def save(self,*args, **kwargs):
        self.clean()
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return str(self.name)+ ' in ' + str(self.room)
    
    @property
    def is_active(self):
        if not self.finish_date:
            return True
        return self.finish_date > timezone.now().date()


class Todo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='todos')
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='todos')
    task = models.TextField()
    completed = models.BooleanField(default=False)
    completed_on = models.DateField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.task[:10]}...by {self.user}"
    
    def clean(self):
        if self.deadline < timezone.now().date():
            raise ValidationError({"deadline": "The deadline cannot be in the past."})
        return super().clean()
    
    @property
    def is_due(self):
        return not self.completed and self.deadline < timezone.now().date()


class SessionRanking(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='rankings')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='rankings')
    rank = models.PositiveIntegerField()
    completion_time = models.DurationField(help_text="Time taken to complete all todos")
    completed_todos_count = models.PositiveIntegerField(default=0)
    total_todos_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ('session', 'user')
        ordering = ['session', '-rank']
    
    def __str__(self):
        return f"{self.user.username} - Rank {self.rank} in {self.session.name}"

