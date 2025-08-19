from pages.logics import notice_mark_all_as_seen, get_unread_notices
from django.views.generic import View
from pages.mixins import AdminPermRequired, MemberRequiredMixin,NotDemoUserMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from pages.models import Room
from .models import Notice


class NoticesStatusView(LoginRequiredMixin, MemberRequiredMixin, View):
    def get(self, request, room_id):
        user = request.user
        room = get_object_or_404(Room, id=room_id)
        notices = get_unread_notices(room, user)
        notices_data = [
            {'id': str(n.id), 'title': n.title, 'content': n.content, 'author': 'system', 'is_html' : n.is_html} if not n.author else
            {'id': str(n.id), 'title': n.title, 'content': n.content, 'author': n.author.username, 'is_html' : n.is_html}
            for n in notices 
        ]
        # No use of API serializers 
        return JsonResponse({'notices': notices_data})
        

    def post(self, request, room_id):
        user = request.user
        if room_id:
            room = get_object_or_404(Room, id=room_id)
            notice_mark_all_as_seen(room, user)
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'room_id not set'})
        


class MarkAsReadView(LoginRequiredMixin,MemberRequiredMixin, NotDemoUserMixin, View):
    def post(self, request):
        user = request.user
        notice_id = self.request.POST.get('notice_id')
        if notice_id:
            notice = get_object_or_404(Notice, id=notice_id)
            notice.mark_as_read(user)
            return JsonResponse({'success': True})
        return JsonResponse({'success': False, 'error': 'notice_id not set'})