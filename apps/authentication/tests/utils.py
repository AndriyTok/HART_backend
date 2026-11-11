import re
import time
from unittest.mock import patch

from django.core.cache import cache
from django.test import override_settings

from rest_framework.test import APITestCase

from core.tasks.email import send_email

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

TEST_PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
GOOGLE_CLIENT_ID = 'test-google-client'
APPLE_CLIENT_ID = 'com.example.hart'


@override_settings(
    FRONTEND_URL='https://app.test',
    GOOGLE_CLIENT_IDS=[GOOGLE_CLIENT_ID],
    APPLE_CLIENT_IDS=[APPLE_CLIENT_ID],
)
class AuthAPITestCase(APITestCase):
    def setUp(self):
        cache.clear()  # throttling counters
        # send emails synchronously into mail.outbox instead of Celery
        patcher = patch('core.services.email_service.send_email.delay', side_effect=lambda **kw: send_email(**kw))
        patcher.start()
        self.addCleanup(patcher.stop)

    @staticmethod
    def extract_uid_token(message) -> tuple[str, str]:
        match = re.search(r'uid=([\w-]+)&(?:amp;)?token=([\w-]+)', message.body)
        return match.group(1), match.group(2)

    def authenticate(self, access: str):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')


def make_id_token(*, iss='https://accounts.google.com', aud=GOOGLE_CLIENT_ID, sub='provider-uid-1', **claims) -> str:
    now = int(time.time())
    payload = {'iss': iss, 'aud': aud, 'sub': sub, 'iat': now, 'exp': now + 600, **claims}
    return jwt.encode(payload, TEST_PRIVATE_KEY, algorithm='RS256')


def patch_provider_keys():
    return patch(
        'apps.authentication.services.social.base.OIDCProvider._get_signing_key',
        return_value=TEST_PRIVATE_KEY.public_key(),
    )
