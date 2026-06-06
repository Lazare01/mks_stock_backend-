# core/constants/role_permissions.py

from .permissions import AppPermission
from .user_roles import UserRole

ROLE_PERMISSIONS = {
    UserRole.ADMIN: [
        AppPermission.DASHBOARD_VIEW,
        AppPermission.STOCK_VIEW,
        AppPermission.SUCCURSALE_VIEW,
        AppPermission.STOCK_MANAGE,
        AppPermission.TRANSFER_MANAGE,
        AppPermission.REPORT_VIEW,
        AppPermission.REPORT_VALIDATE,
        AppPermission.FINANCIAL_VIEW,
        AppPermission.AUDIT_VIEW,
        AppPermission.USER_MANAGE,
    ],
    UserRole.CENTRAL_MGR: [
        AppPermission.DASHBOARD_VIEW,
        AppPermission.SUCCURSALE_VIEW,
        AppPermission.USER_MANAGE,
        AppPermission.STOCK_VIEW,
        AppPermission.STOCK_MANAGE,
        AppPermission.TRANSFER_MANAGE,
        AppPermission.REPORT_VIEW,
        AppPermission.FINANCIAL_VIEW,
        AppPermission.AUDIT_VIEW,
        AppPermission.USER_MANAGE,
    ],
    UserRole.BRANCH_MGR: [
        AppPermission.DASHBOARD_VIEW,
        AppPermission.SUCCURSALE_VIEW,
        AppPermission.REPORT_VIEW,
    ],
    UserRole.AUDITOR: [
        AppPermission.DASHBOARD_VIEW,
        AppPermission.REPORT_VIEW,
        AppPermission.REPORT_VALIDATE,
        AppPermission.AUDIT_VIEW,
        AppPermission.FINANCIAL_VIEW,
    ],
    UserRole.ACCOUNTANT: [
        AppPermission.DASHBOARD_VIEW,
        AppPermission.FINANCIAL_VIEW,
    ],
    UserRole.PARTNER: [
        AppPermission.DASHBOARD_VIEW,
        AppPermission.FINANCIAL_VIEW,
        AppPermission.REPORT_VIEW,
    ],
}
