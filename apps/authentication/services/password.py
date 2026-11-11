from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from rest_framework.exceptions import ValidationError

from apps.authentication.services.emails import send_password_reset_email
from apps.authentication.services.tokens import (
    blacklist_user_tokens,
    get_user_from_action_token,
    password_reset_token_generator,
)

UserModel = get_user_model()


def request_password_reset(*, email: str) -> None:
    # always "succeeds" so the endpoint does not reveal which emails are registered
    user = UserModel.objects.filter(email__iexact=email, is_active=True).first()
    if user:
        send_password_reset_email(user)


def confirm_password_reset(*, uid: str, token: str, new_password: str):
    user = get_user_from_action_token(uid, token, password_reset_token_generator)
    _set_password(user, new_password)
    # the user proved ownership of the mailbox
    if not user.is_email_verified:
        user.is_email_verified = True
        user.save(update_fields=('is_email_verified', 'updated_at'))
    return user


def change_password(*, user, old_password: str, new_password: str):
    # social-only users have no password: an access token alone must not be enough to set one
    # (a stolen token would become a permanent takeover), so they go through the mailbox via password reset
    if not user.has_usable_password():
        raise ValidationError({'detail': 'Account has no password yet. Set one via password reset.'})
    if not user.check_password(old_password):
        raise ValidationError({'old_password': ['Wrong password.']})
    _set_password(user, new_password)
    return user


@transaction.atomic
def _set_password(user, new_password: str) -> None:
    try:
        validate_password(new_password, user)
    except DjangoValidationError as e:
        raise ValidationError({'password': list(e.messages)})

    user.set_password(new_password)
    user.save(update_fields=('password', 'updated_at'))
    # log out every session; access tokens die via SIMPLE_JWT['CHECK_REVOKE_TOKEN']
    blacklist_user_tokens(user)
