from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase


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
