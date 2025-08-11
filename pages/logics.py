from django.urls import reverse_lazy
from stats.models import Notice
from .models import Session, CustomUser
from django.utils import timezone
from django.shortcuts import get_object_or_404 , redirect, HttpResponse, render
from .register_signals import *


def join_session_logic(request, session_id):
    session_obj = Session.objects.get(id=session_id)
    room_members = session_obj.room.members.all()

    def activity_notice(session_obj):
        profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
        user = f"<a href={profile_link}>{request.user}</a>"

        session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})

        session = f"<a href={session_link}>{session_obj.name}</a>"

        # actual content
        title = f"{user} joined the session"
        content = f"<strong>{user}</strong> has joined the session <em>{session}</em>. Welcome!"
        Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)

    if request.user in room_members:
        session_obj.members.add(request.user)
        session_obj.save()
        activity_notice(session_obj)


def start_session_logic(request, session_id):
    session = Session.objects.get(id=session_id)
    if session.room.admin == request.user:
        session.started_at = timezone.now()
        session.save()
        # fire signal
        session_started.send_robust(sender=Session, session_obj = session)



def end_session_logic(request, session_id):
    session = Session.objects.get(id=session_id)
    if session.started_at:
        if session.room.admin == request.user:
            session.finished_at = timezone.now()
            for task in session.todos.all():
                if not task.completed:
                    task.completed = True
                    task.completed_date = timezone.now()
                    task.save()
            session.save()
            session.room.updateRoomRankings()
            # fire signal
            session_ended.send_robust(sender=Session, session_obj = session)


def notice_kick_from_room_logic(request, room_obj, user_id):
    profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
    user = f"<a href={profile_link}>{request.user}</a>"

    room_link = reverse_lazy('room', kwargs={'room_id': room_obj.id})
    room = f"<a href={room_link}>{room_obj.name}</a>"

    kicked_user = get_object_or_404(CustomUser,id=user_id)
    # actual content
    title = f"{kicked_user} was removed from the room"
    content = f"<strong>{user}</strong>, the room admin, has removed <em>{kicked_user}</em> from the room."
    Notice.objects.create(room=room_obj, title=title,content=content, is_html=True)


def notice_kick_from_session_logic(request, session_obj, user_id):
    profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
    user = f"<a href={profile_link}>{request.user}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})
    session = f"<a href={session_link}>{session_obj.name}</a>"

    kicked_user = get_object_or_404(CustomUser,id=user_id)
    # actual content
    title = f"{kicked_user} was removed from the {session} session"
    content = f"<strong>{user}</strong>, the room admin, has removed <em>{kicked_user}</em> from the <strong>{session}</strong> session."
    Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)


def notice_leave_session_logic(request, session_obj):
    profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
    user = f"<a href={profile_link}>{request.user}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': session_obj.id})
    session = f"<a href={session_link}>{session_obj.name}</a>"

    # actual content
    title = f"{user} has left the {session} session"
    content = f"<strong>{user}</strong> has left the <em>{session}</em> session."
    Notice.objects.create(room=session_obj.room, title=title, content=content, is_html=True)


def notice_leave_room_logic(request, room_obj):
    profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
    user = f"<a href={profile_link}>{request.user}</a>"

    # actual content
    title = f"{user} has left the room"
    content = f"<strong>{user}</strong> has left the room."
    Notice.objects.create(room=room_obj, title=title, content=content, is_html=True)


def notice_transfer_ownership_logic(request, room_obj, user_id):
    profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
    user = f"<a href={profile_link}>{request.user}</a>"

    room_link = reverse_lazy('room', kwargs={'room_id': room_obj.id})
    room = f"<a href={room_link}>{room_obj.name}</a>"

    new_owner = get_object_or_404(CustomUser,id=user_id)
    # actual content
    title = "Owner Changed"
    content = f"<strong>{user}</strong>, the former room admin, has transferred ownership to <strong>{new_owner}</strong>."
    Notice.objects.create(room=room_obj, title=title, content=content, is_html=True)


def notice_toggle_task(request, task):
    profile_link = reverse_lazy('profile', kwargs={'username':request.user.username})
    user = f"<a href={profile_link}>{request.user}</a>"

    session_link = reverse_lazy('session', kwargs={'session_id': task.session.id})
    todo = f"<a href={session_link}>{task.task}</a>"

    session = f"<a href={session_link}>{task.session.name}</a>"

    # actual content
    title = f"{user} completed a task"
    content = f"<strong>{user}</strong> completed the task <em>{todo}</em> in the <strong>{session}</strong> session."
    Notice.objects.create(room=task.session.room, title=title, content=content, is_html=True)
