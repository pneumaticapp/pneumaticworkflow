from django.conf import settings
from rest_framework.permissions import BasePermission
from pneumatic_backend.payment.messages import MSG_BL_0021


class ProjectBillingPermission(BasePermission):

    message = MSG_BL_0021

    def has_permission(self, request, view):
        return settings.PROJECT_CONF['BILLING']
