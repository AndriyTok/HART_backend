from django.contrib.auth import get_user_model
from django.db import transaction

from apps.authentication.exceptions import SocialAuthError
from apps.authentication.models import SocialAccountModel
from apps.authentication.services.social.base import SocialIdentity
from apps.authentication.services.tokens import blacklist_user_tokens

UserModel = get_user_model()


@transaction.atomic
def social_login(identity: SocialIdentity, *, name: str = '', surname: str = ''):
    """
    Finds or creates the user behind a verified provider identity.
    `name`/`surname` are what the client sent (Apple gives the name to the client only once).
    """
    account = (
        SocialAccountModel.objects.select_related('user__profile')
        .filter(provider=identity.provider, uid=identity.uid)
        .first()
    )

    if account:
        user = account.user
        if identity.email and account.email != identity.email:
            account.email = identity.email
            account.save(update_fields=('email', 'updated_at'))
    else:
        user = _get_or_create_user(identity)
        SocialAccountModel.objects.create(
            user=user, provider=identity.provider, uid=identity.uid, email=identity.email
        )

    if not user.is_active:
        raise SocialAuthError('User account is disabled.')

    _fill_missing_names(user.profile, identity.name or name, identity.surname or surname)
    return user


def _get_or_create_user(identity: SocialIdentity):
    if not identity.email:
        raise SocialAuthError('Provider did not return an email.')

    user = UserModel.objects.filter(email__iexact=identity.email).first()

    if user is None:
        return UserModel.objects.create_user(
            email=identity.email,
            password=None,
            is_email_verified=identity.email_verified,
        )

    # linking by email is safe only if the provider confirmed the user owns that mailbox
    if not identity.email_verified:
        raise SocialAuthError('Email is not verified by the provider; cannot link to the existing account.')

    if not user.is_email_verified:
        # an unverified password account could have been registered by someone else with this email:
        # drop that password so it cannot be used to get into the now-verified account
        user.set_unusable_password()
        user.is_email_verified = True
        user.save(update_fields=('password', 'is_email_verified', 'updated_at'))
        blacklist_user_tokens(user)

    return user


def _fill_missing_names(profile, name: str, surname: str) -> None:
    update_fields = []
    if name and not profile.name:
        profile.name = name[:150]
        update_fields.append('name')
    if surname and not profile.surname:
        profile.surname = surname[:150]
        update_fields.append('surname')
    if update_fields:
        profile.save(update_fields=(*update_fields, 'updated_at'))
