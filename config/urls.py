from django.contrib import admin
from django.urls import include, path

from config.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health', health_check, name='health_check'),
    path('api/auth', include('apps.authentication.urls')),
    path('api/users', include('apps.user.urls')),
]
