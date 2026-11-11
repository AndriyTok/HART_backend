import hashlib

from apps.authentication.models import SocialProvider
from apps.authentication.services.social.base import OIDCProvider, SocialIdentity


class AppleProvider(OIDCProvider):
    provider = SocialProvider.APPLE
    jwks_url = 'https://appleid.apple.com/auth/keys'
    issuers = ('https://appleid.apple.com',)
    client_ids_setting = 'APPLE_CLIENT_IDS'

    def _expected_nonce(self, nonce: str) -> str:
        # the client gives Apple sha256(raw nonce) and sends the raw nonce to us
        return hashlib.sha256(nonce.encode()).hexdigest()

    def _to_identity(self, claims: dict) -> SocialIdentity:
        # Apple never puts the name into id_token; the client sends it on the first sign-in only
        return SocialIdentity(
            provider=self.provider,
            uid=claims['sub'],
            email=claims.get('email', ''),
            email_verified=self._as_bool(claims.get('email_verified')),
        )
