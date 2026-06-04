# =========================================================
# core/views.py
# =========================================================

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework.decorators import action, permission_classes, api_view

from .models import User
from .serializers import (
    RegisterUserSerializer,
    ObtenTokenPairSerializer,
    UsersListSerialiser,
    UserCreateSerializer,
)

from .base_viewset import SoftDeleteModelViewSet

from .permissions import CanUserManager


class AuthViewSet(viewsets.GenericViewSet):

    queryset = User.objects.all()

    # =====================================================
    # REGISTER
    # =====================================================

    @action(
        detail=False,
        methods=["post"],
        permission_classes=[IsAuthenticated, CanUserManager],
        serializer_class=RegisterUserSerializer,
    )
    def register(self, request):

        serializer = self.get_serializer(data=request.data)

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        return Response(
            {
                "message": "Utilisateur créé avec succès.",
                "user": {
                    "id": str(user.id),
                    "username": user.username,
                    "phone_number": user.phone_number,
                    "role": user.role,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    # =====================================================
    # ME
    # =====================================================

    @action(detail=False, methods=["get"], permission_classes=[IsAuthenticated])
    def me(self, request):

        user = request.user

        return Response(
            {
                "id": str(user.id),
                "username": user.username,
                "phone_number": user.phone_number,
                "role": user.role,
                "permissions": user.permissions,
                "is_active": user.is_active,
            }
        )


# =========================================================
# LOGIN JWT
# =========================================================


class LoginView(TokenObtainPairView):

    serializer_class = ObtenTokenPairSerializer


# =========================================================
# LOGIN JWT
# =========================================================


class UsersViewSet(SoftDeleteModelViewSet):
    permission_classes = [IsAuthenticated, CanUserManager]
    serializer_class = UsersListSerialiser

    def get_queryset(self):

        if self.request.query_params.get("all") == "true":
            return User.all_objects.exclude(is_superuser=True).exclude(
                id=self.request.user.id
            )

        if self.request.query_params.get("deleted") == "true":
            return (
                User.all_objects.filter(is_deleted=True)
                .exclude(is_superuser=True)
                .exclude(id=self.request.user.id)
            )

        return User.objects.exclude(is_superuser=True).exclude(id=self.request.user.id)

    @action(detail=True, methods=["delete"], url_path="hard-delete")
    def hard_delete(self, request, pk=None):

        user = User.all_objects.get(pk=pk)

        user.delete()

        return Response(
            {"message": "Utilisateur supprimé définitivement."},
            status=status.HTTP_204_NO_CONTENT,
        )


# **** **** ***** ***** *************************
# ================  check token =================
# ===============================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_token(request):
    return Response("Token is valid")
