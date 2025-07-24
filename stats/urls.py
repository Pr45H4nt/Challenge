from django.urls import path
from .views import *

urlpatterns = [
    path('room/<uuid:room_id>/notices/', NoticeView.as_view(), name='room-notices'),
    path('room/<uuid:room_id>/addnotice/',NoticeCreateView.as_view(), name='add-notice' ),
    path('notice/<uuid:notice_id>/deletenotice/',DeleteNoticeView.as_view(), name='delete-notice' ),
    path('toggle-pin/<uuid:notice_id>/', toggle_pin, name='toggle-pin'),
    path('session/<uuid:session_id>/', SessionStats.as_view(), name='session-stats'),
    path('session/<uuid:session_id>/userstats', UserSessionStats.as_view(), name='user-session-stats'),

]
