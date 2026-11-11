from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.user.models import ProfileModel

UserModel = get_user_model()


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileModel
        fields = ('name', 'surname', 'updated_at')
        read_only_fields = ('updated_at',)


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    has_password = serializers.SerializerMethodField()
    social_providers = serializers.SlugRelatedField(
        source='social_accounts', slug_field='provider', many=True, read_only=True
    )

    class Meta:
        model = UserModel
        fields = (
            'id',
            'email',
            'is_email_verified',
            'has_password',
            'social_providers',
            'profile',
            'last_login',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_has_password(self, user) -> bool:
        return user.has_usable_password()


class AdminUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = UserModel
        fields = (
            'id',
            'email',
            'is_active',
            'is_staff',
            'is_email_verified',
            'profile',
            'last_login',
            'created_at',
        )
        read_only_fields = ('id', 'email', 'is_email_verified', 'last_login', 'created_at')
