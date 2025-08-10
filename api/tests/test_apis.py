from rest_framework.test import APIClient, APITestCase
from pages.models import Session, Room, Todo, RoomRanking, SessionRanking, TrackTodo
from django.urls import reverse_lazy, reverse
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from authapp.models import Profile, CustomUser
from django.utils import timezone

class UserAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username = 'ame',
            password = 'itsmeprash'
        )
        cls.get_token_url = reverse_lazy('token_obtain_pair')
        cls.refresh_token_url = reverse_lazy('token_refresh')

    def setUp(self):
        self.client = APIClient()
        response = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION = f"Bearer {response.access_token}")


    def authenticate(self,user):
        response = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION = f"Bearer {response.access_token}")


    def get_token(self, **kwargs):
        url = self.get_token_url
        data = {
            "username" : 'ame',
            "password" : 'itsmeprash'
        }
        data.update(kwargs)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        return response.data

    def test_get_token(self):
        self.get_token()

    def test_invalid_cred_token_generation(self):
        url = self.get_token_url

        data = {
            "username" : 'ame',
            "password" : 'wrong pass'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.assertNotIn('access', response.data)
        self.assertNotIn('refresh', response.data)


    def test_refresh_token(self):
        url = self.refresh_token_url
        token_data = self.get_token()

        data = {
            "refresh" : token_data['refresh'],
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    
    def test_get_user(self):
        url = reverse_lazy('user-api')

        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual('ame', response.data.get('username'))
    
    def test_post_user(self):
        url = reverse_lazy('user-api')

        data = {
            'username' : 'testuser',
            'password' : 'testuserpassword'
        }
        response = self.client.post(url,data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = CustomUser.objects.filter(username= data['username']).first()
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password(data['password']))

    
    def test_profile_get(self):
        # list should not be available
        profile_list_url = reverse_lazy('profile-list')
        response = self.client.get(profile_list_url)
        self.assertEqual(response.status_code, 400)

        my_profile_url = reverse_lazy('profile-my-profile')
        response = self.client.get(my_profile_url)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data.get('message'), 'You don\'t have a profile')
        
        profile = Profile.objects.create(
            user = self.user,
            bio = 'hey this is a test bio'
        )

        my_profile_url = reverse_lazy('profile-my-profile')
        response = self.client.get(my_profile_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.get('username'), profile.user.username)
        self.assertEqual(response.data.get('bio'), profile.bio)

    def test_profile_post(self):
        profile_list_url = reverse_lazy('profile-list')
        data = {
            'bio' : 'its a test bio'
        }
        response = self.client.post(profile_list_url, data)
        self.assertEqual(response.status_code, 201)

        exists = Profile.objects.filter(user = self.user, **data).exists()
        self.assertTrue(exists)

    def make_profile(self):
        profile = Profile.objects.create(
            user = self.user,
            bio = 'hey this is a test bio'
        )
        return profile

    def test_profile_put(self):
        profile = self.make_profile()
        url = reverse_lazy('profile-detail', kwargs={'id':profile.id})

        data = {
            'bio' : 'changed_bio'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, data['bio'])
    
    def test_profile_put(self):
        profile = self.make_profile()
        url = reverse_lazy('profile-detail', kwargs={'pk':profile.id})

        data = {
            'bio' : 'changed_bio'
        }

        response = self.client.put(url, data)
        self.assertEqual(response.status_code, 200)

        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, data['bio'])

    def test_profile_patch(self):
        profile = self.make_profile()
        url = reverse_lazy('profile-detail', kwargs={'pk':profile.id})

        data = {
            'bio' : 'changed_bio'
        }

        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, 200)

        profile.refresh_from_db()
        self.assertEqual(profile.user, self.user)
        self.assertEqual(profile.bio, data['bio'])


class RoomAPITest(APITestCase):
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

        cls.room = Room.objects.create(
            name = 'testroomname',
            bio = 'test room bio',
            admin = cls.user,
            password = 'testpassword'
        )

    def setUp(self):
        self.client = APIClient()
        response = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION = f"Bearer {response.access_token}")

    def authenticate(self,user):
        response = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION = f"Bearer {response.access_token}")


    def test_room_get(self):
        # create room that is not joined
        not_joined_room = Room.objects.create(
            name = 'testroomname123',
            bio = 'test room bio',
            admin = self.user3,
            password = 'testpassword'
        )
        # create another room that is joined
        joined_room = Room.objects.create(
            name = 'joined_testroomname123',
            bio = 'test room bio',
            admin = self.user2,
            password = 'testpassword'
        )
        joined_room.members.add(self.user)
        joined_room.save()
        

        url = reverse_lazy('room-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.data
        
        expected_names = {joined_room.name, self.room.name}
        output_names = {room.get('name') for room in data}
        self.assertEqual(expected_names, output_names)

    def send_request(self, method, url, data=None, status_code=200):
        if method == 'get':
            response = self.client.get(url)
            self.assertEqual(response.status_code, status_code)
            return response
        elif method == 'post':
            response = self.client.post(url, data=data)
            self.assertEqual(response.status_code, status_code)
            return response
        elif method == 'put':
            response = self.client.put(url, data=data)
            self.assertEqual(response.status_code, status_code)
            return response
        elif method == 'patch':
            response = self.client.patch(url, data=data)
            self.assertEqual(response.status_code, status_code)
            return response
        elif method == 'delete':
            response = self.client.delete(url, data=data)
            self.assertEqual(response.status_code, status_code)
            return response
        


    def test_room_post(self):
        url = reverse_lazy('room-list')

        data = {
            'name' : 'hi hello',
            'bio' : 'thi is bio',
        }
        self.send_request('post', url=url, data=data, status_code=201)
        exists = Room.objects.filter(admin = self.user,**data).exists()
        self.assertTrue(exists)

    def test_room_patch(self):
        url = reverse_lazy('room-detail', kwargs = {'pk': self.room.id})
        data = {
            'name' : 'hi hello',
        }
        self.send_request('patch', url=url, data=data)

        exists = Room.objects.filter(admin = self.user,**data, bio = self.room.bio).exists()
        self.assertTrue(exists)

    def test_room_put(self):
        url = reverse_lazy('room-detail', kwargs = {'pk': self.room.id})
        data = {
            'name' : 'hi hello',
            'bio' : 'putted bio'
        }
        self.send_request('put', url=url, data=data)

        exists = Room.objects.filter(admin = self.user,**data).exists()
        self.assertTrue(exists)

    def test_join_room(self):
        room = Room.objects.create(
            name = 'testroomname123',
            bio = 'test room bio',
            admin = self.user3,
            password = 'testpassword'
        )
        data = {
            'name' : room.name,
            'password' : 'testpassword'

        }
        url = reverse_lazy('room-join')
        self.send_request('post',data=data, url=url)
        room.refresh_from_db()
        self.assertIn(self.user, room.members.all())

    def test_join_room_invalid_cred(self):
        room = Room.objects.create(
            name = 'testroomname123',
            bio = 'test room bio',
            admin = self.user3,
            password = 'testpassword'
        )
        data = {
            'name' : room.name,
            'password' : 'wrong word'

        }
        url = reverse_lazy('room-join')
        self.send_request('post',data=data, url=url, status_code=401)
        room.refresh_from_db()
        self.assertNotIn(self.user, room.members.all())


    def test_remove_user(self):
        self.room.members.add(self.user1)
        self.room.save()
        self.assertIn(self.user1, self.room.members.all())

        url = reverse_lazy('room-remove-user', kwargs = {'pk': self.room.id})
        data = {
            'user_id' : self.user1.id
        }
        self.send_request(
            method='post', data=data, status_code=200, url=url
        )

        self.assertNotIn(self.user1, self.room.members.all())

    def test_remove_admin(self):
        self.assertEqual(self.user, self.room.admin)
    
        url = reverse_lazy('room-remove-user', kwargs = {'pk': self.room.id})
        data = {
            'user_id' : self.user.id
        }
        self.send_request(
            method='post', data=data, status_code=400, url=url 
        )

        self.assertIn(self.user, self.room.members.all())

    def test_remove_non_member(self):
        self.assertNotIn(self.user2, self.room.members.all())
    
        url = reverse_lazy('room-remove-user', kwargs = {'pk': self.room.id})
        data = {
            'user_id' : self.user2.id
        }
        self.send_request(
            method='post', data=data, status_code=400, url=url 
        )

        self.assertNotIn(self.user2, self.room.members.all())

    def test_remove_me(self):
        self.room.members.add(self.user1)
        self.room.save()
        self.assertIn(self.user1, self.room.members.all())

        url = reverse_lazy('room-leave', kwargs = {'pk': self.room.id})
        self.authenticate(self.user1)

        self.send_request(
            method='post', url=url,
        )
        self.assertNotIn(self.user1, self.room.members.all())

    def test_transfer_admin(self):
        self.room.members.add(self.user1)
        self.room.save()
        self.assertNotEqual(self.user1, self.room.admin)

        url = reverse_lazy('room-transfer-admin', kwargs = {'pk': self.room.id})
        data = {
            'user_id' : self.user1.id
        }
        self.send_request(
            method='post', url=url, data=data
        )
        self.room.refresh_from_db()
        self.assertEqual(self.user1, self.room.admin)

    def test_transfer_admin_to_non_member(self):
        self.assertNotEqual(self.user1, self.room.admin)

        url = reverse_lazy('room-transfer-admin', kwargs = {'pk': self.room.id})
        data = {
            'user_id' : self.user1.id
        }
        self.send_request(
            method='post', url=url, data=data, status_code=400
        )
        self.room.refresh_from_db()
        self.assertNotEqual(self.user1, self.room.admin)

    def test_get_sessions(self):
        self.room.members.add(self.user1)
        self.room.members.add(self.user2)
        self.room.save()
        url = reverse_lazy('room-sessions', kwargs = {'pk': self.room.id})


        session1 = Session.objects.create(
            name='testsession',
            room = self.room
        )
        session1.members.add(self.user1)
        session1.start_date = timezone.now()- timezone.timedelta(days=2)
        session1.finish_date = timezone.now() # end the session to make another session
        session1.save() # members = user, user1

        session2 = Session.objects.create(
            name='testsession2',
            room = self.room
        )
        session2.members.add(self.user1) 
        session2.members.add(self.user2)
        session2.save() # members = user, user2, user3


        # user
        response = self.send_request(
            method='get', url=url, status_code=200
        )
        self.assertEqual(len(response.data), 2)
        expected_output = {session1.name, session2.name}
        actual_output = {i.get('name') for i in response.data}
        self.assertEqual(expected_output, actual_output)


        # user1
        self.authenticate(self.user1)
        response = self.send_request(
            method='get', url=url, status_code=200
        )
        self.assertEqual(len(response.data), 2)
        expected_output = {session1.name, session2.name}
        actual_output = {i.get('name') for i in response.data}
        self.assertEqual(expected_output, actual_output)

        # user2
        self.authenticate(self.user2)
        response = self.send_request(
            method='get', url=url, status_code=200
        )
        self.assertEqual(len(response.data), 1)
        expected_output = {session2.name}
        actual_output = {i.get('name') for i in response.data}
        self.assertEqual(expected_output, actual_output)


class SessionAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = CustomUser.objects.create_user(
            username='adminuser', password='pass'
        )
        cls.user1 = CustomUser.objects.create_user(
            username='member1', password='pass1'
        )
        cls.user2 = CustomUser.objects.create_user(
            username='member2', password='pass2'
        )

        cls.room = Room.objects.create(
            name='Test Room',
            bio='Room bio',
            admin=cls.user,
            password='roompass'
        )
        cls.room.members.add(cls.user1)

        cls.session = Session.objects.create(
            name='Test Session',
            room=cls.room
        )
        cls.session.members.add(cls.user, cls.user1)

    def setUp(self):
        self.client = APIClient()
        self.authenticate(self.user)

    def authenticate(self, user):
        token = RefreshToken.for_user(user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")

    def send_request(self, method, url, data=None, status_code=200):
        method_map = {
            'get': self.client.get,
            'post': self.client.post,
            'put': self.client.put,
            'patch': self.client.patch,
            'delete': self.client.delete,
        }
        response = method_map[method](url, data=data)
        self.assertEqual(response.status_code, status_code, response.data)
        return response

    def test_list_sessions(self):
        url = reverse_lazy('session-list')
        res = self.send_request('get', url)
        self.assertEqual(len(res.data), 1)

    def test_create_session_as_admin(self):
        # End existing session
        self.session.start_date = timezone.now() - timezone.timedelta(days=5)
        self.session.finish_date = timezone.now()
        self.session.save()

        url = reverse_lazy('session-list')
        data = {'name': 'New Session', 'room': self.room.id}
        self.send_request('post', url, data=data, status_code=201)
        self.assertTrue(Session.objects.filter(name='New Session').exists())

    def test_create_session_as_non_admin_forbidden(self):
        self.authenticate(self.user1)
        url = reverse_lazy('session-list')
        data = {'name': 'Should Fail', 'room': self.room.id}
        self.send_request('post', url, data=data, status_code=400)

    def test_patch_session(self):
        url = reverse_lazy('session-detail', kwargs={'pk': self.session.id})
        data = {'name': 'Patched Name'}
        self.send_request('patch', url, data=data)
        self.assertTrue(Session.objects.filter(id=self.session.id, name='Patched Name').exists())

    def test_put_session(self):
        url = reverse_lazy('session-detail', kwargs={'pk': self.session.id})
        data = {'name': 'Put Name', 'room': self.room.id}
        self.send_request('put', url, data=data)
        self.assertTrue(Session.objects.filter(id=self.session.id, name='Put Name').exists())

    def test_remove_user_from_session(self):
        self.session.members.add(self.user2)
        url = reverse_lazy('session-remove-user', kwargs={'pk': self.session.id})
        data = {'user_id': self.user2.id}
        self.send_request('post', url, data=data, status_code=200)
        self.assertNotIn(self.user2, self.session.members.all())

    def test_remove_user_not_member(self):
        url = reverse_lazy('session-remove-user', kwargs={'pk': self.session.id})
        data = {'user_id': self.user2.id}
        self.send_request('post', url, data=data, status_code=400)

    def test_remove_me(self):
        self.authenticate(self.user1)
        url = reverse_lazy('session-remove-me', kwargs={'pk': self.session.id})
        self.send_request('post', url)
        self.assertNotIn(self.user1, self.session.members.all())

    def test_remove_me_as_admin_fails(self):
        url = reverse_lazy('session-remove-me', kwargs={'pk': self.session.id})
        self.send_request('post', url, status_code=400)

    def test_rankings_endpoint(self):
        SessionRanking.objects.create(session=self.session, user=self.user, rank=1)
        url = reverse_lazy('session-get-session-rankings', kwargs={'pk': self.session.id})
        res = self.send_request('get', url)
        self.assertEqual(len(res.data), 1)

    def test_todos_endpoint(self):
        Todo.objects.create(session=self.session, user=self.user, task='Test Todo')
        url = reverse_lazy('session-get-todos', kwargs={'pk': self.session.id})
        res = self.send_request('get', url)
        self.assertEqual(len(res.data), 1)

    def test_my_todos_endpoint(self):
        Todo.objects.create(session=self.session, user=self.user, task='Mine')
        Todo.objects.create(session=self.session, user=self.user1, task='Not Mine')
        url = reverse_lazy('session-get-my-todos', kwargs={'pk': self.session.id})
        res = self.send_request('get', url)
        self.assertEqual(len(res.data), 1)

    def test_start_session(self):
        url = reverse_lazy('session-start-session', kwargs={'pk': self.session.id})
        self.send_request('post', url, status_code=200)

    def test_end_session(self):
        url = reverse_lazy('session-end-session', kwargs={'pk': self.session.id})
        self.send_request('post', url, status_code=200)








    



    