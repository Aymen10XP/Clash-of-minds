import json

from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from quiz.models import Topic


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


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    FRONTEND_URL='http://testserver:5173',
    DEBUG=True,
)
class PasswordResetApiTests(TestCase):
    password = 'secure-test-password-47'

    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='historian',
            email='historian@example.com',
            password=self.password,
            country='TN',
        )

    def post_json(self, path, data):
        return self.client.post(path, json.dumps(data), content_type='application/json')

    def test_request_sends_expiring_reset_link(self):
        response = self.post_json('/api/auth/password-reset/request/', {
            'email': self.user.email.upper(),
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])
        self.assertIn('/reset-password/', mail.outbox[0].body)
        self.assertIn('debugResetUrl', response.json())

    def test_request_does_not_reveal_unknown_email(self):
        response = self.post_json('/api/auth/password-reset/request/', {
            'email': 'unknown@example.com',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
        self.assertNotIn('debugResetUrl', response.json())
        self.assertIn('If an active account', response.json()['message'])

    def test_valid_token_changes_password_and_cannot_be_reused(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        token = default_token_generator.make_token(self.user)
        payload = {
            'uid': uid,
            'token': token,
            'password': 'a-new-secure-password-84',
            'confirmPassword': 'a-new-secure-password-84',
        }

        response = self.post_json('/api/auth/password-reset/confirm/', payload)
        reused_response = self.post_json('/api/auth/password-reset/confirm/', payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(reused_response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('a-new-secure-password-84'))

    def test_invalid_token_and_mismatched_passwords_are_rejected(self):
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        invalid = self.post_json('/api/auth/password-reset/confirm/', {
            'uid': uid,
            'token': 'invalid-token',
            'password': 'a-new-secure-password-84',
            'confirmPassword': 'a-new-secure-password-84',
        })
        mismatch = self.post_json('/api/auth/password-reset/confirm/', {
            'uid': uid,
            'token': default_token_generator.make_token(self.user),
            'password': 'a-new-secure-password-84',
            'confirmPassword': 'different-secure-password-84',
        })

        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(mismatch.status_code, 400)
        self.assertIn('confirmPassword', mismatch.json()['errors'])


class PreferenceMatchingApiTests(TestCase):
    def setUp(self):
        self.topics = [Topic.objects.create(slug=f'topic-{index}', title=f'Topic {index}') for index in range(1, 7)]
        self.user = get_user_model().objects.create_user(
            username='current', email='current@example.com', password='password-123', country='TN',
        )
        self.user.favorite_topics.set(self.topics[:4])
        self.client.force_login(self.user)

    def create_player(self, username, topics, **overrides):
        player = get_user_model().objects.create_user(
            username=username,
            email=f'{username}@example.com',
            password='password-123',
            country='US',
            **overrides,
        )
        player.favorite_topics.set(topics)
        return player

    def test_matches_only_returns_active_players_strictly_above_75_percent(self):
        self.create_player('perfect', self.topics[:4])
        self.create_player('eighty', self.topics[:5])
        self.create_player('seventy_five', self.topics[:3] + [self.topics[4]])
        self.create_player('inactive', self.topics[:4], is_active=False)

        response = self.client.get('/api/auth/matches/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [(match['username'], match['matchRate']) for match in response.json()['matches']],
            [('perfect', 100), ('eighty', 89)],
        )

    def test_profile_accepts_four_to_five_unique_favorites(self):
        response = self.client.post('/api/auth/profile/', json.dumps({
            'username': self.user.username,
            'favoriteTopics': [topic.slug for topic in self.topics[:5]],
        }), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['user']['favoriteTopics']), 5)

        rejected = self.client.post('/api/auth/profile/', json.dumps({
            'username': self.user.username,
            'favoriteTopics': [topic.slug for topic in self.topics],
        }), content_type='application/json')
        self.assertEqual(rejected.status_code, 400)

        too_few = self.client.post('/api/auth/profile/', json.dumps({
            'username': self.user.username,
            'favoriteTopics': [topic.slug for topic in self.topics[:3]],
        }), content_type='application/json')
        self.assertEqual(too_few.status_code, 400)


class AdminUserApiTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            username='staff', email='staff@example.com', password='password-123', country='TN', is_staff=True,
        )
        self.player = get_user_model().objects.create_user(
            username='player', email='player@example.com', password='password-123', country='TN',
        )

    def test_staff_can_deactivate_but_user_is_not_deleted(self):
        self.client.force_login(self.staff)
        response = self.client.post(f'/api/auth/admin/users/{self.player.pk}/deactivate/', '{}', content_type='application/json')

        self.assertEqual(response.status_code, 200)
        self.player.refresh_from_db()
        self.assertFalse(self.player.is_active)
        self.assertTrue(get_user_model().objects.filter(pk=self.player.pk).exists())

    def test_non_staff_cannot_manage_users(self):
        self.client.force_login(self.player)
        self.assertEqual(self.client.get('/api/auth/admin/users/').status_code, 403)
