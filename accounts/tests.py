import json

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase


class UserModelTests(TestCase):
    def test_create_user_with_required_profile_fields(self):
        user = get_user_model().objects.create_user(
            username='historian',
            email='historian@example.com',
            password='secure-test-password',
            country='TN',
        )

        self.assertEqual(user.username, 'historian')
        self.assertEqual(user.email, 'historian@example.com')
        self.assertEqual(user.country, 'TN')
        self.assertTrue(user.check_password('secure-test-password'))
        self.assertNotEqual(user.password, 'secure-test-password')

    def test_email_must_be_unique(self):
        user_model = get_user_model()
        user_model.objects.create_user(
            username='first',
            email='player@example.com',
            password='secure-test-password',
            country='TN',
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            user_model.objects.create_user(
                username='second',
                email='player@example.com',
                password='another-secure-password',
                country='US',
            )

    def test_country_uses_two_letter_uppercase_code(self):
        user = get_user_model()(
            username='traveler',
            email='traveler@example.com',
            country='tun',
        )
        user.set_password('secure-test-password')

        with self.assertRaises(ValidationError) as error:
            user.full_clean()

        self.assertIn('country', error.exception.message_dict)


class AuthenticationApiTests(TestCase):
    password = 'secure-test-password-47'

    def create_user(self, **overrides):
        values = {
            'username': 'historian',
            'email': 'historian@example.com',
            'password': self.password,
            'country': 'TN',
        }
        values.update(overrides)
        return get_user_model().objects.create_user(**values)

    def post_json(self, path, data):
        return self.client.post(path, json.dumps(data), content_type='application/json')

    def test_register_creates_user_with_hashed_password(self):
        response = self.post_json('/api/auth/register/', {
            'username': 'new_player',
            'email': 'PLAYER@example.com',
            'country': 'tn',
            'password': self.password,
            'confirmPassword': self.password,
        })

        self.assertEqual(response.status_code, 201)
        user = get_user_model().objects.get(username='new_player')
        self.assertEqual(user.email, 'player@example.com')
        self.assertEqual(user.country, 'TN')
        self.assertTrue(user.check_password(self.password))
        self.assertNotEqual(user.password, self.password)
        self.assertNotIn('password', response.json()['user'])

    def test_register_returns_validation_errors(self):
        self.create_user(email='player@example.com')

        response = self.post_json('/api/auth/register/', {
            'username': 'new_player',
            'email': 'PLAYER@example.com',
            'country': 'TN',
            'password': self.password,
            'confirmPassword': 'different-password-47',
        })

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.json()['errors'])
        self.assertIn('password2', response.json()['errors'])

    def test_login_accepts_username_and_creates_session(self):
        user = self.create_user()

        response = self.post_json('/api/auth/login/', {
            'identity': user.username,
            'password': self.password,
            'rememberMe': False,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['id'], user.pk)
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)
        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_login_accepts_email_case_insensitively(self):
        user = self.create_user()

        response = self.post_json('/api/auth/login/', {
            'identity': user.email.upper(),
            'password': self.password,
            'rememberMe': True,
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['username'], user.username)
        self.assertFalse(self.client.session.get_expire_at_browser_close())

    def test_login_rejects_invalid_credentials(self):
        self.create_user()

        response = self.post_json('/api/auth/login/', {
            'identity': 'historian',
            'password': 'wrong-password',
        })

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_current_user_reports_anonymous_and_sets_csrf_cookie(self):
        response = self.client.get('/api/auth/me/')

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['authenticated'])
        self.assertIn('csrftoken', response.cookies)

    def test_current_user_returns_logged_in_user(self):
        user = self.create_user()
        self.client.force_login(user)

        response = self.client.get('/api/auth/me/')

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['authenticated'])
        self.assertEqual(response.json()['user']['id'], user.pk)

    def test_logout_clears_session(self):
        self.client.force_login(self.create_user())

        response = self.post_json('/api/auth/logout/', {})

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_csrf_cookie_from_current_user_authorizes_login(self):
        self.create_user()
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_response = csrf_client.get('/api/auth/me/')
        csrf_token = csrf_response.cookies['csrftoken'].value
        body = json.dumps({
            'identity': 'historian',
            'password': self.password,
        })

        rejected_response = csrf_client.post(
            '/api/auth/login/',
            body,
            content_type='application/json',
        )
        accepted_response = csrf_client.post(
            '/api/auth/login/',
            body,
            content_type='application/json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(rejected_response.status_code, 403)
        self.assertEqual(accepted_response.status_code, 200)
