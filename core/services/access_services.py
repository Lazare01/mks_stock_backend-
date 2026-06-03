from inventory.models import Warehouse


class AccessService:

    @staticmethod
    def get_user_warehouse_ids(user):
        """
        Retourne les IDs des agences
        accessibles par l'utilisateur.
        """

        if user.is_superuser:

            return Warehouse.objects.values_list("id", flat=True)

        return user.warehouse_accesses.filter(is_active=True).values_list(
            "warehouse_id", flat=True
        )

    @staticmethod
    def user_can_access_warehouse(user, warehouse):
        """
        Vérifie accès agence.
        """

        if user.is_superuser:
            return True

        return user.has_warehouse_access(warehouse)
