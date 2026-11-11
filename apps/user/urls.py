from django.urls import path

from apps.user.views import AdminUserListView, AdminUserUpdateView, MeView, MyProfileView

urlpatterns = [
    path('/me', MeView.as_view(), name='user_me'),
    path('/me/profile', MyProfileView.as_view(), name='user_me_profile'),
    path('', AdminUserListView.as_view(), name='admin_user_list'),
    path('/<int:pk>', AdminUserUpdateView.as_view(), name='admin_user_update'),
]
