from django.test import TestCase
from pages.models import Room, Session, Todo, TrackTodo, RoomRanking, SessionRanking, CustomUser
from django.core.exceptions import ValidationError
from django.utils import timezone

class TestRoomModel(TestCase):

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
        room_data = {
            'name' : "testroom",
            "admin" : self.user2,
            "password" : "itsatestpass"
        }

        room = Room.objects.create(
            **room_data
        )

        # checks if raw password is not stored
        self.assertNotEqual(room.password, room_data['password'])
        self.assertTrue(room.check_pass(room_data['password']))

        # checks if admin is in members list
        self.assertIn(room.admin, room.members.all())


    def test_admin_change(self):
        # room creation 
        room = self.create_room(self.user)
        room.members.add(self.user2)
        room.members.add(self.user1)

        room.transfer_admin(self.user1.id)
        self.assertNotEqual(room.admin, self.user)
        self.assertEqual(room.admin, self.user1)

    def test_remove_member(self):
        # room creation 
        room = self.create_room(self.user)
        room.members.add(self.user1)
        room.members.add(self.user2)

        room.remove_member(self.user1.id)
        self.assertNotIn(self.user1, room.members.all())
        self.assertIn(self.user2, room.members.all())

        with self.assertRaises(ValidationError) as context:
            room.remove_member(self.user.id)

        self.assertEqual(room.admin,self.user)

    
class TestSessionModel(TestCase):

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

        cls.room1 = Room.objects.create(
            name='testroom1',
            bio='testbioo',
            password = 'mypass1234',
            admin = cls.user
        )

        cls.room2 = Room.objects.create(
            name='testroom2',
            bio='testbioo',
            password = 'mypass1234',
            admin = cls.user
        )


    def test_session_creation(self):

        data1 = {
            'room' : self.room1,
            'name' : 'testsession',
            'description' : 'test description',
            'started_at' : timezone.now(),

        }
        
        session1 = Session.objects.create(
            **data1
        )

        # check admin is in members
        self.assertIn(self.room1.admin, session1.members.all())

        # checks if session is active
        self.assertTrue(session1.is_active)

        with self.assertRaises(ValidationError) as context:
            session1.finished_at = session1.started_at - timezone.timedelta(days=3)
            session1.save()

        
        data1['started_at'] = timezone.now() - timezone.timedelta(days=5)
        data1['finished_at'] = timezone.now() - timezone.timedelta(days=3)

        # session name should be unique
        with self.assertRaises(ValidationError) as context:
            session2 = Session.objects.create(
            **data1
            )
        self.assertIn("The name should be unique in a room!", str(context.exception))
        

        # There cannot be two active sessions
        data1['name'] = 'a unique name'
        del data1['finished_at']
        # session name should be unique
        with self.assertRaises(ValidationError) as context:
            session2 = Session.objects.create(
            **data1
            )
        self.assertIn("There is already an active session in this room.", str(context.exception))
        

        # simulate one session ending and one creating
        session1.finished_at = timezone.now()
        session1.save()
        
        session2 = Session.objects.create(
        **data1
        )

        exists = Session.objects.filter(name='a unique name', room=data1['room']).exists()
        self.assertTrue(exists)


class TodoTest(TestCase):

    def test_filled_today(self):
        user = CustomUser.objects.create_user(
            username = 'ame',
            password = 'itsmeprash'
        )

        room = Room.objects.create(
            name='testroom1',
            bio='testbioo',
            password = 'mypass1234',
            admin = user
        )

        data1 = {
            'room' : room,
            'name' : 'testsession',
            'description' : 'test description',
            'started_at' : timezone.now(),

        }
        
        session = Session.objects.create(
            **data1
        )

        todo = Todo.objects.create(
            user = user,
            session = session,
            task = 'a test name'
        )

        # check if todo is created
        self.assertIsNotNone(Todo.objects.first())

        self.assertFalse(todo.filledtoday)

        TrackTodo.objects.create(
            todo = todo,
            hours = 4.9
        )
        
        self.assertEqual(todo.filledtoday, 4.9)

        TrackTodo.objects.create(
            todo = todo,
            hours = 6
        )

        self.assertEqual(todo.filledtoday, 10.9)

        # task completed
        todo.completed = True
        todo.save()

        # tries to add hours
        with self.assertRaises(ValidationError) as context:
            TrackTodo.objects.create(
                todo = todo,
                hours = 6
            )



class IntegratedTestFlow(TestCase):

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

        cls.room1 = Room.objects.create(
            name='testroom1',
            bio='testbioo',
            password = 'mypass1234',
            admin = cls.user
        )

        cls.room2 = Room.objects.create(
            name='testroom2',
            bio='testbioo',
            password = 'mypass1234',
            admin = cls.user
        )

    
    def test_rankings(self):

        # create a session in room1
        session = Session.objects.create(
            room = self.room1,
            name = 'session1',
            description = 'test description',
        )

        # start the session
        session.started_at = timezone.now()
        session.save()

        # members added to the room
        self.room1.members.add(self.user1)
        self.room1.members.add(self.user2)
        self.room1.members.add(self.user3)

        # members added to the session
        session.members.add(self.user1)
        session.members.add(self.user2)

        # users create tasks
        u1_t1 = Todo.objects.create(
            user = self.user1,
            session = session,
            task = "u1's task1"
        )
        u1_t2 = Todo.objects.create(
            user = self.user1,
            session = session,
            task = "u1's task2"
        )

        u2_t1 = Todo.objects.create(
            user = self.user2,
            session = session,
            task = "u1's task1"
        )
        u2_t2 = Todo.objects.create(
            user = self.user2,
            session = session,
            task = "u1's task2"
        )

        # users add hours to the task
        TrackTodo.objects.create(
            todo = u1_t1,
            hours = 2.0
        )
        TrackTodo.objects.create(
            todo = u1_t2,
            hours = 4.0
        )

        TrackTodo.objects.create(
            todo = u2_t1,
            hours = 3.0
        )
        TrackTodo.objects.create(
            todo = u2_t2,
            hours = 8.0
        )

        # check session rankings
        u1_ranking = SessionRanking.objects.filter(session=session, user=self.user1).first()
        u2_ranking = SessionRanking.objects.filter(session=session, user=self.user2).first()

        self.assertIsNotNone(u1_ranking)
        self.assertIsNotNone(u2_ranking)
    
        self.assertEqual(u1_ranking.rank, 2 )
        self.assertEqual(u2_ranking.rank, 1 )

        self.assertEqual(u1_ranking.total_hours, 6.0)
        self.assertEqual(u2_ranking.total_hours, 11.0)

        # user1 added more hours
        TrackTodo.objects.create(
            todo = u1_t1,
            hours = 3.0
        )
        TrackTodo.objects.create(
            todo = u1_t2,
            hours = 4.0
        )
        # check updated session rankings
        u1_ranking = SessionRanking.objects.filter(session=session, user=self.user1).first()
        u2_ranking = SessionRanking.objects.filter(session=session, user=self.user2).first()

        self.assertIsNotNone(u1_ranking)
        self.assertIsNotNone(u2_ranking)
    
        self.assertEqual(u1_ranking.rank, 1 )
        self.assertEqual(u2_ranking.rank, 2 )

        self.assertEqual(u1_ranking.total_hours, 13.0)
        self.assertEqual(u2_ranking.total_hours, 11.0)


        # session ended
        session.finished_at = timezone.now()
        session.save()


        # check room rankings
        u1_ranking = RoomRanking.objects.filter(room=self.room1, user=self.user1).first()
        u2_ranking = RoomRanking.objects.filter(room=self.room1, user=self.user2).first()

        self.assertIsNotNone(u1_ranking)
        self.assertIsNotNone(u2_ranking)
    
        self.assertEqual(u1_ranking.rank, 1 )
        self.assertEqual(u2_ranking.rank, 2 )

        self.assertEqual(u1_ranking.total_hours, 13.0)
        self.assertEqual(u2_ranking.total_hours, 11.0)

        """
        Create another session and check room and session ranking
        """

        session = Session.objects.create(
            room = self.room1,
            name = 'session2',
            description = 'test description',
        )

        # start the session
        session.started_at = timezone.now()
        session.save()

        # members added to the session
        session.members.add(self.user1)
        session.members.add(self.user2)
        session.members.add(self.user3)

        # users create tasks
        u1_t1 = Todo.objects.create(
            user = self.user1,
            session = session,
            task = "u1's task1"
        )
        u1_t2 = Todo.objects.create(
            user = self.user1,
            session = session,
            task = "u1's task2"
        )

        u2_t1 = Todo.objects.create(
            user = self.user2,
            session = session,
            task = "u2's task1"
        )
        u2_t2 = Todo.objects.create(
            user = self.user2,
            session = session,
            task = "u2's task2"
        )

        u3_t1 = Todo.objects.create(
            user = self.user3,
            session = session,
            task = "u3's task2"
        )

        # users add hours to the task
        TrackTodo.objects.create(
            todo = u1_t1,
            hours = 2.0
        )
        TrackTodo.objects.create(
            todo = u1_t2,
            hours = 4.0
        )

        TrackTodo.objects.create(
            todo = u2_t1,
            hours = 3.0
        )
        TrackTodo.objects.create(
            todo = u2_t2,
            hours = 8.0
        )
        TrackTodo.objects.create(
            todo = u3_t1,
            hours = 19.0
        )

        # check session rankings
        u1_ranking = SessionRanking.objects.filter(session=session, user=self.user1).first()
        u2_ranking = SessionRanking.objects.filter(session=session, user=self.user2).first()
        u3_ranking = SessionRanking.objects.filter(session=session, user=self.user3).first()

        self.assertIsNotNone(u1_ranking)
        self.assertIsNotNone(u2_ranking)
        self.assertIsNotNone(u3_ranking)
    
        self.assertEqual(u1_ranking.rank, 3 )
        self.assertEqual(u2_ranking.rank, 2 )
        self.assertEqual(u3_ranking.rank, 1 )

        # Remove user3 from session
        session.remove_member(self.user3.id)

        u3_ranking = SessionRanking.objects.filter(session=session, user=self.user3).first()
        self.assertIsNone(u3_ranking)

        u1_ranking.refresh_from_db()
        u2_ranking.refresh_from_db()

        self.assertEqual(u1_ranking.rank, 2 )
        self.assertEqual(u2_ranking.rank, 1 )

        # end session
        session.finished_at = timezone.now()
        session.save()

        # check room rankings 
        u1_ranking = RoomRanking.objects.filter(room=self.room1, user=self.user1).first()
        u2_ranking = RoomRanking.objects.filter(room=self.room1, user=self.user2).first()

        self.assertIsNotNone(u1_ranking)
        self.assertIsNotNone(u2_ranking)

        self.assertEqual(u1_ranking.rank, 2 )
        self.assertEqual(u2_ranking.rank, 1 )

        self.assertEqual(u1_ranking.total_hours, 19.0)
        self.assertEqual(u2_ranking.total_hours, 22.0)
        

        # remove member from the room
        self.room1.remove_member(self.user2.id)

        u2_ranking = RoomRanking.objects.filter(room=self.room1, user=self.user2).first()
        self.assertIsNone(u2_ranking)
        
        u1_ranking.refresh_from_db()
        self.assertEqual(u1_ranking.rank, 1)


