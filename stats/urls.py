from django.urls import path
from .views import *
from .notice_seen_views import NoticesStatusView, MarkAsReadView

urlpatterns = [
    path('room/<uuid:room_id>/notices/', NoticeView.as_view(), name='room-notices'),
    path('room/<uuid:room_id>/addnotice/',NoticeCreateView.as_view(), name='add-notice' ),
    path('notice/<uuid:notice_id>/deletenotice/',DeleteNoticeView.as_view(), name='delete-notice' ),
    path('toggle-pin/<uuid:notice_id>/', toggle_pin, name='toggle-pin'),
    path('session/<uuid:session_id>/', SessionStats.as_view(), name='session-stats'),
    path('session/<uuid:session_id>/userstats', UserSessionStats.as_view(), name='user-session-stats'),

    path('notices/<uuid:room_id>', NoticesStatusView.as_view(), name='notice-actions'),
    path('notices/mark-as-read', MarkAsReadView.as_view(), name='notice-mark-as-read'),
    path('user-stats/', UserStatsView.as_view(), name='my-stats')
]
