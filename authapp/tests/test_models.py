from authapp.models import CustomUser, Profile
from django.test import TestCase


class TestCustomUserAndProfile(TestCase):

    def test_user_is_created(self):
        CustomUser.objects.create(
                username = "testuser123",
                password ="testpassword123",
                age = 20
        )

        self.assertEqual(CustomUser.objects.count(), 1)
        self.assertEqual(CustomUser.objects.first().username, 'testuser123')

    def test_profile_is_created(self):
        user = CustomUser.objects.create(
                username = "testuser123",
                password ="testpassword123",
                age = 20
        )

        Profile.objects.create(
            user=user,
            bio = "this is a test bio"
        )

        self.assertEqual(Profile.objects.count(), 1)
        self.assertEqual(Profile.objects.first().user, user)
        self.assertEqual(Profile.objects.first().bio, "this is a test bio")

