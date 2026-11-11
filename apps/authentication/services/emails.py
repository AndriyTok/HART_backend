from urllib.parse import urlencode

from django.conf import settings

from core.services.email_service import EmailService

from apps.authentication.services.tokens import (
    email_verification_token_generator,
    encode_uid,
    password_reset_token_generator,
)


def _frontend_link(path: str, user, token: str) -> str:
    return f'{settings.FRONTEND_URL}{path}?{urlencode({"uid": encode_uid(user), "token": token})}'


def send_verification_email(user) -> None:
    url = _frontend_link('/verify-email', user, email_verification_token_generator.make_token(user))
    EmailService.send(
        to=user.email,
        subject='Confirm your email',
        template_name='authentication/emails/verify_email.html',
        context={'name': user.profile.name, 'url': url},
    )


def send_password_reset_email(user) -> None:
    url = _frontend_link('/reset-password', user, password_reset_token_generator.make_token(user))
    EmailService.send(
        to=user.email,
        subject='Password reset',
        template_name='authentication/emails/password_reset.html',
        context={'name': user.profile.name, 'url': url},
    )
