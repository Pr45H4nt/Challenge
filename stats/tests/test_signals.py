from django.test import TestCase
from stats.models import Notice
from pages.models import Room, CustomUser, Session, Todo
from django.urls import reverse_lazy
from django.utils import timezone
import json


class TestSignals(TestCase):
    
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

        cls.room = Room.objects.create(
            name = 'A test room',
            admin = cls.user1
        )
        cls.room.members.add(cls.user)


    def setUp(self):
        self.client.force_login(
            self.user
        )

    
    def test_join_room_signal(self):
        url = reverse_lazy('joinroom')
        self.room.members.remove(self.user)
        
        data = {
            'name' : self.room.name
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        notice = Notice.objects.filter(room=self.room).first()
        self.assertIsNotNone(notice)


    def test_join_session_signal(self):
        session = Session.objects.create(
            name = 'testsession',
            room = self.room
        )


        url = reverse_lazy('joinsession', kwargs = {'session_id':session.id })
    

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        notice = Notice.objects.filter(room=self.room).first()
        self.assertIsNotNone(notice)


    def test_start_session_signal(self):
        self.room.admin = self.user
        self.room.save()
        self.room.refresh_from_db()
        session = Session.objects.create(
            name = 'testsession',
            room = self.room
        )

        url = reverse_lazy('startsession', kwargs = {'session_id': session.id})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        notice = Notice.objects.filter(room=self.room).first()
        self.assertIsNotNone(notice)

    def test_end_session_signal(self):

        self.room.admin = self.user
        self.room.save()
        self.room.refresh_from_db()
        session = Session.objects.create(
            name = 'testsession',
            room = self.room,
            started_at = timezone.now()
        )

        url = reverse_lazy('endsession', kwargs = {'session_id': session.id})

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        notice = Notice.objects.filter(room=self.room).first()
        self.assertIsNotNone(notice)

    def get_ownership(self):

        self.room.admin = self.user
        self.room.save()
        self.room.refresh_from_db()

    def test_create_session_signal(self):
        self.get_ownership()

        data = {
            'name' : 'a test session',
            'bio' : ' random bio'
        }

        url = reverse_lazy('createsession', kwargs = {'room_id': self.room.id})
        response = self.client.post(url, data)

        notice = Notice.objects.filter(room=self.room).first()
        self.assertIsNotNone(notice)

    
    def test_kicked_from_room(self):
        self.get_ownership()

        url = reverse_lazy('kick-user')

        data = {
            'room_id': self.room.id,
            'user_id' : self.user1.id
        }

        response = self.client.post(url, data=data)
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))

        notice = Notice.objects.filter(room=self.room).count()
        self.assertEqual(notice, 1)

    def test_kicked_from_session(self):
        self.get_ownership()
        
        url = reverse_lazy('kick-user-from-session')
        session = Session.objects.create(
            name = 'testsession',
            room = self.room,
            started_at = timezone.now()
        )

        data = {
            'session_id': session.id,
            'user_id' : self.user1.id
        }

        response = self.client.post(url, data=data)
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))

        notice = Notice.objects.filter(room=self.room).count()
        self.assertEqual(notice, 1)


    def test_left_session(self):
        session = Session.objects.create(
            name = 'testsession',
            room = self.room,
            started_at = timezone.now()
        )
        session.members.add(self.user)

        url = reverse_lazy('leave-session')
        data = {
            'session_id' : session.id
        }
        response = self.client.post(url, data)
        data = json.loads(response.content)
        self.assertTrue(data.get('success'))

        notice = Notice.objects.filter(room=self.room).count()
        self.assertEqual(notice, 1)

    def test_left_room(self):
        url = reverse_lazy('leave-room')
        data = {
            'room_id' : self.room.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        notice = Notice.objects.filter(room=self.room).count()
        self.assertEqual(notice, 1)

    def test_transfer_ownership(self):
        url = reverse_lazy('transfer-ownership')
        self.client.force_login(self.user1)
        data = {
            'room_id' : self.room.id,
            'new_admin' : self.user.id
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        notice = Notice.objects.filter(room=self.room).count()
        self.assertEqual(notice, 1)

    def test_task_created(self):
        session = Session.objects.create(
            name = 'testsession',
            room = self.room,
            started_at = timezone.now()
        )
        session.members.add(self.user)

        url = reverse_lazy('createtask', kwargs = {'session_id': session.id})
        data = {
            'task' : "a random task"
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        notice = Notice.objects.filter(room=self.room).count()
        self.assertEqual(notice, 1)

    def test_task_completed(self):
        session = Session.objects.create(
            name = 'testsession',
            room = self.room,
            started_at = timezone.now()
        )
        session.members.add(self.user)

        todo = Todo.objects.create(
            user = self.user,
            session = session,
            task = 'hey whatsup',
            completed = False
        )

        url = reverse_lazy('toggletask', kwargs = {'task_id': todo.id})
    
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        todo.refresh_from_db()
        self.assertTrue(todo.completed)
        notice = Notice.objects.filter(room=self.room).count()
        self.assertEqual(notice, 1)

    
    









    






    






    


        
