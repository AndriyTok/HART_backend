from django.contrib.auth import get_user_model
from django.db import transaction

from apps.authentication.services.emails import send_verification_email
from apps.authentication.services.tokens import email_verification_token_generator, get_user_from_action_token

UserModel = get_user_model()


@transaction.atomic
def register_user(*, email: str, password: str, profile: dict | None = None):
    user = UserModel.objects.create_user(email=email, password=password, profile=profile)
    # email goes out only after the user row is committed (no email for a rolled-back user,
    # and the Celery worker can always find the user)
    transaction.on_commit(lambda: send_verification_email(user))
    return user


def verify_email(*, uid: str, token: str):
    user = get_user_from_action_token(uid, token, email_verification_token_generator)
    user.is_email_verified = True
    user.save(update_fields=('is_email_verified', 'updated_at'))
    return user


def resend_verification_email(*, email: str) -> None:
    # silent when the user does not exist / is already verified, so emails cannot be enumerated
    user = UserModel.objects.filter(email__iexact=email, is_active=True, is_email_verified=False).first()
    if user:
        send_verification_email(user)
