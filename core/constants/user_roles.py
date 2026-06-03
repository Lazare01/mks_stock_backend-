from django.db import models

class UserRole(models.TextChoices):

    ADMIN = "ADMIN", "Administrateur"

    CENTRAL_MGR = "CENTRAL_MGR", "Manager Stock Central"

    BRANCH_MGR = "BRANCH_MGR", "Manager Agence"

    TECH = "TECH", "Technicien"

    ACCOUNTANT = "ACCOUNTANT", "Comptable"

    AUDITOR = "AUDITOR", "Auditeur"

    # NOUVEAU RÔLE
    PARTNER = "PARTNER", "Partenaire"
    
    DEFAULT = "USER", "Par defaut"
