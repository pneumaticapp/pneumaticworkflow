import json
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple, Union

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.exceptions import AuthenticationFailed

from src.analysis.services import AnalyticService
from src.authentication.entities import UserData, SSOConfigData
from src.authentication.enums import (
    AuthTokenType,
    SSOProvider,
)
from src.authentication.messages import (
    MSG_AU_0015,
    MSG_AU_0017,
    MSG_AU_0020,
)
from src.authentication.models import (
    Account,
)
from src.authentication.services.user_auth import AuthService
from src.authentication.tokens import PneumaticToken
from src.authentication.views.mixins import SignUpMixin
from src.generics.mixins.services import CacheMixin, EncryptionMixin

UserModel = get_user_model()


class BaseSSOService(SignUpMixin, CacheMixin, EncryptionMixin, ABC):
    """
    Abstract base class for Single Sign-On (SSO) authentication services.

    This class provides a unified interface for integrating various
    SSO providers (Auth0, Okta) into the application. It handles the
    common OAuth 2.0/OpenID Connect flow patterns while allowing
    provider-specific implementations through abstract methods.

    Common Methods:
    - _get_config: Retrieves SSO configuration (domain-specific or default)
    - _serialize_value/_deserialize_value: Secure data serialization for cache
    - _complete_authentication: Handles user lookup/creation and token

    Abstract Methods (must be implemented in subclasses):
    - _get_domain_config: Provider-specific domain configuration retrieval
    - _get_default_config: Provider default configuration from settings
    - _get_first_access_token: OAuth token exchange implementation
    - _get_user_profile: User profile retrieval from provider API
    - get_auth_uri: Authorization URL generation with provider parameters
    - get_user_data: Standardized user data extraction from provider profile
    - save_tokens_for_user: Provider-specific token storage
    - authenticate_user: Complete authentication flow orchestration

    Usage Example:
        service = Auth0Service(domain='company.com')
        auth_url = service.get_auth_uri()
        # ... redirect user to auth_url ...
        user, token = service.authenticate_user(code, state)
    """

    cache_key_prefix = 'sso'
    cache_timeout = 600  # 10 min
    sso_provider: SSOProvider = None
    source = None
    exception_class = None

    def __init__(self, domain: Optional[str] = None):
        """
        Initialize SSO service.

        Args:
            domain: Domain for SSO configuration (optional)
        """
        self.config = self._get_config(domain)
        self.tokens: Optional[Dict] = None

    def _get_config(self, domain: Optional[str] = None) -> SSOConfigData:
        """
        Gets SSO configuration for specified domain or uses default settings.

        Only one SSO provider can be used for the product at a time,
        but different keys can be connected to one SSO provider
        for different accounts.

        Args:
            domain: Domain to search for SSO configuration

        Returns:
            SSOConfigData: Configuration for SSO provider

        Raises:
            SSOServiceException: If SSO is disabled or provider doesn't match
        """
        if not settings.PROJECT_CONF['SSO_AUTH']:
            raise self.exception_class(MSG_AU_0017)

        sso_provider = settings.PROJECT_CONF.get('SSO_PROVIDER', '')
        if sso_provider and sso_provider != self.sso_provider:
            raise self.exception_class(MSG_AU_0015)

        if domain:
            return self._get_domain_config(domain)
        return self._get_default_config()

    @abstractmethod
    def _get_domain_config(self, domain: str) -> SSOConfigData:
        """
        Gets SSO configuration for a specific domain from the database.

        This method retrieves domain-specific SSO configuration that allows
        different organizations to use their own SSO provider settings
        while using the same application instance. Each domain can have
        its own client credentials and provider-specific settings.

        Args:
            domain: The domain name to search for in SSOConfig model.
                   This should match the domain field in the database.

        Returns:
            SSOConfigData: Configuration object containing client_id,
                          client_secret, domain, and redirect_uri for
                          the specified domain.

        Raises:
            SSOServiceException: When no active SSO configuration is found
                                for the specified domain, or when the
                                configuration is invalid.
        """
        pass

    @abstractmethod
    def _get_default_config(self) -> SSOConfigData:
        """
        Gets default SSO configuration from Django settings.

        This method retrieves the fallback SSO configuration that is used
        when no domain-specific configuration is provided or found. The
        configuration is loaded from Django settings and typically used
        for single-tenant deployments.

        Returns:
            SSOConfigData: Default configuration object containing client_id,
                          client_secret, domain, and redirect_uri loaded
                          from Django settings (e.g., AUTH0_CLIENT_ID,
                          OKTA_CLIENT_SECRET, etc.).

        Raises:
            SSOServiceException: When required settings are missing or
                                invalid (e.g., missing client_secret),
                                or when the SSO provider is not properly
                                configured in Django settings.
        """
        pass

    def _serialize_value(self, value: Union[str, dict]) -> str:
        """
        Serializes value for cache storage.

        Args:
            value: Value to serialize

        Returns:
            str: JSON string
        """
        return json.dumps(value, ensure_ascii=False)

    def _deserialize_value(
        self,
        value: Optional[str],
    ) -> Union[str, dict, None]:
        """
        Deserializes value from cache.

        Args:
            value: JSON string to deserialize

        Returns:
            Union[str, dict, None]: Deserialized value
        """
        return json.loads(value) if value else None

    @abstractmethod
    def _get_first_access_token(self, code: str, state: str) -> str:
        """
        Gets access token during initial authorization.

        Args:
            code: Authorization code from SSO provider
            state: State for CSRF verification

        Returns:
            str: Access token
        """
        pass

    @abstractmethod
    def _get_user_profile(self, access_token: str) -> dict:
        """
        Gets user profile through SSO provider API.

        Args:
            access_token: Access token

        Returns:
            dict: User profile
        """
        pass

    @abstractmethod
    def get_auth_uri(self) -> str:
        """
        Generates URI for user authorization.

        Returns:
            str: URI for redirecting to SSO provider
        """
        pass

    @abstractmethod
    def get_user_data(self, user_profile: dict) -> UserData:
        """
        Extracts user data from SSO provider profile.

        Args:
            user_profile: User profile from SSO provider

        Returns:
            UserData: Standardized user data
        """
        pass

    @abstractmethod
    def save_tokens_for_user(self, user: UserModel):
        """
        Saves SSO tokens for user.

        Args:
            user: User to save tokens for
        """
        pass

    @abstractmethod
    def authenticate_user(
        self,
        code: str,
        state: str,
        user_agent: Optional[str] = None,
        user_ip: Optional[str] = None,
        **kwargs,
    ) -> Tuple[UserModel, PneumaticToken]:
        """
        Performs complete user authentication through SSO.

        Args:
            code: Authorization code
            state: State for CSRF verification
            user_agent: Browser User-Agent
            user_ip: User IP address
            **kwargs: Additional parameters

        Returns:
            Tuple[UserModel, PneumaticToken]: User and token
        """
        pass

    def _complete_authentication(
        self,
        user_data: UserData,
        user_agent: Optional[str],
        user_ip: Optional[str],
    ) -> Tuple[UserModel, PneumaticToken]:
        try:
            user = UserModel.objects.active().get(email=user_data['email'])
        except UserModel.DoesNotExist as exc:
            # Fallback: try to find account by first available
            # This is temporary solution as discussed
            existing_account = Account.objects.first()
            if not existing_account:
                raise AuthenticationFailed(MSG_AU_0020) from exc
            user, token = self.join_existing_account(
                account=existing_account,
                **user_data,
            )
        else:
            token = AuthService.get_auth_token(
                user=user,
                user_agent=user_agent,
                user_ip=user_ip,
            )

        self.save_tokens_for_user(user)

        AnalyticService.users_logged_in(
            user=user,
            is_superuser=False,
            auth_type=AuthTokenType.USER,
            source=self.source,
        )
        return user, token
