from django.test import TestCase
from stats.models import Notice, CustomUser, Room
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied

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


    def test_notice_create(self):
        room = self.create_room()

        notice = Notice.objects.create(
            room = room,
            author = self.user,
            title = 'Hey How are you',
            content = 'This is the content',
            is_pinned = True,
            is_admin = True
        )

        exists = Notice.objects.filter(
            room = room,
            author = self.user,
            title = 'Hey How are you',
            content = 'This is the content',
            is_pinned = True,
            is_admin = True
        ).exists()

        self.assertTrue(exists)
        self.assertTrue(notice.is_posted_today)

    def test_notice_create_by_member(self):
        room = self.create_room()

        Notice.objects.create(
            room = room,
            author = self.user1,
            title = 'Hey How are you',
            content = 'This is the content',
        )

        exists = Notice.objects.filter(
            room = room,
            author = self.user1,
            title = 'Hey How are you',
            content = 'This is the content',

        ).exists()

        self.assertTrue(exists)

    def test_non_member_tries_to_create_notice(self):
        room = self.create_room()

        with self.assertRaises(PermissionDenied) as context:
            Notice.objects.create(
                room = room,
                author = self.user3,
                title = 'Hey How are you',
                content = 'This is the content',
            )

        exists = Notice.objects.filter(
            room = room,
            author = self.user3,
            title = 'Hey How are you',
            content = 'This is the content',

        ).exists()

        self.assertFalse(exists)

    def test_member_tries_is_admin_create(self):
        room = self.create_room()

        with self.assertRaises(PermissionDenied) as context:
            Notice.objects.create(
                room = room,
                author = self.user2,
                title = 'Hey How are you',
                content = 'This is the content',
                is_admin = True
            )

        exists = Notice.objects.filter(
            room = room,
            author = self.user2,
            title = 'Hey How are you',
            content = 'This is the content',

        ).exists()

        self.assertFalse(exists)

    def test_notice_seen(self):
        room = self.create_room()
        notice = Notice.objects.create(
            room = room,
            author = self.user,
            title = 'Hey How are you',
            content = 'This is the content',
            is_pinned = True,
            is_admin = True
        )

        self.assertTrue(notice.is_read(self.user))
        self.assertFalse(notice.is_read(self.user2))

        notice.mark_as_read(self.user2)
        notice.refresh_from_db()
        self.assertTrue(notice.is_read(self.user2))

