from rest_framework import status
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView

from apps.authentication.serializers import (
    EmailSerializer,
    PasswordChangeSerializer,
    PasswordResetConfirmSerializer,
    RegisterSerializer,
    SocialLoginSerializer,
    UidTokenSerializer,
)
from apps.authentication.services.password import change_password, confirm_password_reset, request_password_reset
from apps.authentication.services.registration import register_user, resend_verification_email, verify_email
from apps.authentication.services.social.registry import get_social_provider
from apps.authentication.services.social.service import social_login
from apps.authentication.services.tokens import issue_tokens
from apps.user.serializers import UserSerializer


class PublicAuthView(GenericAPIView):
    # no authentication: a stale Bearer header must not break login/registration
    authentication_classes = ()
    permission_classes = (AllowAny,)
    throttle_scope = 'auth'


def _auth_response(user, status_code=status.HTTP_200_OK) -> Response:
    return Response({**issue_tokens(user), 'user': UserSerializer(user).data}, status_code)


class LoginView(TokenObtainPairView):
    throttle_scope = 'auth'


class RefreshView(TokenRefreshView):
    pass


class LogoutView(TokenBlacklistView):
    pass


class RegisterView(PublicAuthView):
    serializer_class = RegisterSerializer

    def post(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        user = register_user(**serializer.validated_data)
        return _auth_response(user, status.HTTP_201_CREATED)


class VerifyEmailView(PublicAuthView):
    serializer_class = UidTokenSerializer

    def post(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        user = verify_email(**serializer.validated_data)
        return Response(UserSerializer(user).data, status.HTTP_200_OK)


class ResendVerificationEmailView(PublicAuthView):
    serializer_class = EmailSerializer

    def post(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        resend_verification_email(**serializer.validated_data)
        return Response({'detail': 'If the email is registered and not verified, a link was sent.'})


class PasswordResetRequestView(PublicAuthView):
    serializer_class = EmailSerializer

    def post(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        request_password_reset(**serializer.validated_data)
        return Response({'detail': 'If the email is registered, a link was sent.'})


class PasswordResetConfirmView(PublicAuthView):
    serializer_class = PasswordResetConfirmSerializer

    def post(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        confirm_password_reset(uid=data['uid'], token=data['token'], new_password=data['password'])
        return Response({'detail': 'Password has been changed.'})


class PasswordChangeView(GenericAPIView):
    serializer_class = PasswordChangeSerializer
    throttle_scope = 'auth'

    def post(self, *args, **kwargs):
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        user = change_password(user=self.request.user, **serializer.validated_data)
        # old tokens are revoked, so the client gets a fresh pair
        return _auth_response(user)


class SocialLoginView(PublicAuthView):
    serializer_class = SocialLoginSerializer

    def post(self, *args, **kwargs):
        provider = get_social_provider(kwargs['provider'])
        serializer = self.get_serializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        identity = provider.verify(data['id_token'], nonce=data.get('nonce'))
        user = social_login(identity, name=data['name'], surname=data['surname'])
        return _auth_response(user)
