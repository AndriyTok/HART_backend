from apps.authentication.models import SocialProvider
from apps.authentication.services.social.base import OIDCProvider, SocialIdentity


class GoogleProvider(OIDCProvider):
    provider = SocialProvider.GOOGLE
    jwks_url = 'https://www.googleapis.com/oauth2/v3/certs'
    issuers = ('https://accounts.google.com', 'accounts.google.com')
    client_ids_setting = 'GOOGLE_CLIENT_IDS'

    def _to_identity(self, claims: dict) -> SocialIdentity:
        return SocialIdentity(
            provider=self.provider,
            uid=claims['sub'],
            email=claims.get('email', ''),
            email_verified=self._as_bool(claims.get('email_verified')),
            name=claims.get('given_name', ''),
            surname=claims.get('family_name', ''),
        )
