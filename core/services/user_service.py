# services/user_service.py
# core/services/user_service.py

from django.db import transaction
from django.utils import timezone

from core.models import User, UserWarehouseAccess
from core.constants.user_roles import UserRole

from inventory.models import (
    Warehouse,
    WarehouseType,
    ManagerAssignment,
)


class UserService:

    @staticmethod
    @transaction.atomic
    def create_user(validated_data):

        password = validated_data.pop("password")

        user = User.objects.create_user(
            password=password,
            **validated_data
        )

        UserService._assign_default_access(user)

        return user

    @staticmethod
    def _assign_default_access(user):

        if user.role == UserRole.CENTRAL_MGR:

            central_warehouse = Warehouse.objects.filter(
                warehouse_type=WarehouseType.CENTRAL
            ).first()

            if not central_warehouse:
                raise ValueError(
                    "Aucun warehouse CENTRAL configuré."
                )

            UserWarehouseAccess.objects.get_or_create(
                user=user,
                warehouse=central_warehouse,
                defaults={
                    "can_view": True,
                    "can_manage_stock": True,
                    "can_transfer_stock": True,
                    "can_manage_sales": True,
                    "can_manage_installations": True,
                    "is_active": True,
                },
            )

            ManagerAssignment.objects.create(
                manager=user,
                warehouse=central_warehouse,
                start_date=timezone.now().date(),
                is_active=True,
            )