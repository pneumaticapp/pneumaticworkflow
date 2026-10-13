import secrets
from collections.abc import Callable
from datetime import timedelta
from types import SimpleNamespace

import pytest
from celery import Task as CeleryTask
from django.core.cache import caches
from django.utils import timezone
from oauth2_provider.models import AccessToken, Application
from pytest_django.fixtures import SettingsWrapper
from pytest_mock import MockerFixture

from src.authentication.services.consent import ConsentService
from src.authentication.services.delegation import DelegationService
from src.authentication.throttling import (
    OAuthAuthorizeThrottle,
    OAuthRegisterThrottle,
    OAuthTokenThrottle,
)
from src.generics.tests.clients import PneumaticApiClient
from src.generics.throttling import CustomSimpleRateThrottle
from src.mcp.models import (
    AccessBinding,
    AuthorizationRequest,
    ClientPolicy,
    Connection,
)
from src.storage.services.upload_sessions import UploadSessionService
from src.processes.enums import FieldType
from src.processes.models.workflows.fields import TaskField
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_owner,
    create_test_template,
    create_test_workflow,
)


@pytest.fixture(autouse=True)
def mcp_settings(settings: SettingsWrapper, mocker: MockerFixture):
    settings.MCP_ENABLED = True
    settings.MCP_PUBLIC_URL = 'https://pneumatic.test/mcp'
    settings.MCP_ISSUER_URL = 'https://pneumatic.test'
    settings.MCP_SERVICE_SECRET = 'mcp-test-service-secret-32-characters'
    settings.MCP_FILE_SERVICE_SECRET = 'mcp-test-file-secret-32-characters'
    settings.MCP_FILE_SERVICE_URL = 'http://file-service:8000'
    settings.PROJECT_CONF = {**settings.PROJECT_CONF, 'ANALYTICS': False}
    settings.ANALYTICS_WRITE_KEY = ''
    settings.CACHES = {
        **settings.CACHES,
        'default': {
            **settings.CACHES['default'],
            'KEY_PREFIX': 'review_mcp_' + secrets.token_hex(16),
        },
    }
    rates = {
        **settings.REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'],
        OAuthRegisterThrottle.scope: None,
        OAuthAuthorizeThrottle.scope: None,
        OAuthTokenThrottle.scope: None,
    }
    mocker.patch.object(CustomSimpleRateThrottle, 'THROTTLE_RATES', rates)
    settings.OAUTH2_PROVIDER = {
        **settings.OAUTH2_PROVIDER,
        'OIDC_ISS_ENDPOINT': settings.MCP_ISSUER_URL,
    }
    return settings


@pytest.fixture
def authorization_request(
    grant: SimpleNamespace,
) -> AuthorizationRequest:
    return AuthorizationRequest.objects.create(
        parameters={
            'client_id': grant.app.client_id,
            'scope': ' '.join(grant.connection.scopes),
        },
        expires_at=timezone.now() + timedelta(minutes=10),
    )


@pytest.fixture
def oauth_rate(
    mcp_settings: SettingsWrapper,
    mocker: MockerFixture,
) -> SimpleNamespace:
    backend = caches['default']
    ip = '192.0.2.31'
    throttles = {
        'register': OAuthRegisterThrottle,
        'authorize': OAuthAuthorizeThrottle,
        'token': OAuthTokenThrottle,
    }
    rates = CustomSimpleRateThrottle.THROTTLE_RATES
    for throttle in throttles.values():
        rates[throttle.scope] = '1/min'
    timer = mocker.patch.object(
        CustomSimpleRateThrottle,
        'timer',
        return_value=1000,
    )
    return SimpleNamespace(
        backend=backend,
        ip=ip,
        timer=timer,
        rates=rates,
        keys={
            budget: throttle.cache_format
            % {
                'scope': throttle.scope,
                'ident': ip,
            }
            for budget, throttle in throttles.items()
        },
    )


@pytest.fixture
def authorization_parameters(
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
) -> dict:
    return {
        'client_id': grant.app.client_id,
        'redirect_uri': 'https://client.test/callback',
        'response_type': 'code',
        'scope': 'pneumatic:read',
        'state': 'rate-review',
        'code_challenge': 'A' * 43,
        'code_challenge_method': 'S256',
        'resource': mcp_settings.MCP_PUBLIC_URL,
    }


@pytest.fixture
def login_code(
    authorization_request: AuthorizationRequest,
    grant: SimpleNamespace,
) -> dict:
    issued = ConsentService.create_login_code(
        request_id=authorization_request.pk,
        user=grant.user,
    )
    return {
        'code': issued.code,
        'request_id': str(issued.request_id),
    }


@pytest.fixture(autouse=True)
def external_effects(
    mocker: MockerFixture,
    mcp_settings: SettingsWrapper,
    django_capture_on_commit_callbacks,
):
    """Keep normal on-commit scheduling real; intercept only broker sends."""
    analytics_track_mock = mocker.patch(
        target='src.analysis.services.analytics.track',
    )
    broker = mocker.patch.object(
        target=CeleryTask,
        attribute='apply_async',
        autospec=True,
    )
    with django_capture_on_commit_callbacks(execute=True):
        yield SimpleNamespace(broker=broker)
    analytics_track_mock.assert_not_called()


@pytest.fixture
def api_client() -> PneumaticApiClient:
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture
def grant(mcp_settings: SettingsWrapper) -> SimpleNamespace:
    account = create_test_account()
    user = create_test_owner(account=account)
    app = Application.objects.create(
        name='Test MCP client',
        client_type=Application.CLIENT_PUBLIC,
        authorization_grant_type=Application.GRANT_AUTHORIZATION_CODE,
        redirect_uris='https://client.test/callback',
    )
    ClientPolicy.objects.create(application=app)
    scopes = [
        'pneumatic:read',
        'pneumatic:write',
        'files:read',
        'files:write',
    ]
    connection = Connection.objects.create(
        application=app,
        user=user,
        account=account,
        scopes=scopes,
        resource=mcp_settings.MCP_PUBLIC_URL,
    )
    token = secrets.token_urlsafe(32)
    access = AccessToken.objects.create(
        application=app,
        user=user,
        token=token,
        scope=' '.join(scopes),
        resource=[mcp_settings.MCP_PUBLIC_URL],
        expires=timezone.now() + timedelta(minutes=15),
    )
    AccessBinding.objects.create(access_token=access, connection=connection)
    return SimpleNamespace(
        account=account,
        user=user,
        app=app,
        connection=connection,
        token=token,
        access=access,
    )


@pytest.fixture
def delegated_client(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    mcp_settings: SettingsWrapper,
) -> Callable:
    def get_client(
        *,
        tool: str,
        method: str,
        path: str,
        scopes: list[str] | None = None,
    ) -> PneumaticApiClient:
        issued = DelegationService.create(
            token=grant.token,
            resource=mcp_settings.MCP_PUBLIC_URL,
            tool=tool,
            method=method,
            path=path,
            scopes=scopes,
        )
        api_client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {issued.credential}',
        )
        return api_client

    return get_client


@pytest.fixture
def task_field(grant: SimpleNamespace) -> TaskField:
    workflow = create_test_workflow(user=grant.user)
    task = workflow.tasks.get(number=1)
    return TaskField.objects.create(
        task=task,
        workflow=workflow,
        account=grant.account,
        api_name='field_file',
        type=FieldType.FILE,
        name='File',
    )


@pytest.fixture
def task_fieldset(grant: SimpleNamespace) -> SimpleNamespace:
    template = create_test_template(user=grant.user)
    fieldset_template = create_test_fieldset_template(
        account=grant.account,
        template=template,
        task=template.tasks.get(number=1),
    )
    fieldset_template.fields.update(type=FieldType.FILE)
    workflow = create_test_workflow(user=grant.user, template=template)
    task = workflow.tasks.get(number=1)
    fieldset = task.fieldsets.get(api_name=fieldset_template.api_name)
    return SimpleNamespace(
        task=task,
        fieldset=fieldset,
        field=fieldset.fields.get(),
    )


@pytest.fixture
def kickoff_fieldset(grant: SimpleNamespace) -> SimpleNamespace:
    template = create_test_template(user=grant.user, is_active=True)
    fieldset = create_test_fieldset_template(
        account=grant.account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    fieldset.fields.update(type=FieldType.FILE)
    return SimpleNamespace(
        template=template,
        fieldset=fieldset,
        field=fieldset.fields.get(),
    )


@pytest.fixture
def fieldset_upload_session(
    grant: SimpleNamespace,
    task_fieldset: SimpleNamespace,
    mcp_settings: SettingsWrapper,
) -> SimpleNamespace:
    authorization = DelegationService.create(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='create_upload_link',
        method='POST',
        path='/integrations/mcp/uploads',
    )
    request = SimpleNamespace(
        user=grant.user,
        auth=DelegationService.get_delegation(
            credential=authorization.credential,
        ),
    )
    created = UploadSessionService.create(
        user=request.user,
        delegation=request.auth,
        data={
            'target_type': 'task',
            'task_id': task_fieldset.task.pk,
            'field_api_name': task_fieldset.field.api_name,
            'filename': 'fieldset.txt',
            'content_type': 'text/plain',
            'size': 3,
        },
    )
    return SimpleNamespace(
        request=request,
        session=created.session,
        credential=created.credential,
    )


@pytest.fixture
def registered_client(api_client: PneumaticApiClient) -> SimpleNamespace:
    metadata = {
        'client_name': 'External MCP',
        'redirect_uris': ['https://client.test/callback'],
        'grant_types': ['authorization_code', 'refresh_token'],
        'response_types': ['code'],
        'token_endpoint_auth_method': 'none',
    }
    registered = api_client.post(
        path='/oauth/mcp/register',
        data=metadata,
        format='json',
    ).json()
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {registered["registration_access_token"]}',
    )
    return SimpleNamespace(
        client=api_client,
        metadata=metadata,
        registered=registered,
        path=f'/oauth/mcp/register/{registered["client_id"]}',
    )


@pytest.fixture
def upload_session(
    grant: SimpleNamespace,
    task_field: TaskField,
    mcp_settings: SettingsWrapper,
) -> SimpleNamespace:
    authorization = DelegationService.create(
        token=grant.token,
        resource=mcp_settings.MCP_PUBLIC_URL,
        tool='create_upload_link',
        method='POST',
        path='/integrations/mcp/uploads',
    )
    request = SimpleNamespace(
        user=grant.user,
        auth=DelegationService.get_delegation(
            credential=authorization.credential,
        ),
    )
    created = UploadSessionService.create(
        user=request.user,
        delegation=request.auth,
        data={
            'target_type': 'task',
            'task_id': task_field.task_id,
            'field_api_name': task_field.api_name,
            'filename': 'test.txt',
            'content_type': 'text/plain',
            'size': 3,
        },
    )
    return SimpleNamespace(
        request=request,
        session=created.session,
        credential=created.credential,
    )
