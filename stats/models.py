from django.db import models
from pages.models import Room, CustomUser, RoomMembership
import uuid
from django.utils import timezone
from django.core.exceptions import PermissionDenied

# Create your models here.
class Notice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='notices')
    author = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, related_name='notices')
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    created_on = models.DateTimeField(auto_now_add=True)
    is_html = models.BooleanField(default=False)


    class Meta:
        ordering = ['-is_pinned', '-created_on']

    def clean(self):
        room = getattr(self, 'room', None)
        author = getattr(self, 'author', None)
        is_admin = getattr(self, 'is_admin', None)
        
        if room and author:
            if author not in room.members.all():
                raise PermissionDenied("The author is not from the room")
            if is_admin and author != room.admin:
                raise PermissionDenied("Non admin cannot post as admin")
            
        return super().clean()

    def save(self, *args, **kwargs):
        self.clean()
        return super().save( *args, **kwargs)

    @property
    def is_posted_today(self):
        today = timezone.localdate()
        return today == self.created_on.date()
    
    def is_read(self, user):
        if self.author == user:
            return True
        read_flag = NoticeReadStatus.objects.filter(notice=self, user=user).exists()
        if read_flag:
            return True

        # check if user joined the room before the notice was created
        joined_before_notification = RoomMembership.objects.filter(
            room=self.room,
            user=user,
            joined_on__lt=self.created_on
        ).exists()

        # if user joined before the notice, but hasn't read it => unread (False)
        # if user joined after notice was created => consider it read (True)
        return not joined_before_notification

    def mark_as_read(self, user):
        NoticeReadStatus.objects.get_or_create(notice=self, user=user)

    def __str__(self):
        return f"📌 {self.title} - {self.room.name}"
    

class NoticeReadStatus(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name='read_statuses')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notice_reads')
    read_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('notice', 'user')
