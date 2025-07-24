from django.urls import path
from .views import *
from .views2 import *

urlpatterns = [
    path("", Homeview.as_view(), name="home"),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("createroom/", RoomCreateView.as_view(), name="createroom"),
    path("joinroom/", RoomJoinView.as_view(), name="joinroom"),
    path("room/<str:room_id>/", RoomView.as_view(), name="room"),
    path("room/<str:room_id>/settings", RoomSettingsView.as_view(), name="room-settings"),
    path("room/<str:room_id>/edit", RoomUpdateView.as_view(), name="update-room-info"),
    path("room/<str:room_id>/changepass", ChangeRoomPasswordView.as_view(), name="change-room-pass"),
    path('kick-user/', kick_from_room, name='kick-user'),
    path('transfer-ownership/', transfer_ownership, name='transfer-ownership'),
    path('delete-room/', delete_room, name='delete-room'),
    path('leave-room/', leave_room, name='leave-room'),


    path('room/<str:room_id>/createsession/', SessionCreate.as_view(), name='createsession'),
    # path('createtodo/', TodoCreateView.as_view(), name='createtodo'),
    path('toggle/<str:task_id>/', toggletask, name='toggletask'),
    path('delete/<str:task_id>/', RemoveTodoView.as_view(), name= 'deletetask'),
    path('session/<str:session_id>/', SessionView.as_view(), name='session'),
    path("session/<str:session_id>/settings", SessionSettingsView.as_view(), name="session-settings"),
    path("session/<str:session_id>/edit", SessionUpdateView.as_view(), name="update-session-info"),
    path('joinsession/<str:session_id>/', joinsession, name='joinsession'),
    path('session/<str:session_id>/createtask', TodoCreateFromSession.as_view(), name='createtask'),
    path('startsession/<str:session_id>/', start_session, name='startsession'),
    path('endsession/<str:session_id>/', end_session, name='endsession'),
    path('kick-user-session/', kick_from_session, name='kick-user-from-session'),
    path('leave-session/', leave_session, name='leave-session'),





]
