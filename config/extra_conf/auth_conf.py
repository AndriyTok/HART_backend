import os

AUTH_USER_MODEL = 'user.UserModel'

# Base URL of the client app; links in emails point here (e.g. {FRONTEND_URL}/verify-email?uid=..&token=..)
FRONTEND_URL = (os.environ.get('FRONTEND_URL') or 'http://localhost:3000').rstrip('/')

# Lifetime (seconds) of email-verification and password-reset links
PASSWORD_RESET_TIMEOUT = 60 * 60 * 2


def _split_env(name: str) -> list[str]:
    return [value.strip() for value in os.environ.get(name, '').split(',') if value.strip()]


GOOGLE_CLIENT_IDS = _split_env('GOOGLE_CLIENT_IDS')
APPLE_CLIENT_IDS = _split_env('APPLE_CLIENT_IDS')
