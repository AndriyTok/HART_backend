from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from rest_framework import status

from apps.authentication.services.tokens import issue_tokens
from apps.authentication.tests.utils import AuthAPITestCase

UserModel = get_user_model()

PASSWORD = 'Str0ng-pass-123'
NEW_PASSWORD = 'An0ther-strong-456'


class PasswordResetTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserModel.objects.create_user(email='donor@example.com', password=PASSWORD)

    def test_unknown_email_gets_same_response_and_no_email(self):
        known = self.client.post(reverse('auth_password_reset'), {'email': 'donor@example.com'})
        unknown = self.client.post(reverse('auth_password_reset'), {'email': 'nobody@example.com'})

        self.assertEqual(known.status_code, unknown.status_code)
        self.assertEqual(known.data, unknown.data)
        self.assertEqual(len(mail.outbox), 1)

    def test_reset_changes_password_revokes_tokens_and_link_is_one_time(self):
        tokens = issue_tokens(self.user)
        self.client.post(reverse('auth_password_reset'), {'email': 'donor@example.com'})
        uid, token = self.extract_uid_token(mail.outbox[0])

        response = self.client.post(
            reverse('auth_password_reset_confirm'), {'uid': uid, 'token': token, 'password': NEW_PASSWORD}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))
        self.assertTrue(self.user.is_email_verified)

        # old refresh is blacklisted, old access is revoked
        refresh = self.client.post(reverse('auth_refresh'), {'refresh': tokens['refresh']})
        self.assertEqual(refresh.status_code, status.HTTP_401_UNAUTHORIZED)
        self.authenticate(tokens['access'])
        self.assertEqual(self.client.get(reverse('user_me')).status_code, status.HTTP_401_UNAUTHORIZED)
        self.client.credentials()

        again = self.client.post(
            reverse('auth_password_reset_confirm'), {'uid': uid, 'token': token, 'password': 'Third-pass-789!'}
        )
        self.assertEqual(again.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reset_rejects_weak_password(self):
        self.client.post(reverse('auth_password_reset'), {'email': 'donor@example.com'})
        uid, token = self.extract_uid_token(mail.outbox[0])
        response = self.client.post(
            reverse('auth_password_reset_confirm'), {'uid': uid, 'token': token, 'password': '123'}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_social_only_user_sets_password_via_reset(self):
        user = UserModel.objects.create_user(email='social@example.com', password=None)
        self.client.post(reverse('auth_password_reset'), {'email': 'social@example.com'})
        uid, token = self.extract_uid_token(mail.outbox[0])

        response = self.client.post(
            reverse('auth_password_reset_confirm'), {'uid': uid, 'token': token, 'password': NEW_PASSWORD}
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.check_password(NEW_PASSWORD))


class PasswordChangeTests(AuthAPITestCase):
    def test_change_requires_correct_old_password(self):
        user = UserModel.objects.create_user(email='donor@example.com', password=PASSWORD)
        self.authenticate(issue_tokens(user)['access'])

        wrong = self.client.post(
            reverse('auth_password_change'), {'old_password': 'nope', 'new_password': NEW_PASSWORD}
        )
        self.assertEqual(wrong.status_code, status.HTTP_400_BAD_REQUEST)

        ok = self.client.post(
            reverse('auth_password_change'), {'old_password': PASSWORD, 'new_password': NEW_PASSWORD}
        )
        self.assertEqual(ok.status_code, status.HTTP_200_OK)
        self.assertIn('access', ok.data)

    def test_social_only_user_cannot_set_password_with_token_only(self):
        user = UserModel.objects.create_user(email='donor@example.com', password=None)
        self.authenticate(issue_tokens(user)['access'])

        response = self.client.post(
            reverse('auth_password_change'), {'old_password': 'anything', 'new_password': NEW_PASSWORD}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password reset', response.data['detail'])
        user.refresh_from_db()
        self.assertFalse(user.has_usable_password())

    def test_requires_authentication(self):
        response = self.client.post(reverse('auth_password_change'), {'new_password': NEW_PASSWORD})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
