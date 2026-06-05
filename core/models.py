import uuid

from django.db import transaction

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from core.constants.role_permissions import ROLE_PERMISSIONS
from django.utils import timezone
from core.constants.user_roles import UserRole


# permetter  de filtrer les utilisateurs NO DELETED
class ActiveManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().filter(
            is_deleted=False
        )
        
class UserManager(BaseUserManager,ActiveManager):
    

    def create_user(self, username, password=None, **extra_fields):

        # extra_fields.setdefault("is_active", False)

        user = self.model(username=username, **extra_fields)

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, username, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        # # SUPERADMIN ACTIF
        # extra_fields.setdefault("is_active", True)

        user = self.model(username=username, **extra_fields)

        user.set_password(password)

        user.save(using=self._db)

        return user


# =========================================================
# BASE MODELS
# =========================================================


class TimeStampedModel(models.Model):
    """
    Classe abstraite pour :
    - Traçabilité
    - Soft delete
    """
    
    objects=ActiveManager()
    
    all_objects = models.Manager()

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_created",
    )

    is_deleted = models.BooleanField(default=False)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.save(update_fields=["is_deleted"])


# =========================================================
# core/models.py
# =========================================================


class User(AbstractUser, TimeStampedModel):

    objects = UserManager()

    role = models.CharField(
        max_length=30, choices=UserRole.choices, default=UserRole.DEFAULT
    )

    phone_number = models.CharField(max_length=30, blank=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.username} ({self.role})"

    # =====================================================
    # PERMISSIONS
    # =====================================================

    @property
    def permissions(self):
        if self.is_superuser:
            return ["*"]
        return ROLE_PERMISSIONS.get(self.role, [])

    def has_permission(self, permission: str):

        perms = self.permissions

        return "*" in perms or permission in perms

        # =====================================================


# logique de suppression 

    @transaction.atomic
    def soft_delete(self):
        """
        Suppression logique d'un utilisateur.
        """

        if self.is_deleted:
            return

        # Désactiver les accès aux succursales
        self.warehouse_accesses.filter(
            is_active=True
        ).update(
            is_active=False
        )

        # Clôturer les affectations actives
        self.manager_assignments.filter(
            is_active=True
        ).update(
            is_active=False,
            end_date=timezone.now().date()
        )

        # Marquer l'utilisateur supprimé
        self.is_deleted = True

        self.save(
            update_fields=["is_deleted"]
        )
    
    # WAREHOUSE ACCESS
    # =====================================================

    def has_warehouse_access(self, warehouse):
        """
        Vérifie si l'utilisateur
        peut accéder à une agence.
        """

        if self.is_superuser:
            return True

        return self.warehouse_accesses.filter(
            warehouse=warehouse, is_active=True
        ).exists()

    def get_access_for_warehouse(self, warehouse):
        """
        Retourne les permissions locales
        d'une agence.
        """

        if self.is_superuser:
            return None

        return self.warehouse_accesses.filter(
            warehouse=warehouse, is_active=True
        ).first()

    def can_manage_warehouse_stock(self, warehouse):
        """
        Peut gérer le stock ?
        """

        if self.is_superuser:
            return True

        access = self.get_access_for_warehouse(warehouse)

        if not access:
            return False

        return access.can_manage_stock

    def can_transfer_warehouse_stock(self, warehouse):
        """
        Peut transférer du stock ?
        """

        if self.is_superuser:
            return True

        access = self.get_access_for_warehouse(warehouse)

        if not access:
            return False

        return access.can_transfer_stock
    
    


class UserWarehouseAccess(TimeStampedModel):
    """
    Permissions d'un utilisateur
    sur une agence précise.

    IMPORTANT :
    Le rôle définit CE QUE l'utilisateur peut faire.
    Ce modèle définit OÙ il peut le faire.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="warehouse_accesses",
    )

    warehouse = models.ForeignKey(
        "inventory.Warehouse", on_delete=models.CASCADE, related_name="authorized_users"
    )

    # =====================================================
    # Permissions locales
    # =====================================================

    can_view = models.BooleanField(default=True)

    can_manage_stock = models.BooleanField(default=False)

    can_transfer_stock = models.BooleanField(default=False)

    can_manage_sales = models.BooleanField(default=False)

    can_manage_installations = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "core_user_warehouse_access"

        unique_together = ("user", "warehouse")

    def __str__(self):

        return f"{self.user.username} -> {self.warehouse.name}"
