from src.authentication.permissions import SSOPermission
from src.authentication.services.okta import OktaService
from src.authentication.views.base_sso import BaseSSOViewSet


class OktaViewSet(BaseSSOViewSet):

    permission_classes = (SSOPermission,)
    service_class = OktaService
