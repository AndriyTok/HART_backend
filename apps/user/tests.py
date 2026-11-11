from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework import status

from apps.authentication.services.tokens import issue_tokens
from apps.authentication.tests.utils import AuthAPITestCase

UserModel = get_user_model()


class MeTests(AuthAPITestCase):
    def setUp(self):
        super().setUp()
        self.user = UserModel.objects.create_user(email='donor@example.com', password='Str0ng-pass-123')
        self.tokens = issue_tokens(self.user)
        self.authenticate(self.tokens['access'])

    def test_get_me(self):
        response = self.client.get(reverse('user_me'))

        self.assertEqual(response.data['email'], 'donor@example.com')
        self.assertEqual((response.data['profile']['name'], response.data['profile']['surname']), ('', ''))

    def test_update_my_profile(self):
        response = self.client.patch(reverse('user_me_profile'), {'name': 'Ivan', 'surname': 'Franko'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual((response.data['name'], response.data['surname']), ('Ivan', 'Franko'))
        self.assertEqual(self.client.get(reverse('user_me')).data['profile']['name'], 'Ivan')

    def test_me_profile_does_not_allow_put(self):
        response = self.client.put(reverse('user_me_profile'), {'name': 'Ivan', 'surname': 'Franko'})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_superuser_gets_profile_too(self):
        admin = UserModel.objects.create_superuser(email='admin@example.com', password='Adm1n-pass-123')
        self.assertEqual(admin.profile.name, '')

    def test_delete_me_revokes_refresh_token(self):
        response = self.client.delete(reverse('user_me'))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(UserModel.objects.exists())

        self.client.credentials()
        refresh = self.client.post(reverse('auth_refresh'), {'refresh': self.tokens['refresh']})
        self.assertEqual(refresh.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_regular_user_cannot_list_users(self):
        self.assertEqual(self.client.get(reverse('admin_user_list')).status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_deactivate_user(self):
        admin = UserModel.objects.create_superuser(email='admin@example.com', password='Adm1n-pass-123')
        self.authenticate(issue_tokens(admin)['access'])

        response = self.client.patch(reverse('admin_user_update', kwargs={'pk': self.user.pk}), {'is_active': False})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)


class QueryCountTests(AuthAPITestCase):
    """
    Guards against N+1. On failure Django prints every executed SQL query,
    so a duplicated SELECT on profiles/social_accounts points to the missing select_related/prefetch_related.
    """

    def setUp(self):
        super().setUp()
        self.admin = UserModel.objects.create_superuser(email='admin@example.com', password='Adm1n-pass-123')
        self.authenticate(issue_tokens(self.admin)['access'])

    def test_me_query_count(self):
        # auth user + profile + social_accounts
        with self.assertNumQueries(3):
            self.client.get(reverse('user_me'))

    def test_admin_user_list_query_count_does_not_grow_with_page_size(self):
        for i in range(10):
            UserModel.objects.create_user(email=f'user{i}@example.com', password='Str0ng-pass-123')

        # auth user + COUNT for pagination + users JOIN profiles
        with self.assertNumQueries(3):
            response = self.client.get(reverse('admin_user_list'), {'size': 10})

        self.assertEqual(len(response.data['data']), 10)
