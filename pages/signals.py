from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse_lazy
from stats.models import Notice
from .models import Session, Room, TrackTodo, CustomUser
from .register_signals import *
from django.shortcuts import get_object_or_404


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

@receiver(signal=room_joined)
def joined_room_notice(sender, user, room, **kwargs):
    profile_link = reverse_lazy('profile', kwargs={'username':user.username})
    user = f"<a href={profile_link}>{user}</a>"

    room_link = reverse_lazy('room', kwargs={'room_id': room.id})

    room_html = f"<a href={room_link}>{room.name}</a>"

    # actual content
    title = f"{user} has joined the room"
    content = f"<strong>{user}</strong> just joined <em>{room_html}</em>. Welcome aboard!"
    Notice.objects.create(room=room, title=title, content=content, is_html=True)


@receiver(signal=session_joined)
def joined_session_notice(sender, user, session, **kwargs):
    profile_link = reverse_lazy('profile', kwargs={'username':user.username})
    user = f"<a href={profile_link}>{user}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': session.id})

    session_html = f"<a href={session_link}>{session.name}</a>"

    # actual content
    title = f"{user} joined the session"
    content = f"<strong>{user}</strong> has just joined the session <em>{session_html}</em>. Welcome!"
    Notice.objects.create(room=session.room, title=title, content=content, is_html=True)


@receiver(signal=session_started)
def started_session(sender, session_obj, **kwargs):
    admin =  session_obj.room.admin
    profile_link = reverse_lazy('profile', kwargs={'username':admin.username})
    user = f"<a href={profile_link}>{admin}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})

    session = f"<a href={session_link}>{session_obj.name}</a>"

    # actual content
    title = f"{user} started the session"
    content = f"<strong>{user}</strong> has started the session <em>{session}</em>. Let’s get going! 🚀"
    Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)


@receiver(signal=session_ended)
def ended_session(sender, session_obj, **kwargs):
    admin = session_obj.room.admin

    profile_link = reverse_lazy('profile', kwargs={'username':admin.username})
    user = f"<a href={profile_link}>{admin}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})

    session = f"<a href={session_link}>{session_obj.name}</a>"

    # actual content
    title = f"{user} ended the session"

    session_rankings = "<h4>📊 Session Rankings</h4><ul>"
    for item in session_obj.rankings.all():
        session_rankings += f"<li>{item.rank}. <strong>{item.user}</strong> — {item.total_hours} hours</li>"
    session_rankings += "</ul>"

    room_rankings = "<h4>🌐 Room Rankings</h4><ul>"
    for item in session_obj.room.rankings.all():
        room_rankings += f"<li>{item.rank}. <strong>{item.user}</strong> — {item.total_hours} hours</li>"
    room_rankings += "</ul>"

    content = f"""
    <strong>{user}</strong> has ended the session <em>{session}</em>. Congratulations to everyone!
    {session_rankings}
    {room_rankings}
    """

    Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)


@receiver(signal= session_created)
def session_created(sender, session_obj, **kwargs):
    admin = session_obj.room.admin

    profile_link = reverse_lazy('profile', kwargs={'username':admin.username})
    user = f"<a href={profile_link}>{admin}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})

    session = f"<a href={session_link}>{session_obj.name}</a>"

    # actual content
    title = f"{user} created a new session"
    content = f"<strong>{user}</strong> has created a new session: <em>{session}</em> 🎉"
    Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)

@receiver(signal=kicked_from_room)
def kicked_from_room(sender, room_obj, user_id, **kwargs):
    admin = room_obj.admin
    profile_link = reverse_lazy('profile', kwargs={'username':admin.username})
    user = f"<a href={profile_link}>{admin}</a>"

    room_link = reverse_lazy('room', kwargs={'room_id': room_obj.id})
    room = f"<a href={room_link}>{room_obj.name}</a>"

    kicked_user = get_object_or_404(CustomUser,id=user_id)
    # actual content
    title = f"{kicked_user} was removed from the room"
    content = f"<strong>{user}</strong>, the room admin, has removed <em>{kicked_user}</em> from the room."
    Notice.objects.create(room=room_obj, title=title,content=content, is_html=True)



@receiver(signal=kicked_from_session)
def kicked_from_session(sender, session_obj, user_id, **kwargs):
    admin = session_obj.room.admin

    profile_link = reverse_lazy('profile', kwargs={'username':admin.username})
    user = f"<a href={profile_link}>{admin}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})
    session = f"<a href={session_link}>{session_obj.name}</a>"

    kicked_user = get_object_or_404(CustomUser,id=user_id)
    # actual content
    title = f"{kicked_user} was removed from the {session} session"
    content = f"<strong>{user}</strong>, the room admin, has removed <em>{kicked_user}</em> from the <strong>{session}</strong> session."
    Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)

@receiver(signal=left_session)
def left_session(sender, session_obj, user, **kwargs):
    profile_link = reverse_lazy('profile', kwargs={'username':user.username})
    user = f"<a href={profile_link}>{user}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})
    session = f"<a href={session_link}>{session_obj.name}</a>"

    # actual content
    title = f"{user} has left the {session} session"
    content = f"<strong>{user}</strong> has left the <em>{session}</em> session."
    Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)


@receiver(signal=left_room)
def left_room(sender, room_obj, user, **kwargs):
    profile_link = reverse_lazy('profile', kwargs={'username':user.username})
    user = f"<a href={profile_link}>{user}</a>"

    # actual content
    title = f"{user} has left the room"
    content = f"<strong>{user}</strong> has left the room."
    Notice.objects.create(room=room_obj, title=title, content=content, is_html=True)


@receiver(signal=owner_transferred)
def owner_transferred(sender, room_obj, user_id, **kwargs):
    admin = room_obj.admin
    profile_link = reverse_lazy('profile', kwargs={'username':admin.username})
    user = f"<a href={profile_link}>{admin}</a>"

    room_link = reverse_lazy('room', kwargs={'room_id': room_obj.id})
    room = f"<a href={room_link}>{room_obj.name}</a>"

    new_owner = get_object_or_404(CustomUser,id=user_id)
    # actual content
    title = "Owner Changed"
    content = f"<strong>{user}</strong>, the former room admin, has transferred ownership to <strong>{new_owner}</strong>."
    Notice.objects.create(room=room_obj, title=title, content=content, is_html=True)


@receiver(signal=task_completed)
def task_completed(sender, task_obj, **kwargs):
    user = task_obj.session.room.admin
    profile_link = reverse_lazy('profile', kwargs={'username':user.username})
    user = f"<a href={profile_link}>{user}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': task_obj.session.id})
    todo = f"<a href={session_link}>{task_obj.task}</a>"

    session = f"<a href={session_link}>{task_obj.session.name}</a>"

    # actual content
    title = f"{user} completed a task"
    content = f"<strong>{user}</strong> completed the task <em>{todo}</em> in the <strong>{session}</strong> session."
    Notice.objects.create(room=task_obj.session.room, title=title, content=content, is_html=True)

@receiver(signal=task_created)
def task_created(sender, task_obj, **kwargs):
    user = task_obj.user

    profile_link = reverse_lazy('profile', kwargs={'username':user.username})
    user = f"<a href={profile_link}>{user}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': task_obj.session.id})
    task = f"<a href={session_link}>{task_obj.task}</a>"

    session = f"<a href={session_link}>{task_obj.session.name}</a>"

    # actual content
    title = f"{user} created a new task"
    content = f"<strong>{user}</strong> added the task <em>{task}</em> to the <strong>{session}</strong> session."
    Notice.objects.create(room=task_obj.session.room, title=title, content=content, is_html=True)
