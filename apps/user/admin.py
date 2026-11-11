from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm

from apps.authentication.models import SocialAccountModel
from apps.user.models import ProfileModel, UserModel


class UserCreationAdminForm(AdminUserCreationForm):
    class Meta:
        model = UserModel
        fields = ('email',)


class UserChangeAdminForm(UserChangeForm):
    class Meta:
        model = UserModel
        fields = '__all__'


class ProfileInline(admin.StackedInline):
    model = ProfileModel
    can_delete = False
    fields = ('name', 'surname')


class SocialAccountInline(admin.TabularInline):
    model = SocialAccountModel
    extra = 0
    readonly_fields = ('provider', 'uid', 'email', 'created_at')
    can_delete = True


@admin.register(UserModel)
class UserModelAdmin(UserAdmin):
    form = UserChangeAdminForm
    add_form = UserCreationAdminForm
    inlines = (ProfileInline, SocialAccountInline)

    list_display = ('email', 'profile__name', 'profile__surname', 'is_email_verified', 'is_active', 'is_staff')
    list_select_related = ('profile',)
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'is_email_verified')
    search_fields = ('email', 'profile__name', 'profile__surname')
    ordering = ('email',)
    readonly_fields = ('last_login', 'created_at', 'updated_at')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Status', {'fields': ('is_active', 'is_email_verified')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'usable_password', 'password1', 'password2'),
        }),
    )

    def get_inlines(self, request, obj):
        # on the "add user" page the profile is created in save_model, not through the inline
        return self.inlines if obj else ()

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not change:
            ProfileModel.objects.get_or_create(user=obj)
