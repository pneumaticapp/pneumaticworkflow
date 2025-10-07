from django.contrib.auth import get_user_model
from django.db.models import ObjectDoesNotExist
from src.accounts.models import Account
from django.conf import settings
from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from src.generics.mixins.views import CustomViewSetMixin
from src.authentication.permissions import Auth0Permission
from src.analytics.mixins import BaseIdentifyMixin
from src.authentication.services.user_auth import (
    AuthService
)
from src.authentication.services.exceptions import (
    AuthException
)
from src.authentication.services.auth0 import (
    Auth0Service
)
from src.authentication.serializers import (
    Auth0TokenSerializer,
)
from src.authentication.views.mixins import SignUpMixin
from src.utils.validation import raise_validation_error
from src.authentication.throttling import (
    Auth0AuthUriThrottle,
    Auth0TokenThrottle,
)
from src.utils.logging import (
    capture_sentry_message,
    SentryLogLevel,
)
from src.authentication.messages import MSG_AU_0003
from src.authentication.tasks import update_auth0_contacts


UserModel = get_user_model()


class Auth0ViewSet(
    SignUpMixin,
    CustomViewSetMixin,
    BaseIdentifyMixin,
    GenericViewSet
):
    permission_classes = (Auth0Permission,)
    serializer_class = Auth0TokenSerializer

    @property
    def throttle_classes(self):
        if self.action == 'token':
            return (Auth0TokenThrottle,)
        elif self.action == 'auth_uri':
            return (Auth0AuthUriThrottle,)
        return ()

    @action(methods=('GET',), detail=False)
    def token(self, request, *args, **kwargs):
        slz = self.get_serializer(data=request.GET)
        slz.is_valid(raise_exception=True)
        try:
            service = Auth0Service()
            user_data = service.get_user_data(
                auth_response={
                    'code': slz.validated_data['code'],
                    'state': slz.validated_data['state'],
                }
            )
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            try:
                user = UserModel.objects.active().get(email=user_data['email'])
                token = AuthService.get_auth_token(
                    user=user,
                    user_agent=request.headers.get(
                        'User-Agent',
                        request.META.get('HTTP_USER_AGENT')
                    ),
                    user_ip=request.META.get('HTTP_X_REAL_IP'),
                )
            except ObjectDoesNotExist:
                if settings.PROJECT_CONF['SIGNUP']:
                    # Get user's organizations from Auth0
                    user_profile = service._get_user_profile(
                        service.tokens['access_token']
                    )
                    organizations = (
                        service.get_user_organizations(user_profile)
                    )
                    # Check if any organization matches existing account
                    existing_account = None
                    if organizations:
                        org_ids = [
                            org.get('id')
                            for org in organizations
                            if org.get('id')
                        ]
                        if org_ids:
                            existing_account = Account.objects.filter(
                                external_id__in=org_ids,
                                is_deleted=False
                            ).first()
                    if existing_account:
                        # Join existing account
                        user, token = self.join_existing_account(
                            account=existing_account,
                            **user_data,
                        )
                        capture_sentry_message(
                            message='Auth0 user joined existing account',
                            data={
                                'user_email': user_data['email'],
                                'account_id': existing_account.id,
                                'external_id': existing_account.external_id,
                                'organizations': organizations
                            },
                            level=SentryLogLevel.INFO
                        )
                    else:
                        # Create new account
                        user, token = self.signup(
                            **user_data,
                            utm_source=slz.validated_data.get('utm_source'),
                            utm_medium=slz.validated_data.get('utm_medium'),
                            utm_term=slz.validated_data.get('utm_term'),
                            utm_content=slz.validated_data.get('utm_content'),
                            gclid=slz.validated_data.get('gclid'),
                            utm_campaign=slz.validated_data.get('utm_campaign')
                        )
                        # Set external_id for the first organization
                        if organizations:
                            first_org_id = organizations[0].get('id')
                            if first_org_id:
                                user.account.external_id = first_org_id
                                user.account.save(
                                    update_fields=['external_id']
                                )
                        capture_sentry_message(
                            message='Auth0 user created new account',
                            data={
                                'user_email': user_data['email'],
                                'account_id': user.account.id,
                                'external_id': user.account.external_id,
                                'organizations': organizations
                            },
                            level=SentryLogLevel.INFO
                        )
                else:
                    raise AuthenticationFailed(MSG_AU_0003)
            service.save_tokens_for_user(user)
            update_auth0_contacts.delay(user.id)
            return self.response_ok({'token': token})

    @action(methods=('GET',), detail=False, url_path='auth-uri')
    def auth_uri(self, request, *args, **kwargs):
        try:
            service = Auth0Service()
            auth_uri = service.get_auth_uri()
        except AuthException as ex:
            raise_validation_error(message=ex.message)
        else:
            return self.response_ok({
                'auth_uri': auth_uri
            })

    @action(methods=('GET',), detail=False)
    def logout(self, *args, **kwargs):
        capture_sentry_message(
            message='Auth0 logout request',
            data=self.request.GET,
            level=SentryLogLevel.INFO
        )
        return self.response_ok()
