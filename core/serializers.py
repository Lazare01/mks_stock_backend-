from rest_framework import serializers
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User, UserRole


# =========================================================
# REGISTER
# =========================================================

class RegisterUserSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=True,
        min_length=6
    )
    
    role = serializers.CharField(
        write_only=True,
        required=True,
    )


    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'phone_number',
            'password',
            'role'
        ]
        
    # =====================================================
    # VALIDATION ROLE
    # =====================================================

    def validate_role(self, value):

        # Vérifier si on veut créer un ADMIN
        if value == UserRole.ADMIN:

            # Vérifier s'il existe déjà un admin
            admin_exists = User.objects.filter(
                role=UserRole.ADMIN
            ).exists()

            if admin_exists:

                raise serializers.ValidationError(
                    "Un administrateur existe déjà."
                )

        return value
    # =====================================================
    # CREATE USER
    # =====================================================


    def create(self, validated_data):

        password = validated_data.pop("password")

        user = User.objects.create_user(
            **validated_data
        )

        user.set_password(password)
        user.save()

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
        token['username'] = user.username
        token['role'] = user.role
        
        return token

    def validate(self, attrs):

        username = attrs.get("username")
        password = attrs.get("password")

        # Vérifier utilisateur
        try:
            user = User.objects.get(username=username)

        except User.DoesNotExist:
            raise AuthenticationFailed(
                "Aucun utilisateur trouvé avec ce username."
            )

        # Vérifier mot de passe
        if not user.check_password(password):
            raise AuthenticationFailed(
                "Mot de passe incorrect."
            )

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


class UsersSerialiser(serializers.ModelSerializer):
    class Meta:
        model=User
        fields=[
            "id",
            "username",
            "role",
            "phone_number",
            "is_active",
            "created_at",
            "is_deleted"
        ]