from django.urls import path
from .views import *
from .views2 import *

urlpatterns = [
    path("", Homeview.as_view(), name="home"),
    path("createroom/", RoomCreateView.as_view(), name="createroom"),
    path("joinroom/", RoomJoinView.as_view(), name="joinroom"),
    path("room/<str:room_id>/", RoomView.as_view(), name="room"),
    path('room/<str:room_id>/createsession/', SessionCreate.as_view(), name='createsession'),
    path('createtodo/', TodoCreateView.as_view(), name='createtodo'),
    path('toggle/<str:task_id>/', toggletask, name='toggletask'),
    path('session/<str:session_id>/', SessionView.as_view(), name='session'),
    path('joinsession/<str:session_id>/', joinsession, name='joinsession'),
    path('session/<str:session_id>/createtask', TodoCreateFromSession.as_view(), name='createtask'),
    path('startsession/<str:session_id>/', start_session, name='startsession'),
    path('endsession/<str:session_id>/', end_session, name='endsession'),


]
