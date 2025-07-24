from django.db import models
from authapp.models import CustomUser
from django.contrib.auth.hashers import make_password , check_password, is_password_usable, identify_hasher
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

    def is_hashed(self,password):
        try:
            identify_hasher(password)
            return True
        except ValueError:
            return False

    def hash_pass(self):
        if self.password:
            hashed_pass = make_password(self.password)
            self.password = hashed_pass

    def save(self, *args, **kwargs):
        if self.password and not self.is_hashed(self.password):
            self.hash_pass()
        super().save(*args, **kwargs)
    
    def check_pass(self, given_pass):
        print(self.password)
        if self.password:
            return check_password(given_pass, self.password )
        return True


        



    
    @property
    def total_hours(self):
        hashmap = {}
        
        for session in self.sessions.all():
            if not session.is_active:
                for user, hours in session.total_hours.items():
                    hashmap[user] = hashmap.get(user, 0) + hours
        return hashmap

    @property
    def current_rankings(self):
        hashmap = self.total_hours

        sorted_items = sorted(hashmap.items(), key=lambda item: item[1], reverse=True)
        return sorted_items
    
    def updateRoomRankings(self):
        ranks = self.current_rankings
        if ranks:
            start = 1
            for rank in ranks:
                RoomRanking.objects.update_or_create(room=self, user=rank[0],
                                                        defaults={
                                                         "rank":start, "total_hours" : rank[1]}
                                                         )
                start += 1
    
    def transfer_admin(self, user_id):
        user = CustomUser.objects.filter(id = user_id).first()
        if user and user in self.members.all():
            self.admin = user
            self.save()

    def remove_member(self, user_id):
        sessions = self.sessions.all()
        for session in sessions:
            session.remove_member(user_id)
        self.members.remove(user_id)
        self.save()


    def __str__(self):
        return f"{self.name}"
    
    
class Session(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='sessions')
    name = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    start_date = models.DateTimeField(null=True,blank=True)
    finish_date = models.DateField(null=True, blank=True)
    members = models.ManyToManyField(CustomUser, related_name='sessions', blank=True)
    
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
        self.room.updateRoomRankings()
        return super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.room.updateRoomRankings()

    
    def __str__(self):
        return str(self.name)+ ' in ' + str(self.room)
    
    @property
    def is_active(self):
        if not self.finish_date:
            return True
        return self.finish_date > timezone.now().date()
    
    @property
    def total_hours(self):
        hashmap = {}
        for member in self.members.all():
            todos = self.todos.filter(user=member)
            hours = sum([i.total_hours for i in todos])
            hashmap[member] = hours

        return hashmap
    
    @property
    def current_rankings(self):
        hashmap = self.total_hours

        sorted_items = sorted(hashmap.items(), key=lambda item: item[1], reverse=True)
        return sorted_items

    def updateSessionRanking(self):
        ranks = self.current_rankings
        if ranks:
            start = 1
            for rank in ranks:
                SessionRanking.objects.update_or_create(session=self, user=rank[0],
                                                        defaults={
                                                         "rank":start, "total_hours" : rank[1]}
                                                         )
                start += 1

    def remove_member(self, user_id):
        todos = self.todos.filter(user__id= user_id).delete()
        self.members.remove(user_id)
        self.save()
    
    


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
    
    @property
    def is_due(self):
        return not self.completed and self.deadline < timezone.now().date()
    
    @property
    def total_hours(self):
        tracks = self.tracking.all()
        hours = sum([i.hours for i in tracks])
        return hours
    
    @property
    def filledtoday(self):
        today = timezone.localdate()
        inst =self.tracking.filter(day=today)
        if inst:
            hour = 0
            for item in inst:
                hour += item.hours
            return hour
        return False
    
    
    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.session.updateSessionRanking()
        


class TrackTodo(models.Model):
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE, related_name='tracking')
    day = models.DateField(null=True, blank=True)
    hours = models.FloatField(default=0.0)
    hours_till_day = models.FloatField(default=0.0)


    
    def save(self, *args, **kwargs):
        returned_value = super().save(*args, **kwargs)
        self.todo.session.updateSessionRanking()
        return returned_value



class SessionRanking(models.Model):
    session = models.ForeignKey(Session, on_delete=models.CASCADE, related_name='rankings')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='session_rankings')
    rank = models.PositiveIntegerField()
    total_hours = models.FloatField(default=0.0)
    
    class Meta:
        unique_together = ('session', 'user')
        ordering = ['rank']
    
    def __str__(self):
        return f"{self.user.username} - Rank {self.rank} in {self.session.name}"


class RoomRanking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='rankings')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='room_rankings')
    rank = models.PositiveIntegerField()
    total_hours = models.FloatField(default=0.0)

    

    class Meta:
        unique_together = ('room', 'user')
        ordering = ['rank']



