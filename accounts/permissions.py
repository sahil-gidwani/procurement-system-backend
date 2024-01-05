from rest_framework.permissions import BasePermission


class IsProcurementOfficer(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_role == 'procurement_officer'


class IsVendor(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_role == 'vendor'
