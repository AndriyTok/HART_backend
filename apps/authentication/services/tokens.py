from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.tokens import PasswordResetTokenGenerator, default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.exceptions import InvalidActionTokenError

UserModel = get_user_model()

# gives a pair of tokens without password
def issue_tokens(user) -> dict[str, str]:
    refresh = RefreshToken.for_user(user)
    update_last_login(None, user) # sender is not used in the signal, so we can pass None
    return {'access': str(refresh.access_token), 'refresh': str(refresh)}


def blacklist_user_tokens(user) -> None:
    for token in OutstandingToken.objects.filter(user=user, blacklistedtoken__isnull=True):
        BlacklistedToken.objects.get_or_create(token=token)


class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    """
    One-time link: becomes invalid once the email is verified or changed.
    Unlike the password-reset hash it ignores last_login, so logging in does not break the link.
    """
    key_salt = 'apps.authentication.EmailVerificationTokenGenerator'

    def _make_hash_value(self, user, timestamp):
        return f'{user.pk}{user.email}{user.is_email_verified}{timestamp}'


email_verification_token_generator = EmailVerificationTokenGenerator()
# Django's generator is one-time too: its hash includes the password hash and last_login
password_reset_token_generator = default_token_generator


def encode_uid(user) -> str:
    return urlsafe_base64_encode(force_bytes(user.pk))


def get_user_from_action_token(uid: str, token: str, generator: PasswordResetTokenGenerator):
    try:
        user = UserModel.objects.get(pk=force_str(urlsafe_base64_decode(uid)))
    except (TypeError, ValueError, OverflowError, UserModel.DoesNotExist):
        raise InvalidActionTokenError

    if not user.is_active or not generator.check_token(user, token):
        raise InvalidActionTokenError

    return user
