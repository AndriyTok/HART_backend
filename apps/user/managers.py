from django.contrib.auth.base_user import BaseUserManager
from django.db import transaction


class UserManager(BaseUserManager):
    use_in_migrations = True

    @classmethod
    def normalize_email(cls, email):
        return super().normalize_email(email or '').strip().lower()

    # noinspection PyMethodOverriding
    def get_by_natural_key(self, email):
        return self.get(email__iexact=email)

    @transaction.atomic
    def create_user(self, email, password=None, profile: dict | None = None, **extra_fields):
        if not email:
            raise ValueError('The Email must be set')

        user = self.model(email=self.normalize_email(email), **extra_fields)
        # users from Google/Apple have no password
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        # every user has a profile, so `user.profile` is always safe to access
        profile_model = self.model._meta.get_field('profile').related_model
        profile_model.objects.create(user=user, **(profile or {}))

        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_email_verified', True)

        if extra_fields['is_staff'] is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields['is_superuser'] is not True:
            raise ValueError('Superuser must have is_superuser=True')
        if not password:
            raise ValueError('Superuser must have a password')

        return self.create_user(email=email, password=password, **extra_fields)
