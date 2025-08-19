from django.test import TestCase
from authapp.models import CustomUser, Profile
from django.urls import reverse_lazy
import json

class TestViews(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create_user(username='ame', password='heythisispass')

        # urls
        self.signup_url = reverse_lazy('signup')
        self.login_url = reverse_lazy('login')
        self.logout_url = reverse_lazy('logout')
        self.changepass_url = reverse_lazy('changepass')
        self.editprofile_url = reverse_lazy('editprofile')
        self.createprofile_url = reverse_lazy('createprofile')
        self.settings_url = reverse_lazy('settings')
        self.profile_url = lambda username: reverse_lazy('profile', kwargs={'username': username})
        self.demo_account_login_url = reverse_lazy('demo-account-login')

    def login(self):
        self.client.login(username='ame', password='heythisispass')


    def test_signup(self):
        url = self.signup_url
        data = {
            'username' : 'testuser',
            'password1' : 'strongpassword123',
            'password2' : 'strongpassword123',

        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse_lazy('editprofile'))

        user = CustomUser.objects.filter(username='testuser').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.username , "testuser")

        self.assertIsNotNone(self.client.session.get('_auth_user_id'), msg="user is not logged in")
        self.assertEqual(int(self.client.session.get('_auth_user_id')), user.id)


    def test_signup_invalid(self):
        url = self.signup_url

        data = {
            'username' : 'testuser',
            'password1' : 'strongpassword123',
            'password2' : 'mismatchhed 124',

        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

        user = CustomUser.objects.filter(username='testuser').first()
        self.assertIsNone(user, msg=f"user = {user}")


    def test_login(self):
        url = self.login_url

        data = {
            'username' : 'ame',
            'password' : 'heythisispass'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertIsNotNone(self.client.session.get('_auth_user_id'))
        self.assertEqual(int(self.client.session.get('_auth_user_id')), self.user.id)


    def test_invalid_login(self):
        url = self.login_url

        data = {
            'username' : 'ame',
            'password' : 'heynotthis'
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)



    def test_logout(self):
        url = self.logout_url
        self.login()

        response = self.client.post(url)

        self.assertIsNone(self.client.session.get('_auth_user_id'))


    def test_password_change(self):
        url = self.changepass_url

        self.login()

        data = {
            'old_password': 'heythisispass',
            'new_password' : 'changedthis',
            'confirm_password' : 'changedthis',
        }

        response = self.client.post(url, data)     

        self.assertEqual(response.status_code, 302)
        user = CustomUser.objects.get(username='ame')
        self.assertTrue(user.check_password(data['new_password']))


    def test_password_change_invalid(self):
        url = self.changepass_url

        self.login()

        data = {
            'old_password': 'heythisispjaasss',
            'new_password' : 'changedthis',
            'confirm_password' : 'chagedthis',
        }

        response = self.client.post(url, data)
        self.assertTrue(response.context['error'])
        self.assertEqual(response.status_code, 200)
        
        user = CustomUser.objects.get(username='ame')

        self.assertFalse(user.check_password(data['new_password']))
        self.assertFalse(user.check_password(data['confirm_password']))


    def test_profile_create(self):
        url = self.createprofile_url

        self.login()

        data = {
            'bio' : "This is a test bio"
        }

        response = self.client.post(url, data)

        profile = Profile.objects.filter(user=self.user).first()
        self.assertIsNotNone(profile)
        self.assertEqual(profile.bio, data['bio'])


    def test_display_profile(self):
        url = self.profile_url('ame')
        self.login()

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_profile_update(self):
        url = self.editprofile_url

        self.login()

        data = {
            "bio" : "this is an edited bio"
        }

        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)
        profile = Profile.objects.get(user=self.user)

        self.assertEqual(profile.bio, data['bio'])

    
    def test_display_settings(self):
        url = self.settings_url

        self.login()
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
    


    def test_display_settings_invalid(self):
        url = self.settings_url

        response = self.client.get(url)

        self.assertEqual(response.status_code, 302)
