from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Session, Room, TrackTodo

@receiver(signal=post_save, sender=Room)
def auto_add_admin_as_member_in_room(sender, instance, created, **kwargs):
    if created and instance.admin:
        instance.members.add(instance.admin)

@receiver(signal=post_save, sender= Session)
def auto_add_admin_as_member_in_session(sender, instance, created, **kwargs):
    if created and instance.room.admin:
        instance.members.add(instance.room.admin)


@receiver(signal=post_save, sender = TrackTodo )
def update_session_rankings(sender, instance, created, **kwargs):
    if created:
        instance.todo.session.updateSessionRanking()