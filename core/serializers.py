from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserRole
from .services.user_service import UserService
from django.utils import timezone


from inventory.models import (
    Warehouse,
)

from warehouse.models import WarehouseType, ManagerAssignment

from core.models import (
    User,
    UserWarehouseAccess,
)

# =========================================================
# REGISTER
# =========================================================


class RegisterUserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True, required=True, min_length=6)

    role = serializers.CharField(
        write_only=True,
        required=True,
    )

    class Meta:
        model = User
        fields = ["id", "username", "phone_number", "password", "role"]

    # =====================================================
    # VALIDATION ROLE
    # =====================================================

    def validate_role(self, value):

        # Vérifier si on veut créer un ADMIN
        if value == UserRole.ADMIN:

            # Vérifier s'il existe déjà un admin
            admin_exists = User.objects.filter(role=UserRole.ADMIN).exists()

            if admin_exists:

                raise serializers.ValidationError("Un administrateur existe déjà.")

        return value

    # =====================================================
    # CREATE USER
    # =====================================================

    # def create(self, validated_data):

    #     password = validated_data.pop("password")

    #     user = User.objects.create_user(
    #         **validated_data
    #     )

    #     user.set_password(password)
    #     user.save()

    #     return user

    def create(self, validated_data):

        password = validated_data.pop("password")

        # =====================================================
        # REACTIVER UN UTILISATEUR SUPPRIME
        # =====================================================

        user = User.all_objects.filter(username=validated_data["username"]).first()

        if user and user.is_deleted:

            user.is_deleted = False

            # si tu utilises is_active
            user.is_active = True

            user.role = validated_data["role"]

            user.phone_number = validated_data.get("phone_number", user.phone_number)

            user.set_password(password)

            user.save()

            return user

        # =====================================================
        # CREATION NORMALE
        # =====================================================

        user = User.objects.create_user(**validated_data)

        user.set_password(password)
        user.save()

        # =====================================================
        # AFFECTATION AUTOMATIQUE CENTRAL MANAGER
        # =====================================================

        if user.role == UserRole.CENTRAL_MGR:

            central_warehouse = Warehouse.objects.filter(
                warehouse_type=WarehouseType.CENTRAL
            ).first()

            if not central_warehouse:
                raise serializers.ValidationError("Aucun warehouse CENTRAL n'existe.")

            # Accès au warehouse central
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

            # Affectation comme manager du warehouse central
            ManagerAssignment.objects.get_or_create(
                manager=user,
                warehouse=central_warehouse,
                defaults={
                    "start_date": timezone.now().date(),
                    "is_active": True,
                },
            )

        return user


# =========================================================
# JWT TOKEN
# =========================================================


class ObtenTokenPairSerializer(TokenObtainPairSerializer):

    username_field = User.USERNAME_FIELD

    @classmethod
    def get_token(cls, user):

        token = super().get_token(user)

        # Informations personnalisées
        token["username"] = user.username
        token["role"] = user.role

        return token

    def validate(self, attrs):

        username = attrs.get("username")
        password = attrs.get("password")

        # Vérifier utilisateur
        try:
            user = User.objects.get(username=username)

        except User.DoesNotExist:
            raise AuthenticationFailed("Aucun utilisateur trouvé avec ce username.")

        # Vérifier mot de passe
        if not user.check_password(password):
            raise AuthenticationFailed("Mot de passe incorrect.")

        # Génération du token
        data = super().validate(attrs)

        # Ajouter infos utilisateur dans la réponse
        data["user"] = {
            "id": str(user.id),
            "username": user.username,
            "role": user.role,
        }

        return data


# =========================================================
# ALL USERS
# =========================================================
class UserCreateSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User

        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "password",
        )

    def create(self, validated_data):

        return UserService.create_user(validated_data)


# =========================================================
# ALL USERS
# =========================================================


class UsersListSerialiser(serializers.ModelSerializer):

    has_warehouse_access = serializers.SerializerMethodField()
    warehouse_name = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "role",
            "phone_number",
            "is_active",
            "created_at",
            "is_deleted",
            "has_warehouse_access",
            "warehouse_name",
            "permissions",
        ]

    def get_permissions(self, obj):
        return obj.permissions

    def get_has_warehouse_access(self, obj):
        return obj.warehouse_accesses.filter(is_active=True).exists()

    def get_warehouse_name(self, obj):
        access = (
            obj.warehouse_accesses.filter(is_active=True)
            .select_related("warehouse")
            .first()
        )

        return access.warehouse.name if access else None
