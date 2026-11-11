from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidActionTokenError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Link is invalid or expired.'
    default_code = 'invalid_token'


# plain APIException, not AuthenticationFailed: DRF turns the latter into 403 on views without authenticators
class SocialAuthError(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = 'Social authentication failed.'
    default_code = 'social_auth_failed'
