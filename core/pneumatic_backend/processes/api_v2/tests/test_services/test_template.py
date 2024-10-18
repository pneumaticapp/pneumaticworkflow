import pytest
from copy import deepcopy
from django.contrib.auth import get_user_model
from rest_framework.serializers import ValidationError
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_template,
)
from pneumatic_backend.processes.api_v2.serializers.template.template import (
    TemplateSerializer
)
from pneumatic_backend.processes.api_v2.services.templates.template import (
    TemplateService
)
from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.enums import (
    SysTemplateType,
    PerformerType,
    TemplateType,
)
from pneumatic_backend.processes.models import (
    Template,
    SystemTemplate,
    SystemTemplateCategory,
)
from pneumatic_backend.authentication.enums import AuthTokenType


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_create_template_by_steps__ok(mocker):

    # arrange
    user = create_test_user()
    service = TemplateService(user=user)
    name = 'Template name'
    tasks = [
        {
            'number': 1,
            'name': 'Step 1',
            'description': 'description 1',
        },
        {
            'number': 2,
            'name': 'Step 2',
            'description': 'description 2',
        }
    ]
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'template_generated_from_landing'
    )

    # act
    template = service.create_template_by_steps(
        name=name,
        tasks=tasks
    )

    # assert
    assert template.name == name
    assert template.is_active is True
    assert template.template_owners.filter(id=user.id).exists()
    assert template.tasks.count() == 2
    task = template.tasks.order_by('number').first()
    assert task.name == 'Step 1'
    assert task.description == 'description 1'
    analytics_mock.assert_called_once_with(
        template=template,
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )


def test_create_template_by_steps__validation_error__ok(mocker):

    # arrange
    user = create_test_user()
    service = TemplateService(user=user)
    name = 'Template name'
    tasks = [
        {
            'number': 1,
            'name': 'Step 1',
            'description': 'description 1',
        },
        {
            'number': 1,
            'name': 'Step 2',
            'description': 'description 2',
        }
    ]
    filled_data = {
        'name': name,
        'tasks': tasks
    }
    fill_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'TemplateService.fill_template_data',
        return_value=filled_data
    )
    logging_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'capture_sentry_message'
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'template_generated_from_landing'
    )

    # act
    with pytest.raises(ValidationError):
        service.create_template_by_steps(
            name=name,
            tasks=tasks
        )

    # assert
    assert not Template.objects.filter(name=name).exists()
    fill_template_data_mock.assert_called_once_with(
        initial_data={
            'name': name,
            'is_active': True,
            'tasks': tasks
        }
    )
    logging_mock.assert_called_once()
    analytics_mock.assert_not_called()


def test_get_from_sys_template__ok(mocker):

    # arrange
    user = create_test_user()
    is_superuser = True
    auth_type = AuthTokenType.API
    service = TemplateService(
        user=user,
        is_superuser=is_superuser,
        auth_type=auth_type
    )
    name = 'Template name'
    category = SystemTemplateCategory.objects.create(
        name='Sales',
        order=1,
    )
    sys_template = SystemTemplate.objects.create(
        name=name,
        type=SysTemplateType.LIBRARY,
        template={},
        category=category,
        is_active=True
    )
    data_mock = mocker.Mock()
    fill_template_data_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'TemplateService.fill_template_data',
        return_value=data_mock
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'library_template_opened'
    )

    # act
    result = service.get_from_sys_template(sys_template)

    # assert
    assert result is data_mock
    fill_template_data_mock.assert_called_once_with(
        initial_data=sys_template.template
    )
    analytics_mock.assert_called_once_with(
        user=user,
        sys_template=sys_template,
        auth_type=auth_type,
        is_superuser=is_superuser
    )


def test_create_template_from_sys_template__ok(
    mocker,
    api_client
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    account_owner = create_test_user(
        account=account,
        is_account_owner=True
    )
    user = create_test_user(
        account=account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    name = (
        '{{ user_first_name }} {{ user_last_name }} template '
        '{{ account_name }} {{ user_email }}'
    )
    task_api_name = 'some-api-name'
    system_template = SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": name,
            "kickoff": {
                "fields": [
                    {
                        "name": "Performer",
                        "type": "user",
                        "order": 1,
                        "api_name": "performer",
                        "is_required": True
                    },
                ]
            },
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    "description": "",
                    "api_name": task_api_name,
                    'raw_performers': [
                        {
                            'type': PerformerType.FIELD,
                            'source_id': 'performer'
                        }
                    ]
                }
            ]
        },
        is_active=True
    )
    template = create_test_template(user=user, tasks_count=1)
    template_slz_init_mock = mocker.patch.object(
        TemplateSerializer,
        attribute='__init__',
        return_value=None
    )
    template_slz_validate_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.is_valid'
    )
    template_slz_save_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.save',
        return_value=template
    )
    service = TemplateService(user=user)
    template_data = deepcopy(system_template.template)
    template_data['name'] = (
        f'{user.first_name} {user.last_name} template '
        f'{account.name} {user.email}'
    )
    template_data['template_owners'] = [account_owner.id, user.id]
    template_data['is_active'] = True
    template_data['tasks'][0]['api_name'] = task_api_name

    # act
    result = service.create_template_from_sys_template(
        system_template=system_template
    )

    # assert
    template_slz_init_mock.assert_called_once_with(
        data=template_data,
        context={
            'account': account,
            'user': user,
            'auth_type': AuthTokenType.USER,
            'type': TemplateType.CUSTOM,
            'generic_name': None,
            'is_superuser': False,
            'automatically_created': True,
        }
    )
    template_slz_validate_mock.assert_called_once_with(raise_exception=True)
    template_slz_save_mock.assert_called_once()
    assert result.id == template.id
    assert result.system_template_id == system_template.id


def test_create_template_from_sys_template__default_task_performer__ok(
    mocker,
    api_client
):

    # arrange
    account = create_test_account()
    user = create_test_user(
        account=account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    system_template = SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'New template',
            "kickoff": {},
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    "description": "some desc",
                    "api_name": "task-1",
                }
            ]
        },
        is_active=True
    )

    template_slz_init_mock = mocker.patch.object(
        TemplateSerializer,
        attribute='__init__',
        return_value=None
    )
    template_slz_validate_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.is_valid'
    )
    template_slz_save_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.save'
    )
    template_data = deepcopy(system_template.template)
    template_data['template_owners'] = [user.id]
    template_data['tasks'][0]['raw_performers'] = [
        {
            'type': PerformerType.USER,
            'source_id': user.id
        }
    ]
    template_data['is_active'] = True
    service = TemplateService(user=user)

    # act
    service.create_template_from_sys_template(
        system_template=system_template
    )

    # assert
    template_slz_init_mock.assert_called_once_with(
        data=template_data,
        context={
            'account': account,
            'user': user,
            'auth_type': AuthTokenType.USER,
            'type': TemplateType.CUSTOM,
            'generic_name': None,
            'is_superuser': False,
            'automatically_created': True,
        }
    )
    template_slz_validate_mock.assert_called_once_with(raise_exception=True)
    template_slz_save_mock.assert_called_once()


def test_create_template_from_sys_template__create_task_api_name__ok(
    mocker,
    api_client
):
    # arrange
    account = create_test_account()
    user = create_test_user(
        account=account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    system_template = SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'New template',
            "kickoff": {
                "fields": [
                    {
                        "name": "Performer",
                        "type": "user",
                        "order": 3,
                        "api_name": "performer",
                        "is_required": True
                    }
                ]
            },
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    "description": "",
                    "raw_performers": [
                        {
                            'type': PerformerType.FIELD,
                            'source_id': 'performer'
                        }
                    ]
                }
            ]
        },
        is_active=True
    )
    template_data = deepcopy(system_template.template)

    template_slz_init_mock = mocker.patch.object(
        TemplateSerializer,
        attribute='__init__',
        return_value=None
    )
    template_slz_validate_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.is_valid'
    )
    template_slz_save_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.save'
    )
    task_api_name = 'some-api-name'
    create_api_name_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'create_api_name',
        return_value=task_api_name
    )
    template_data['template_owners'] = [user.id]
    template_data['tasks'][0]['api_name'] = task_api_name
    template_data['is_active'] = True
    service = TemplateService(user=user)

    # act
    service.create_template_from_sys_template(
        system_template=system_template
    )

    # assert
    create_api_name_mock.assert_called_once_with(prefix='task')
    template_slz_init_mock.assert_called_once_with(
        data=template_data,
        context={
            'account': account,
            'user': user,
            'auth_type': AuthTokenType.USER,
            'type': TemplateType.CUSTOM,
            'generic_name': None,
            'is_superuser': False,
            'automatically_created': True,
        }
    )
    template_slz_validate_mock.assert_called_once_with(raise_exception=True)
    template_slz_save_mock.assert_called_once()


def test_create_template_from_sys_template__validation_error__save_draft(
    mocker,
    api_client
):
    # arrange
    account = create_test_account()
    user = create_test_user(
        account=account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    system_template = SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'New template',
            "kickoff": {},
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    'api_name': 'task-1',
                    "raw_performers": [
                        {
                            'type': PerformerType.FIELD,
                            'source_id': 'performer'
                        }
                    ]
                }
            ]
        },
        is_active=True
    )
    template_slz_init_mock = mocker.patch.object(
        TemplateSerializer,
        attribute='__init__',
        return_value=None
    )
    template_slz_validate_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.is_valid',
        side_effect=ValidationError()

    )
    template_slz_save_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.save',
    )
    template_mock = mocker.Mock()
    template_slz_save_as_draft_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.save_as_draft',
        return_value=template_mock
    )
    template_data = deepcopy(system_template.template)
    template_data['template_owners'] = [user.id]
    template_data['is_active'] = True

    service = TemplateService(user=user)

    # act
    template = service.create_template_from_sys_template(
        system_template=system_template
    )

    # assert
    template_slz_init_mock.assert_called_once_with(
        data=template_data,
        context={
            'account': account,
            'user': user,
            'auth_type': AuthTokenType.USER,
            'type': TemplateType.CUSTOM,
            'generic_name': None,
            'is_superuser': False,
            'automatically_created': True,
        }
    )
    template_slz_validate_mock.assert_called_once_with(raise_exception=True)
    template_slz_save_mock.assert_not_called()
    template_slz_save_as_draft_mock.assert_called_once()
    assert template is template_mock


def test_create_template_from_sys_template__save_validation_error__save_draft(
    mocker,
    api_client
):
    # arrange
    account = create_test_account()
    user = create_test_user(
        account=account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    system_template = SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'New template',
            "kickoff": {},
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    'api_name': 'task-1',
                    "raw_performers": [
                        {
                            'type': PerformerType.FIELD,
                            'source_id': 'performer'
                        }
                    ]
                }
            ]
        },
        is_active=True
    )
    template_slz_init_mock = mocker.patch.object(
        TemplateSerializer,
        attribute='__init__',
        return_value=None
    )
    template_slz_validate_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.is_valid'
    )
    template_slz_save_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.save',
        side_effect=ValidationError()
    )
    template_mock = mocker.Mock()
    template_slz_save_as_draft_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.save_as_draft',
        return_value=template_mock
    )
    template_data = deepcopy(system_template.template)
    template_data['template_owners'] = [user.id]
    template_data['is_active'] = True

    service = TemplateService(user=user)

    # act
    template = service.create_template_from_sys_template(
        system_template=system_template
    )

    # assert
    template_slz_init_mock.assert_called_once_with(
        data=template_data,
        context={
            'account': account,
            'user': user,
            'auth_type': AuthTokenType.USER,
            'type': TemplateType.CUSTOM,
            'generic_name': None,
            'is_superuser': False,
            'automatically_created': True,
        }
    )
    template_slz_validate_mock.assert_called_once_with(raise_exception=True)
    template_slz_save_mock.assert_called_once()
    template_slz_save_as_draft_mock.assert_called_once()
    assert template is template_mock


def test_create_template_from_sys_template__limit_is_reached__save_draft(
    mocker,
    api_client
):
    # arrange
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    account.active_templates = 1
    account.max_active_templates = 1
    account.save()
    user = create_test_user(
        account=account,
        email='admin@test.test',
        is_account_owner=False,
        is_admin=True,
    )
    system_template = SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'New template',
            "kickoff": {},
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    'api_name': 'task-1',
                    "raw_performers": [
                        {
                            'type': PerformerType.FIELD,
                            'source_id': 'performer'
                        }
                    ]
                }
            ]
        },
        is_active=True
    )
    template_slz_init_mock = mocker.patch.object(
        TemplateSerializer,
        attribute='__init__',
        return_value=None
    )
    template_slz_validate_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.is_valid',
    )
    template_mock = mocker.Mock()
    template_slz_save_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.serializers.template.template.'
        'TemplateSerializer.save',
        return_value=template_mock
    )
    template_data = deepcopy(system_template.template)
    template_data['template_owners'] = [user.id]
    template_data['is_active'] = False

    service = TemplateService(user=user)

    # act
    template = service.create_template_from_sys_template(
        system_template=system_template
    )

    # assert
    template_slz_init_mock.assert_called_once_with(
        data=template_data,
        context={
            'account': account,
            'user': user,
            'auth_type': AuthTokenType.USER,
            'type': TemplateType.CUSTOM,
            'generic_name': None,
            'is_superuser': False,
            'automatically_created': True,
        }
    )
    template_slz_validate_mock.assert_called_once_with(raise_exception=True)
    template_slz_save_mock.assert_called_once()
    assert template is template_mock


def test_create_template_from_library_template__ok(mocker):

    # arrange
    user = create_test_user()
    system_template = SystemTemplate.objects.create(
        name='Library template',
        type=SysTemplateType.LIBRARY,
        is_active=True,
        template={
            "name": 'New template',
            "kickoff": {},
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    'api_name': 'task-1',
                    "raw_performers": [
                        {
                            'type': PerformerType.FIELD,
                            'source_id': 'performer'
                        }
                    ]
                }
            ]
        }
    )
    template_mock = mocker.Mock()
    create_template_from_sys_template_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'TemplateService.create_template_from_sys_template',
        return_value=template_mock
    )
    analytics_mock = mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService.'
        'template_created_from_landing_library'
    )
    auth_type = AuthTokenType.API
    is_superuser = True
    service = TemplateService(
        user=user,
        auth_type=auth_type,
        is_superuser=is_superuser
    )

    # act
    template = service.create_template_from_library_template(
        system_template=system_template
    )

    # assert
    assert template is template_mock
    create_template_from_sys_template_mock.assert_called_once_with(
        system_template=system_template
    )
    analytics_mock.assert_called_once_with(
        user=user,
        template=template_mock,
        auth_type=auth_type,
        is_superuser=is_superuser
    )
