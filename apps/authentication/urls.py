from django.urls import path

from apps.authentication.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetRequestView,
    RefreshView,
    RegisterView,
    ResendVerificationEmailView,
    SocialLoginView,
    VerifyEmailView,
)

urlpatterns = [
    path('/register', RegisterView.as_view(), name='auth_register'),
    path('/login', LoginView.as_view(), name='auth_login'),
    path('/refresh', RefreshView.as_view(), name='auth_refresh'),
    path('/logout', LogoutView.as_view(), name='auth_logout'),
    path('/verify-email', VerifyEmailView.as_view(), name='auth_verify_email'),
    path('/verify-email/resend', ResendVerificationEmailView.as_view(), name='auth_verify_email_resend'),
    path('/password/reset', PasswordResetRequestView.as_view(), name='auth_password_reset'),
    path('/password/reset/confirm', PasswordResetConfirmView.as_view(), name='auth_password_reset_confirm'),
    path('/password/change', PasswordChangeView.as_view(), name='auth_password_change'),
    path('/social/<str:provider>', SocialLoginView.as_view(), name='auth_social_login'),
]
