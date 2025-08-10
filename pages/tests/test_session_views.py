from django.urls import reverse_lazy
from django.test import TestCase
from pages.models import CustomUser, Room, Session, SessionRanking, RoomRanking, Todo, TrackTodo
import json
from django.core.exceptions import ValidationError
from django.utils import timezone


class TestSessionView(TestCase):

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

        # urls
        cls.home_url = reverse_lazy("home")
        cls.dashboard_url = reverse_lazy("dashboard")
        cls.create_room_url = reverse_lazy("createroom")
        cls.join_room_url = reverse_lazy("joinroom")
        cls.kick_user_url = reverse_lazy("kick-user")
        cls.transfer_ownership_url = reverse_lazy("transfer-ownership")
        cls.delete_room_url = reverse_lazy("delete-room")
        cls.leave_room_url = reverse_lazy("leave-room")

        cls.create_session_url = lambda room_id: reverse_lazy('createsession', kwargs = {'room_id': room_id})
        cls.toggle_task_url = lambda task_id: reverse_lazy("toggletask", kwargs={"task_id": task_id})
        cls.delete_task_url = lambda task_id: reverse_lazy("deletetask", kwargs={"task_id": task_id})
        cls.join_session_url = lambda session_id: reverse_lazy("joinsession", kwargs={"session_id": session_id})
        cls.create_task_from_session_url = lambda session_id: reverse_lazy("createtask", kwargs={"session_id": session_id})
        cls.start_session_url = lambda session_id: reverse_lazy("startsession", kwargs={"session_id": session_id})
        cls.end_session_url = lambda session_id: reverse_lazy("endsession", kwargs={"session_id": session_id})
        cls.kick_user_from_session_url = reverse_lazy("kick-user-from-session")
        cls.leave_session_url = reverse_lazy("leave-session")

        cls.room_url = lambda room_id: reverse_lazy("room", kwargs={"room_id": room_id})
        cls.room_settings_url = lambda room_id: reverse_lazy("room-settings", kwargs={"room_id": room_id})
        cls.update_room_info_url = lambda room_id: reverse_lazy("update-room-info", kwargs={"room_id": room_id})
        cls.change_room_pass_url = lambda room_id: reverse_lazy("change-room-pass", kwargs={"room_id": room_id})
        cls.session_url = lambda session_id: reverse_lazy("session", kwargs={"session_id": session_id})
        cls.session_settings_url = lambda session_id: reverse_lazy("session-settings", kwargs={"session_id": session_id})
        cls.update_session_info_url = lambda session_id: reverse_lazy("update-session-info", kwargs={"session_id": session_id})


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
        return room
    
    def create_session(self,room=None, **kwargs):
        session_data = {
            'name' : 'testsession1',
            'description': 'test description',
            'room' : room or self.create_room()
        }
        kwargs.update(session_data)
        session = Session.objects.create(**kwargs)
        return session

    
    
    def test_session_creation(self):
        room = self.create_room()
        room.members.add(self.user1)
        room.members.add(self.user2)
        room.refresh_from_db()

        url = self.create_session_url(room.id)
        self.login()
        
        data = {
            'name' : 'testsession1',
            'description': 'test description'
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        session = Session.objects.filter(name='testsession1', room=room).first()
        self.assertIsNotNone(session)

        self.assertEqual(session.name, data['name'])
        self.assertEqual(session.description, data['description'])

    def test_non_admin_create_session(self):
        room = self.create_room()
        room.members.add(self.user1)
        room.members.add(self.user2)
        room.refresh_from_db()

        url = self.create_session_url(room.id)
        self.client.login(
            username = 'testuser1',
            password = 'itsmypassword1'
        )
        
        data = {
            'name' : 'testsession1',
            'description': 'test description'
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

        session = Session.objects.filter(name='testsession1', room=room).first()
        self.assertIsNone(session)

    def test_join_session(self):
        room = self.create_room(admin=self.user1)
        room.members.add(self.user)
        session = self.create_session(room=room)

        url = self.join_session_url(session.id)

        self.login()
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        session.refresh_from_db()
        self.assertIn(self.user, session.members.all())

    def test_non_member_of_room_tries_to_join_session(self):
        room = self.create_room(admin=self.user1)
        session = self.create_session(room=room)

        url = self.join_session_url(session.id)

        self.login()
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 403)

        session.refresh_from_db()
        self.assertNotIn(self.user, session.members.all())

    def test_leave_session(self):
        room = self.create_room(admin=self.user1)
        room.members.add(self.user)
        session = self.create_session(room=room)
        session.members.add(self.user)
        session.refresh_from_db()
        self.assertIn(self.user, session.members.all())

        url = self.leave_session_url

        data = {
            'session_id' : session.id
        }
        self.login()
        response = self.client.post(url, data=data)
        response = json.loads(response.content)
        self.assertTrue(response['success'])

        session.refresh_from_db()
        self.assertNotIn(self.user, session.members.all())

    def test_admin_leaves_session(self):
        room = self.create_room(admin=self.user)
        session = self.create_session(room=room)
        session.refresh_from_db()
        self.assertIn(self.user, session.members.all())

        url = self.leave_session_url

        data = {
            'session_id' : session.id
        }
        self.login()
        with self.assertRaises(ValidationError) as context:
            self.client.post(url, data=data)

        session.refresh_from_db()
        self.assertIn(self.user, session.members.all())

    
    def create_usuable_session_with_members(self):
        room = self.create_room()
        room.members.add(self.user1)
        room.members.add(self.user2)
        room.refresh_from_db()
        
        session = self.create_session(room)
        session.members.add(self.user1)
        session.members.add(self.user2)
        session.refresh_from_db()
        return session


    def test_non_admin_tries_kick_from_session(self):
        url = self.kick_user_from_session_url
        session = self.create_usuable_session_with_members()

        # non admin tries
        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )
        data = {
            'session_id' : session.id,
            'user_id' : self.user2.id
        }
        self.assertIn(self.user2, session.members.all())

        with self.assertRaises(ValueError) as context:
            self.client.post(url, data)

        session.refresh_from_db()
        self.assertIn(self.user2, session.members.all())

    def test_admin_tries_kick_from_session(self):
        url = self.kick_user_from_session_url
        session = self.create_usuable_session_with_members()

        # admin tries
        self.login()
        data = {
            'session_id' : session.id,
            'user_id' : self.user1.id
        }
        self.assertIn(self.user1, session.members.all())

        response = self.client.post(url, data)
        response = json.loads(response.content)
        self.assertTrue(response['success'])
        session.refresh_from_db()
        self.assertNotIn(self.user1, session.members.all())

    def test_admin_tries_kick_admin_from_session(self):
        url = self.kick_user_from_session_url
        session = self.create_usuable_session_with_members()

        # admin tries
        self.login()
        data = {
            'session_id' : session.id,
            'user_id' : self.user.id
        }
        self.assertIn(self.user, session.members.all())

        with self.assertRaises(ValidationError) as context:
            self.client.post(url, data)
        
        session.refresh_from_db()
        self.assertIn(self.user1, session.members.all())


    def test_start_session(self):
        # admin = self.user and additional members = self.user1, self.user2
        session = self.create_usuable_session_with_members()

        url = self.start_session_url(session.id)

        # check if its started
        self.assertIsNone(session.start_date)

        # admin logs in
        self.login()
        request = self.client.post(url)
        today = timezone.now().date()
        self.assertEqual(request.status_code, 302)

        # session should be started 
        session.refresh_from_db()
        self.assertIsNotNone(session.start_date)
        
        # since, 'now' can potentially differ, using date only to validate
        self.assertEqual(session.start_date.date(), today)

    def test_non_admin_tries_start_session(self):
        # admin = self.user and additional members = self.user1, self.user2
        session = self.create_usuable_session_with_members()

        url = self.start_session_url(session.id)

        # check if its started
        self.assertIsNone(session.start_date)

        # non-admin logs in
        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )

        request = self.client.post(url)
        self.assertEqual(request.status_code, 302)

        # session should be started 
        session.refresh_from_db()
        self.assertIsNone(session.start_date)
        

    def test_end_session(self):
        # admin = self.user and additional members = self.user1, self.user2
        session = self.create_usuable_session_with_members()
        session.start_date = timezone.now()
        session.save()
        session.refresh_from_db()

        url = self.end_session_url(session.id)

        # check if its started
        self.assertIsNotNone(session.start_date)
        self.assertTrue(session.is_active)

        # admin logs in
        self.login()
        request = self.client.post(url)
        today = timezone.now().date()
        self.assertEqual(request.status_code, 302)

        # session should be started 
        session.refresh_from_db()
        self.assertIsNotNone(session.start_date)
        self.assertIsNotNone(session.finish_date)
        
        # since, 'now' can potentially differ, using date only to validate
        self.assertEqual(session.finish_date.date(), today)

    def test_non_admin_tries_end_session(self):
        # admin = self.user and additional members = self.user1, self.user2
        session = self.create_usuable_session_with_members()
        session.start_date = timezone.now()
        session.save()
        session.refresh_from_db()

        url = self.end_session_url(session.id)

        # check if its started
        self.assertIsNotNone(session.start_date)
        self.assertTrue(session.is_active)

        # admin logs in
        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )
        request = self.client.post(url)
        self.assertEqual(request.status_code, 302)

        # session should be started 
        session.refresh_from_db()
        self.assertIsNotNone(session.start_date)
        self.assertIsNone(session.finish_date)

    
    def test_session_update(self):
        session = self.create_usuable_session_with_members()
        url = self.update_session_info_url(session.id)

        self.login()
        data = {
            'name' : 'a changed name',
            'description': 'a changed description'
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        session.refresh_from_db()
        self.assertEqual(session.name, data['name'])
        self.assertEqual(session.description, data['description'])
    
    def test_non_admin_tries_update_session(self):
        session = self.create_usuable_session_with_members()
        url = self.update_session_info_url(session.id)

        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )
        data = {
            'name' : 'a changed name',
            'description': 'a changed description'
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

        session.refresh_from_db()
        self.assertNotEqual(session.name, data['name'])
        self.assertNotEqual(session.description, data['description'])


    def test_dashboard_status(self):
        session = self.create_usuable_session_with_members()
        url = self.dashboard_url

        self.login()
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    
    


        





    

    