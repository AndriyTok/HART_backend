import hashlib

from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status

from apps.authentication.models import SocialAccountModel
from apps.authentication.tests.utils import APPLE_CLIENT_ID, AuthAPITestCase, make_id_token, patch_provider_keys

UserModel = get_user_model()


class SocialLoginTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        keys = patch_provider_keys()
        keys.start()
        self.addCleanup(keys.stop)

    def social_login(self, provider, **data):
        return self.client.post(reverse('auth_social_login', kwargs={'provider': provider}), data, format='json')

    def google_token(self, **claims):
        claims = {'email': 'donor@gmail.com', 'email_verified': True, 'given_name': 'Ivan', 'family_name': 'Franko',
                  **claims}
        return make_id_token(**claims)

    def test_google_creates_verified_user_without_password(self):
        response = self.social_login('google', id_token=self.google_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        user = UserModel.objects.get()
        self.assertEqual(user.email, 'donor@gmail.com')
        self.assertEqual((user.profile.name, user.profile.surname), ('Ivan', 'Franko'))
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.has_usable_password())
        self.assertEqual(response.data['user']['social_providers'], ['google'])

    def test_second_login_finds_user_by_uid_even_if_email_changed(self):
        self.social_login('google', id_token=self.google_token())
        response = self.social_login('google', id_token=self.google_token(email='new@gmail.com'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(UserModel.objects.count(), 1)
        self.assertEqual(SocialAccountModel.objects.get().email, 'new@gmail.com')

    def test_links_to_existing_verified_user(self):
        user = UserModel.objects.create_user(
            email='donor@gmail.com', password='Str0ng-pass-123', is_email_verified=True
        )

        response = self.social_login('google', id_token=self.google_token(email='Donor@gmail.com'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user']['id'], user.pk)
        user.refresh_from_db()
        self.assertTrue(user.has_usable_password())

    def test_linking_unverified_account_drops_its_password(self):
        user = UserModel.objects.create_user(email='donor@gmail.com', password='Str0ng-pass-123')

        response = self.social_login('google', id_token=self.google_token())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user.refresh_from_db()
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.has_usable_password())

    def test_unverified_provider_email_is_not_linked(self):
        UserModel.objects.create_user(email='donor@gmail.com', password='Str0ng-pass-123')
        response = self.social_login('google', id_token=self.google_token(email_verified=False))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(SocialAccountModel.objects.exists())

    def test_rejects_wrong_audience_issuer_and_signature(self):
        bad_aud = self.social_login('google', id_token=self.google_token(aud='someone-elses-app'))
        bad_iss = self.social_login('google', id_token=self.google_token(iss='https://evil.example'))
        garbage = self.social_login('google', id_token='not.a.jwt')

        for response in (bad_aud, bad_iss, garbage):
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(UserModel.objects.exists())

    def test_inactive_user_cannot_log_in(self):
        self.social_login('google', id_token=self.google_token())
        UserModel.objects.update(is_active=False)
        response = self.social_login('google', id_token=self.google_token())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_unknown_provider(self):
        response = self.social_login('myspace', id_token='x')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_apple_with_hashed_nonce_and_name_from_client(self):
        raw_nonce = 'random-nonce-123'
        token = make_id_token(
            iss='https://appleid.apple.com',
            aud=APPLE_CLIENT_ID,
            sub='apple-uid',
            email='abc@privaterelay.appleid.com',
            email_verified='true',
            nonce=hashlib.sha256(raw_nonce.encode()).hexdigest(),
        )

        response = self.social_login('apple', id_token=token, nonce=raw_nonce, name='Lesya', surname='Ukrainka')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user = UserModel.objects.get()
        self.assertTrue(user.is_email_verified)
        self.assertEqual((user.profile.name, user.profile.surname), ('Lesya', 'Ukrainka'))

        wrong_nonce = self.social_login('apple', id_token=token, nonce='other')
        self.assertEqual(wrong_nonce.status_code, status.HTTP_401_UNAUTHORIZED)
