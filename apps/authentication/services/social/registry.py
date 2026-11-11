from rest_framework.exceptions import NotFound

from apps.authentication.models import SocialProvider
from apps.authentication.services.social.apple import AppleProvider
from apps.authentication.services.social.base import BaseSocialProvider
from apps.authentication.services.social.google import GoogleProvider

# a new provider = a new BaseSocialProvider subclass + one line here
_PROVIDERS: dict[str, type[BaseSocialProvider]] = {
    SocialProvider.GOOGLE: GoogleProvider,
    SocialProvider.APPLE: AppleProvider,
}


def get_social_provider(name: str) -> BaseSocialProvider:
    provider_class = _PROVIDERS.get(name)
    if provider_class is None:
        raise NotFound(f'Unknown provider "{name}".')
    return provider_class()
