from rest_framework.permissions import BasePermission

from core.constants.permissions import AppPermission


# =========================================================
# BASE GLOBAL PERMISSION
# =========================================================

class HasAppPermission(BasePermission):

    """
    Vérifie les permissions globales.

    Exemple :
    - users.manage
    - stock.transfer
    - sales.create
    """

    required_permission = None

    message = "Permission refusée."

    def has_permission(self, request, view):

        user = request.user

        # =====================================================
        # UTILISATEUR CONNECTE ?
        # =====================================================

        if not user or not user.is_authenticated:
            return False

        # =====================================================
        # SUPER ADMIN
        # =====================================================

        if user.is_superuser:
            return True

        # =====================================================
        # PERMISSION CONFIGUREE ?
        # =====================================================

        if not self.required_permission:
            return False

        # =====================================================
        # VERIFICATION
        # =====================================================

        return user.has_permission(
            self.required_permission
        )


class HasWarehouseAccess(BasePermission):

    """
    Vérifie accès agence.
    """

    message = "Accès à cette agence refusé."

    def has_object_permission(self, request, view, obj):

        user = request.user

        if user.is_superuser:
            return True

        # =====================================================
        # RECUPERATION DU WAREHOUSE
        # =====================================================

        warehouse = getattr(obj, "warehouse", None)

        if not warehouse:
            return False

        return user.has_warehouse_access(
            warehouse
        )


class CanManageWarehouseStock(BasePermission):

    """
    Vérifie permission stock
    + accès agence.
    """

    message = "Gestion du stock refusée."

    def has_object_permission(self, request, view, obj):

        user = request.user

        if user.is_superuser:
            return True

        # =====================================================
        # ROLE
        # =====================================================

        if not user.has_permission(
            AppPermission.STOCK_MANAGE
        ):
            return False

        # =====================================================
        # AGENCE
        # =====================================================

        return user.can_manage_warehouse_stock(
            obj.warehouse
        )


# =========================================================
# USER MANAGEMENT
# =========================================================

class CanUserManager(HasAppPermission):

    required_permission = AppPermission.USER_MANAGE


# =========================================================
# STOCK MANAGEMENT
# =========================================================

class CanManageStock(HasAppPermission):

    required_permission = AppPermission.STOCK_MANAGE


# =========================================================
# STOCK TRANSFER
# =========================================================

class CanTransferStock(HasAppPermission):

    required_permission = AppPermission.STOCK_TRANSFER


# =========================================================
# SALES MANAGEMENT
# =========================================================

class CanManageSales(HasAppPermission):

    required_permission = AppPermission.SALES_MANAGE