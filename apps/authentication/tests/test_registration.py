from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from rest_framework import status

from kombu.exceptions import OperationalError

from apps.authentication.tests.utils import AuthAPITestCase

UserModel = get_user_model()


class RegistrationTests(AuthAPITestCase):
    def register(self, email='Donor@Example.com', password='Str0ng-pass-123', **extra):
        data = {'email': email, 'password': password, **extra}
        with self.captureOnCommitCallbacks(execute=True):
            return self.client.post(reverse('auth_register'), data, format='json')

    def test_register_creates_unverified_user_returns_tokens_and_sends_email(self):
        response = self.register()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.data['user']['email'], 'donor@example.com')
        self.assertFalse(response.data['user']['is_email_verified'])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('https://app.test/verify-email?uid=', mail.outbox[0].body)

    def test_register_succeeds_when_email_broker_is_down(self):
        with patch('core.services.email_service.send_email.delay', side_effect=OperationalError('broker down')):
            with self.assertLogs('core.services.email_service', 'ERROR'):
                response = self.register()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(UserModel.objects.filter(email='donor@example.com').exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_register_with_profile(self):
        response = self.register(profile={'name': 'Ivan', 'surname': 'Franko'})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user']['profile']['name'], 'Ivan')
        self.assertEqual(response.data['user']['profile']['surname'], 'Franko')
        self.assertIn('Hi, Ivan!', mail.outbox[0].alternatives[0][0])

    def test_register_without_profile_still_creates_empty_one(self):
        self.register()
        profile = UserModel.objects.get().profile
        self.assertEqual((profile.name, profile.surname), ('', ''))

    def test_email_is_case_insensitive_unique(self):
        self.register()
        response = self.register(email='DONOR@example.COM')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_weak_password_rejected(self):
        response = self.register(password='12345678')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(UserModel.objects.exists())

    def test_verify_email_link_works_once_even_after_login(self):
        self.register()
        uid, token = self.extract_uid_token(mail.outbox[0])
        # logging in changes last_login; the link must stay valid
        self.client.post(reverse('auth_login'), {'email': 'donor@example.com', 'password': 'Str0ng-pass-123'})

        response = self.client.post(reverse('auth_verify_email'), {'uid': uid, 'token': token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(UserModel.objects.get().is_email_verified)

        response = self.client.post(reverse('auth_verify_email'), {'uid': uid, 'token': token})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_with_garbage(self):
        response = self.client.post(reverse('auth_verify_email'), {'uid': 'zzz', 'token': 'abc-def'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_does_not_reveal_unknown_email(self):
        response = self.client.post(reverse('auth_verify_email_resend'), {'email': 'nobody@example.com'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 0)

    def test_login_is_case_insensitive(self):
        self.register()
        credentials = {'email': 'DONOR@example.com', 'password': 'Str0ng-pass-123'}
        response = self.client.post(reverse('auth_login'), credentials)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_stale_bearer_header_does_not_break_public_endpoints(self):
        self.authenticate('not-a-jwt')
        response = self.register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
