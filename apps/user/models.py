from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models.functions import Lower

from core.models import BaseModel

from apps.user.managers import UserManager


class UserModel(AbstractBaseUser, PermissionsMixin, BaseModel):
    class Meta:
        db_table = 'users'
        constraints = [
            models.UniqueConstraint(Lower('email'), name='users_email_ci_unique'),
        ]

    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    EMAIL_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)


class ProfileModel(BaseModel):
    class Meta:
        db_table = 'profiles'

    user = models.OneToOneField(UserModel, on_delete=models.CASCADE, related_name='profile')
    # optional: Apple may not share the name, superusers are created without one
    name = models.CharField(max_length=150, blank=True)
    surname = models.CharField(max_length=150, blank=True)

    def __str__(self):
        return f'{self.name} {self.surname}'.strip() or str(self.user)
