from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from apps.user.serializers import ProfileSerializer

UserModel = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    profile = ProfileSerializer(required=False)

    def validate_email(self, email):
        email = UserModel.objects.normalize_email(email)
        if UserModel.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError('User with this email already exists.')
        return email

    def validate(self, attrs):
        # unsaved user, so the similarity validator can compare the password with the email
        validate_password(attrs['password'], UserModel(email=attrs['email']))
        return attrs


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class UidTokenSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()


class PasswordResetConfirmSerializer(UidTokenSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, trim_whitespace=False)
    new_password = serializers.CharField(write_only=True, trim_whitespace=False)


class SocialLoginSerializer(serializers.Serializer):
    id_token = serializers.CharField()
    nonce = serializers.CharField(required=False)
    # Apple returns the name to the client on the first sign-in only
    name = serializers.CharField(max_length=150, required=False, default='', allow_blank=True)
    surname = serializers.CharField(max_length=150, required=False, default='', allow_blank=True)
