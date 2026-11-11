from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.generics import GenericAPIView, ListAPIView, RetrieveUpdateAPIView, UpdateAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from apps.user.serializers import AdminUserSerializer, ProfileSerializer, UserSerializer
from apps.user.services import delete_user

UserModel = get_user_model()


class MeView(GenericAPIView):
    def get(self, *args, **kwargs):
        return Response(UserSerializer(self.request.user).data, status.HTTP_200_OK)

    def delete(self, *args, **kwargs):
        delete_user(self.request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MyProfileView(RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    http_method_names = ('get', 'patch')

    def get_object(self):
        return self.request.user.profile


class AdminUserListView(ListAPIView):
    queryset = UserModel.objects.select_related('profile').order_by('-id')
    serializer_class = AdminUserSerializer
    permission_classes = (IsAdminUser,)


class AdminUserUpdateView(UpdateAPIView):
    queryset = UserModel.objects.select_related('profile')
    serializer_class = AdminUserSerializer
    permission_classes = (IsAdminUser,)
    http_method_names = ('patch',)
