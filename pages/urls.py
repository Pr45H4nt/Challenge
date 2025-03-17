from django.urls import path
from .views import *
from .views2 import *

urlpatterns = [
    path("", Homeview.as_view(), name="home"),
    path("createroom/", RoomCreateView.as_view(), name="createroom"),
    path("joinroom/", RoomJoinView.as_view(), name="joinroom"),
    path("room/<int:room_id>/", RoomView.as_view(), name="room"),
    path('room/<int:room_id>/createtodo/', TodoCreateFromRoomView.as_view(), name='createtodoroom'),
    path('createtodo/', TodoCreateView.as_view(), name='createtodo'),

]
