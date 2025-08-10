from django.urls import reverse_lazy
from django.test import TestCase
from pages.models import CustomUser, Room, Session, SessionRanking, RoomRanking, Todo, TrackTodo
import json


class TestRoomViews(TestCase):

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

        cls.create_session_url = reverse_lazy("createsession")
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
    


    def test_room_creation(self):
        url = self.create_room_url

        self.login()

        data = {
            'name' : 'a test room',
            'bio' : 'a test bio',
            'password' : 'a test password'
        }

        response = self.client.post(url, data=data)
        # status code check
        self.assertEqual(response.status_code, 302)

        # room should be created 
        room = Room.objects.filter(name="a test room").first()
        self.assertIsNotNone(room)

        # admin should be the user
        self.assertEqual(room.admin, self.user)

        # checks if raw password is not stored
        self.assertNotEqual(room.password, data['password'])
        self.assertTrue(room.check_pass(data['password']))

        # checks if admin is in members list
        self.assertIn(room.admin, room.members.all())

        # check if room is not made with same name
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 200)
        errors = response.context['form'].errors
        self.assertIsNotNone(errors)
        self.assertIn('name', errors)
        


    def test_join_and_view_room(self):
        url = self.join_room_url

        room = self.create_room(admin=self.user1)

        data = {
            'name': room.name,
            'password' : 'itsatestpass'
        }

        self.login()
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)

        # check membership
        self.assertIn(self.user, room.members.all())

        # check room view
        url = self.room_url(room.id)
        
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # check room settings
        url = self.room_settings_url(room.id)
        
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # checking if it allows to a non member
        self.client.login(
            username = self.user2.username,
            password = 'itsmypassword2'
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


        # checking if it allows to a non member

        response = self.client.get(url)

        self.assertEqual(response.status_code, 403)


    def test_room_update(self):
        room = self.create_room()
        room.members.add(self.user2)
        url = self.update_room_info_url(room.id)

        self.login()
        data = {
            'name' : 'changed name',
            'bio': 'changed_bio'
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 302)
        room.refresh_from_db()
        self.assertEqual(room.name, data['name'])
        self.assertEqual(room.bio, data['bio'])

    
        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )
        data = {
            'name' : 'abs name',
            'bio': 'sandas'
        }
        response = self.client.post(url, data=data)

        self.assertEqual(response.status_code, 403)
        

    def test_room_update_password(self):
        room = self.create_room()
        url = self.change_room_pass_url(room.id)

        self.login()
        correct_data = {
            'current_password' : 'itsatestpass',
            'new_password' : "changed password",
            'confirm_password' : 'changed password'
        }
        wrong_password_data = {
            'current_password' : 'a wrong pass',
            'new_password' : "changed password",
            'confirm_password' : 'changed password'
        }
        wrong_confirm_data = {
            'current_password' : 'itsatestpass',
            'new_password' : "changed password",
            'confirm_password' : 'changed and typo password'
        }
        set_no_password_data = {
            'current_password' : 'changed password',
            'new_password' : "",
            'confirm_password' : ''
        }


        response = self.client.post(url, data=wrong_password_data)
        self.assertEqual(response.status_code, 200)
        errors = response.context['form'].errors
        self.assertIsNotNone(errors)
        self.assertIn('current_password', errors)

        response = self.client.post(url, data=wrong_confirm_data)
        self.assertEqual(response.status_code, 200)
        errors = response.context['form'].errors
        self.assertIsNotNone(errors)
        self.assertIn('confirm_password', errors)

        response = self.client.post(url, data=correct_data)
        self.assertEqual(response.status_code, 302)
        room.refresh_from_db()
        # check if hashed password is stored and password is changed
        self.assertNotEqual(room.password, correct_data['new_password'])
        self.assertNotEqual(room.password, correct_data['current_password'])
        self.assertTrue(room.check_pass(correct_data['new_password']))
        self.assertFalse(room.check_pass(correct_data['current_password']))

        response = self.client.post(url, data=set_no_password_data)
        self.assertEqual(response.status_code, 302)
        room.refresh_from_db()
        # check if password is not stored
        self.assertEqual(room.password, "")

        # if not admin tries to enter 
        room.members.add(self.user1)
        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )
        
        response = self.client.post(url, data=correct_data)

        self.assertEqual(response.status_code, 403)

    def test_non_admin_tries_kick_from_room(self):
        url = self.kick_user_url
        room = self.create_room()
        room.members.add(self.user1)
        room.members.add(self.user2)
        room.refresh_from_db()

        # non admin tries
        self.client.login(
            username = self.user1.username,
            password = 'itsmypassword1'
        )
        data = {
            'room_id' : room.id,
            'user_id' : self.user2.id
        }
        self.assertIn(self.user2, room.members.all())

        response = self.client.post(url, data)
        response = json.loads(response.content)
        self.assertFalse(response['success'])
        room.refresh_from_db()
        self.assertIn(self.user2, room.members.all())

    
    def test_admin_tries_kick_from_room(self):
        url = self.kick_user_url
        room = self.create_room()
        room.members.add(self.user1)
        room.members.add(self.user2)
        room.refresh_from_db()

        # admin tries
        self.login()
        data = {
            'room_id' : room.id,
            'user_id' : self.user1.id
        }
        self.assertIn(self.user1, room.members.all())

        response = self.client.post(url, data)
        response = json.loads(response.content)
        self.assertTrue(response['success'])
        room.refresh_from_db()
        self.assertNotIn(self.user1, room.members.all())

    def test_tries_to_kick_admin(self):
        url = self.kick_user_url
        room = self.create_room()
        room.members.add(self.user1)
        room.members.add(self.user2)
        room.refresh_from_db()
        self.assertIn(self.user, room.members.all())

        # admin tries
        self.login()
        data = {
            'room_id' : room.id,
            'user_id' : self.user.id
        }

        response = self.client.post(url, data)
        response = json.loads(response.content)
        self.assertFalse(response['success'])
        room.refresh_from_db()
        self.assertIn(self.user, room.members.all())

    def test_leave_room(self):
        url = self.leave_room_url
        room = self.create_room(admin=self.user1)
        room.members.add(self.user)
        room.refresh_from_db()

        data = {
            'room_id' : room.id
        }

        self.login()

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        room.refresh_from_db()
        self.assertNotIn(self.user, room.members.all())

    def test_admin_leaves_room(self):
        url = self.leave_room_url
        room = self.create_room()

        data = {
            'room_id' : room.id
        }

        self.login()
        
        with self.assertRaises(ValueError) as context:
            self.client.post(url, data=data)
        room.refresh_from_db()
        self.assertIn(self.user, room.members.all())

    def test_transfer_ownership(self):
        url = self.transfer_ownership_url
        room = self.create_room()
        room.members.add(self.user1)
        room.refresh_from_db()
        self.assertEqual(room.admin, self.user)

        data = {
            'room_id' : room.id,
            'new_admin' : self.user1.id
        }
        self.login()
        response = self.client.post(url, data=data)
        room.refresh_from_db()
        self.assertEqual(room.admin, self.user1)

        # former admin is still in the room
        self.assertIn(self.user , room.members.all())

    def test_non_admin_tries_to_transfer_ownership(self):
        url = self.transfer_ownership_url
        room = self.create_room(self.user1)
        room.members.add(self.user)
        room.members.add(self.user2)
        room.refresh_from_db()
        self.assertEqual(room.admin, self.user1)

        data = {
            'room_id' : room.id,
            'new_admin' : self.user2.id
        }
        self.login()
        with self.assertRaises(ValueError) as context:
            self.client.post(url, data=data)
        room.refresh_from_db()
        self.assertEqual(room.admin, self.user1)

        

    def test_leave_room(self):
        url = self.leave_room_url
        room = self.create_room(self.user1)
        room.members.add(self.user)
        room.members.add(self.user2)

        data = {
            'room_id' : room.id,
        }
        self.login()
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 302)
        room.refresh_from_db()
        self.assertNotIn(self.user, room.members.all())



    def test_admin_leaves_room(self):
        url = self.leave_room_url
        room = self.create_room(self.user)
        room.members.add(self.user2)
        room.refresh_from_db()
        self.assertEqual(room.admin, self.user)

        data = {
            'room_id' : room.id,
        }
        self.login()
        
        with self.assertRaises(ValueError) as context:
            self.client.post(url, data=data)

        room.refresh_from_db()
        self.assertEqual(room.admin, self.user)
        self.assertIn(self.user, room.members.all())

        
    def test_delete_room(self):
        url = self.delete_room_url
        room = self.create_room(self.user)
        room.refresh_from_db()

        data = {
            'room_id' : room.id,
        }
        self.login()
        self.client.post(url, data)
        exists = Room.objects.filter(id=room.id).exists()
        self.assertFalse(exists)

    def test_delete_room(self):
        url = self.delete_room_url
        room = self.create_room(self.user1)
        room.members.add(self.user)
        room.refresh_from_db()

        data = {
            'room_id' : room.id,
        }
        self.login()

        with self.assertRaises(ValueError) as context:
            self.client.post(url, data=data)

        exists = Room.objects.filter(id=room.id).exists()
        self.assertTrue(exists)

    



