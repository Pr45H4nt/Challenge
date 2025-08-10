from django.urls import reverse_lazy
from django.test import TestCase
from pages.models import CustomUser, Room, Session, SessionRanking, RoomRanking, Todo, TrackTodo
import json
from django.core.exceptions import ValidationError, PermissionDenied
from django.utils import timezone


class TestTodoView(TestCase):

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
        room.members.add(self.user1)
        room.members.add(self.user2)
        room.save()
        room.refresh_from_db()
        return room
    
    def create_session(self,room=None, **kwargs):

        session_data = {
            'name' : 'testsession1',
            'description': 'test description',
            'room' : room or self.create_room(),
            'start_date' : timezone.now()
        }
        kwargs.update(session_data)
        session = Session.objects.create(**kwargs)
        session.members.add(self.user1)
        session.members.add(self.user2)
        session.save()
        session.refresh_from_db()
        return session

    def create_todo(self, user = None, session=None, **kwargs):
        """
        create and return a session object

        default admin = self.user

        default members = self.user1, self.user2
        """

        todo_data = {
            'user' : user or self.user,
            'session': session or self.create_session(),
            'task' : 'a test task'
        }
        todo_data.update(kwargs)
        todo = Todo.objects.create(**todo_data)
        return todo

    
    def test_todo_creation_by_admin(self):
        session = self.create_session()
        url = self.create_task_from_session_url(session.id)

        self.login()
        data = {
            'task' : 'a simple task'
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        exists = Todo.objects.filter(session = session, task= data['task'], user=self.user).exists()
        self.assertTrue(exists)

    def test_todo_creation_by_member(self):
        session = self.create_session()
        url = self.create_task_from_session_url(session.id)

        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )
        data = {
            'task' : 'a simple task'
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)

        exists = Todo.objects.filter(session = session, task= data['task'], user=self.user1).exists()
        self.assertTrue(exists)

    def test_todo_creation_by_non_member(self):
        session = self.create_session()
        url = self.create_task_from_session_url(session.id)

        self.client.login(
            username = self.user3.username,
            password = 'itsmypassword3'
        )
        data = {
            'task' : 'a simple task'
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 403)

        exists = Todo.objects.filter(session = session, task= data['task'], user=self.user1).exists()
        self.assertFalse(exists)

    def test_remove_todo(self):
        todo = self.create_todo(self.user1)
        url = self.delete_task_url(todo.id)

        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        exists = Todo.objects.filter(id=todo.id).exists()
        self.assertFalse(exists)

    def test_remove_todo_by_non_author(self):
        todo = self.create_todo(self.user1)
        url = self.delete_task_url(todo.id)

        self.login()

        response = self.client.post(url)
        self.assertEqual(response.status_code, 403)

        exists = Todo.objects.filter(id=todo.id).exists()
        self.assertTrue(exists)

    def test_toggle_task(self):
        todo = self.create_todo(self.user1)
        url = self.toggle_task_url(todo.id)
        self.assertFalse(todo.completed)

        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        todo.refresh_from_db()
        self.assertTrue(todo.completed)
        self.assertIsNotNone(todo.completed_on)

        # make it incomplete
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        todo.refresh_from_db()
        self.assertFalse(todo.completed)
        self.assertIsNone(todo.completed_on)



    def test_toggle_task_completed_by_non_author(self):
        todo = self.create_todo(self.user1)
        url = self.toggle_task_url(todo.id)
        self.assertFalse(todo.completed)

        self.login()

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        todo.refresh_from_db()
        self.assertFalse(todo.completed)
        self.assertIsNone(todo.completed_on)
    
    def test_toggle_task_not_completed_by_non_author(self):
        todo = self.create_todo(self.user1, completed= True, completed_on= timezone.now())
        url = self.toggle_task_url(todo.id)
        self.assertTrue(todo.completed)

        self.login()

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        todo.refresh_from_db()
        self.assertTrue(todo.completed)
        self.assertIsNotNone(todo.completed_on)

    def test_toggle_task_in_inactive_session(self):
        todo = self.create_todo(self.user1)
        url = self.toggle_task_url(todo.id)
        self.assertFalse(todo.completed)
        todo.session.finish_date = timezone.now()
        todo.session.save()
        todo.refresh_from_db()

        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        todo.refresh_from_db()
        self.assertFalse(todo.completed)
        self.assertIsNone(todo.completed_on)

    def test_toggle_task_not_completed_in_inactive_session(self):
        todo = self.create_todo(self.user1, completed= True, completed_on= timezone.now())        
        url = self.toggle_task_url(todo.id)
        self.assertTrue(todo.completed)
        todo.session.finish_date = timezone.now()
        todo.session.save()
        todo.refresh_from_db()

        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )

        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        todo.refresh_from_db()
        self.assertTrue(todo.completed)
        self.assertIsNotNone(todo.completed_on)
    

    def test_add_hours(self):
        todo = self.create_todo(self.user1)
        url = self.session_url(todo.session.id)
        self.assertEqual(todo.total_hours, 0)

        data = {
            'todo_id' : todo.id,
            'hours' : '2h 30m'
        }

        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        todo.refresh_from_db()
        self.assertEqual(todo.total_hours, 2.5)

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        todo.refresh_from_db()
        self.assertEqual(todo.total_hours, 5.0)

    def test_add_hours_by_non_author(self):
        todo = self.create_todo(self.user1)
        url = self.session_url(todo.session.id)
        self.assertEqual(todo.total_hours, 0)

        data = {
            'todo_id' : todo.id,
            'hours' : '2h 30m'
        }

        self.login()

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 403)

        todo.refresh_from_db()
        self.assertEqual(todo.total_hours, 0)

















    
