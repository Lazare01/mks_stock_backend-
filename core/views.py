# =========================================================
# core/views.py
# =========================================================
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from rest_framework_simplejwt.views import TokenObtainPairView

from rest_framework.decorators import action, permission_classes, api_view

from .models import User,UserWarehouseAccess
from .serializers import (
    RegisterUserSerializer,
    ObtenTokenPairSerializer,
    UsersListSerialiser,
    UserCreateSerializer,
)
from core.constants.user_roles import UserRole

from .base_viewset import SoftDeleteModelViewSet

from .permissions import CanUserManager

from inventory.models  import Warehouse,WarehouseType,ManagerAssignment


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


class UsersViewSet(viewsets.ModelViewSet):
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

    # =======================================
    # ============= delete user =============
    # =======================================

    @action(detail=True, methods=["delete"], url_path="hard-delete")
    def hard_delete(self, request, pk=None):

        user = User.all_objects.get(pk=pk)

        user.delete()

        return Response(
            {"message": "Utilisateur supprimé définitivement."},
            status=status.HTTP_204_NO_CONTENT,
        )

    # =======================================
    # ============= affecter user  =============
    # =======================================

    @action(
        detail=True,
        methods=["post"],
        url_path="assign-branch",
    )
    def assign_branch(self, request, pk=None):

        manager = self.get_object()

        warehouse_id = request.data.get("warehouse_id")

        if not warehouse_id:
            return Response(
                {"detail": "warehouse_id est obligatoire."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if manager.role != UserRole.BRANCH_MGR:
            return Response(
                {
                    "detail": (
                        "Seuls les utilisateurs ayant le rôle "
                        "BRANCH_MGR peuvent être affectés."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        warehouse = get_object_or_404(
            Warehouse,
            id=warehouse_id,
        )

        if warehouse.warehouse_type != WarehouseType.BRANCH:
            return Response(
                {"detail": ("Le manager doit être affecté " "à une succursale.")},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ==========================================
        # Désactivation des anciens accès
        # ==========================================

        UserWarehouseAccess.objects.filter(
            user=manager,
            is_active=True,
        ).update(
            is_active=False,
        )

        # ==========================================
        # Création du nouvel accès
        # ==========================================

        UserWarehouseAccess.objects.update_or_create(
            user=manager,
            warehouse=warehouse,
            defaults={
                "can_view": True,
                "can_manage_stock": True,
                "can_transfer_stock": True,
                "can_manage_sales": True,
                "can_manage_installations": True,
                "is_active": True,
            },
        )

        # ==========================================
        # Affectation du manager
        # ==========================================

        assignment = ManagerAssignment.objects.create(
            manager=manager,
            warehouse=warehouse,
            start_date=timezone.now().date(),
            is_active=True,
        )

        return Response(
            {
                "message": "Manager affecté avec succès.",
                "assignment_id": assignment.id,
                "manager": {
                    "id": manager.id,
                    "email": manager.email,
                },
                "warehouse": {
                    "id": warehouse.id,
                    "name": warehouse.name,
                },
            },
            status=status.HTTP_201_CREATED,
        )


# **** **** ***** ***** *************************
# ================  check token =================
# ===============================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_token(request):
    return Response("Token is valid")
