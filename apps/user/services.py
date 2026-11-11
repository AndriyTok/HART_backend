from django.db import transaction

from apps.authentication.services.tokens import blacklist_user_tokens


@transaction.atomic
def delete_user(user) -> None:
    # refresh tokens must be revoked first: after deletion they would point to a missing user
    blacklist_user_tokens(user)
    user.delete()
