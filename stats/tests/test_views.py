from django.test import TestCase
from stats.models import Notice, CustomUser
from pages.models import Room, Session
from django.urls import reverse_lazy
from django.utils import timezone
import json


class NoticeViewsTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username = 'ame',
            password = 'itsmeprash'
        )
        cls.user1 = CustomUser.objects.create_user(
            username = 'testuser1',
            password = 'itsmypassword1'
        )

        cls.user2 = CustomUser.objects.create_user(
            username = 'testuser2',
            password = 'itsmypassword2'
        )

        cls.user3 = CustomUser.objects.create_user(
            username = 'testuser3',
            password = 'itsmypassword3'
        )

        cls.notice_url = lambda room_id: reverse_lazy('room-notices', kwargs={'room_id': room_id})
        cls.add_notice_url = lambda room_id: reverse_lazy('add-notice', kwargs={'room_id': room_id})
        cls.delete_notice_url = lambda notice_id: reverse_lazy('delete-notice', kwargs={'notice_id': notice_id})
        cls.toggle_pin_url = lambda notice_id: reverse_lazy('toggle-pin', kwargs={'notice_id': notice_id})
        cls.session_stats_url = lambda session_id: reverse_lazy('session-stats', kwargs={'session_id': session_id})
        cls.user_session_stats_url = lambda session_id: reverse_lazy('user-session-stats', kwargs={'session_id': session_id})

    def login(self):
        self.client.login(
            username = 'ame',
            password = 'itsmeprash'
        )


    def create_room(self, admin=None, **kwargs):
        room_data = {
            'name' : "testroom",
            "admin": admin or self.user,
            "password" : "itsatestpass"
        }

        kwargs.update(room_data)

        room = Room.objects.create(
            **kwargs
        )
        room.members.add(self.user)
        room.members.add(self.user1)
        room.members.add(self.user2)
        room.save()
        room.refresh_from_db()
        return room
    
    def create_notice(self, author= None, room = None, **kwargs):
        data = {
            'room': room or self.create_room(),
            'author': author or self.user,
            'title' : 'a test title',
            'content' : 'a test content',
        }
        data.update(kwargs)
        notice = Notice.objects.create(
            **data
        )
        return notice


    
    def test_admin_notice_create(self):
        room = self.create_room(admin=self.user)
        url = self.add_notice_url(room.id)

        self.login()
        data = {
            'title' : 'a test title',
            'content' : 'a test content',
            'is_pinned': True,
            'is_admin' : True,
            'is_html' : True
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        
        data['is_html'] = False
        notice = Notice.objects.filter(**data).first()
        self.assertIsNotNone(notice)

    def test_member_notice_create(self):
        room = self.create_room(admin=self.user1)
        url = self.add_notice_url(room.id)

        self.login()
        data = {
            'title' : 'a test title',
            'content' : 'a test content',
            'is_html' : True
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        
        data['is_html'] = False
        notice = Notice.objects.filter(**data).first()
        self.assertIsNotNone(notice)


    def test_delete_notice(self):
        notice = self.create_notice(author=self.user1)
        url = self.delete_notice_url(notice.id)

        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)

        exists = Notice.objects.filter(id=notice.id).exists()
        self.assertFalse(exists)

    def test_non_author_tries_delete(self):
        notice = self.create_notice(author=self.user1)
        url = self.delete_notice_url(notice.id)

        self.client.login(
            username = self.user2.username,
            password = 'itsmypassword2'
        )
        response = self.client.post(url)

        self.assertEqual(response.status_code, 403)

        exists = Notice.objects.filter(id=notice.id).exists()
        self.assertTrue(exists)

    def test_admin_deletes(self):
        notice = self.create_notice(author=self.user1)
        url = self.delete_notice_url(notice.id)

        self.login()
        response = self.client.post(url)

        self.assertEqual(response.status_code, 302)

        exists = Notice.objects.filter(id=notice.id).exists()
        self.assertFalse(exists)

    def test_toggle_pin(self):
        notice = self.create_notice()
        url = self.toggle_pin_url(notice.id)
        self.assertFalse(notice.is_pinned)

        self.login()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        notice.refresh_from_db()
        self.assertTrue(notice.is_pinned)

        # tries toggle again
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        notice.refresh_from_db()
        self.assertFalse(notice.is_pinned)

    def test_non_admin_tries_toggle_pin(self):
        notice = self.create_notice(author=self.user2)
        url = self.toggle_pin_url(notice.id)
        self.assertFalse(notice.is_pinned)

        self.client.login(
            username = self.user2.username,
            password = 'itsmypassword2'
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        notice.refresh_from_db()
        self.assertFalse(notice.is_pinned)

        # tries again
        notice.is_pinned = True
        notice.save()
        notice.refresh_from_db()
        self.assertTrue(notice.is_pinned)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        notice.refresh_from_db()
        self.assertTrue(notice.is_pinned)


    def create_session(self,room=None, **kwargs):

        session_data = {
            'name' : 'testsession1',
            'description': 'test description',
            'room' : room or self.create_room(),
            'started_at' : timezone.now()
        }
        kwargs.update(session_data)
        session = Session.objects.create(**kwargs)
        session.members.add(self.user)
        session.members.add(self.user1)
        session.members.add(self.user2)
        session.save()
        session.refresh_from_db()
        return session
    
    def test_session_stats_availibility(self):
        room = self.create_room(admin=self.user1)
        session = self.create_session(room=room)
        url = self.session_stats_url(session.id)
        
        self.login()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_non_member_session_stats_availibility(self):
        room = self.create_room(admin=self.user1)
        session = self.create_session(room=room)
        url = self.session_stats_url(session.id)
        
        self.client.login(
            username = 'testuser3',
            password = 'itsmypassword3'
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)



    def test_user_stats_availibility(self):
        room = self.create_room(admin=self.user1)
        session = self.create_session(room=room)
        url = self.user_session_stats_url(session.id)
        self.login()
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_non_member_user_stats_availibility(self):
        room = self.create_room(admin=self.user1)
        session = self.create_session(room=room)
        url = self.user_session_stats_url(session.id)

        self.client.login(
            username = 'testuser3',
            password = 'itsmypassword3'
        )

        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    
    def test_get_unread_notices(self):
        notice1 = self.create_notice(author=self.user1)
        kwargs = {
            'room': notice1.room ,
            'author': self.user2,
            'title' : 'a test title2',
            'content' : 'a test content',
        }
        notice2 = self.create_notice( **kwargs)
        kwargs['author'] = self.user
        notice3 = self.create_notice(**kwargs)


        url = reverse_lazy('notice-actions', kwargs = {'room_id': notice1.room.id})
        
        self.login()
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIsNotNone(data.get('notices'))

        expected_output = {
            str(n.id)
            for n in [notice2, notice1]
        }

        actual_output = {n['id'] for n in data['notices']}

    
        self.assertEqual(expected_output, actual_output)
        
        # mark all as true test
        response = self.client.post(url)
        data = json.loads(response.content)
        self.assertTrue(data['success'])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(len(data.get('notices')), 0)





