from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import jwt

from apps.authentication.exceptions import SocialAuthError


@dataclass(frozen=True)
class SocialIdentity:
    provider: str
    uid: str
    email: str
    email_verified: bool
    name: str = ''
    surname: str = ''


class BaseSocialProvider(ABC):
    provider: str

    @abstractmethod
    def verify(self, token: str, *, nonce: str | None = None) -> SocialIdentity:
        """Validates the provider token and returns who the user is. Raises SocialAuthError."""


@cache
def _get_jwks_client(url: str) -> jwt.PyJWKClient:
    # one client per URL for the whole process, so provider keys are cached between requests
    return jwt.PyJWKClient(url, cache_keys=True)


class OIDCProvider(BaseSocialProvider, ABC):
    """Verifies an OpenID Connect id_token (RS256) against the provider's public keys (JWKS)."""

    jwks_url: str
    issuers: tuple[str, ...]
    client_ids_setting: str

    def verify(self, token: str, *, nonce: str | None = None) -> SocialIdentity:
        claims = self._decode(token)

        if nonce is not None and claims.get('nonce') != self._expected_nonce(nonce):
            raise SocialAuthError('Invalid nonce.')

        return self._to_identity(claims)

    @abstractmethod
    def _to_identity(self, claims: dict) -> SocialIdentity:
        ...

    def _expected_nonce(self, nonce: str) -> str:
        return nonce

    def _get_client_ids(self) -> list[str]:
        client_ids = getattr(settings, self.client_ids_setting, None)
        if not client_ids:
            raise ImproperlyConfigured(f'{self.client_ids_setting} is not set')
        return client_ids

    def _get_signing_key(self, token: str):
        return _get_jwks_client(self.jwks_url).get_signing_key_from_jwt(token).key

    def _decode(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                self._get_signing_key(token),
                algorithms=['RS256'],
                audience=self._get_client_ids(),
                issuer=self.issuers,
                leeway=10,
                options={'require': ['iss', 'aud', 'sub', 'exp', 'iat']},
            )
        except (jwt.PyJWTError, jwt.PyJWKClientError) as e:
            raise SocialAuthError(f'Invalid {self.provider} token: {e}')

    @staticmethod
    def _as_bool(value) -> bool:
        # Apple sends some boolean claims as strings
        return value is True or value == 'true'
