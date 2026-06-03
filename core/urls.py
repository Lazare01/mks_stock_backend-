from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AuthViewSet, LoginView,check_token,UsersViewSet

router = DefaultRouter()

router.register(r"auth", AuthViewSet, basename="auth")
router.register(r"users", UsersViewSet, basename="users")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/login/", LoginView.as_view(), name="login"),
    path('auth/check_token/',check_token,name='check_token')
]
