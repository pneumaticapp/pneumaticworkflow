import pytest
from pneumatic_backend.processes.enums import (
    SysTemplateType,
    PerformerType,
    FieldType,
)
from pneumatic_backend.authentication.enums import AuthTokenType
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_account,
    create_test_template,
)
from pneumatic_backend.processes.models import (
    SystemTemplate,
    SystemWorkflowKickoffData,
    FieldTemplate
)
from pneumatic_backend.processes.api_v2.services.system_workflows import (
    SystemWorkflowService
)
from pneumatic_backend.processes.api_v2.services import WorkflowService
from pneumatic_backend.processes.api_v2.services.exceptions import (
    WorkflowServiceException
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)


pytestmark = pytest.mark.django_db


def test_get_system_workflow_kickoff_data():

    # arrange
    user = create_test_user()
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

    kickoff_data = SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ACCOUNT_OWNER,
        order=1,
        kickoff_data={
            "name": "Some workflow for owner",
        }
    )

    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ADMIN,
        order=1,
        kickoff_data={
            "name": "Some workflow for admin",
        }
    )

    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_NON_ADMIN,
        order=1,
        kickoff_data={
            "name": "Some workflow for non admin",
        }
    )
    service = SystemWorkflowService(user=user)

    # act
    qst = service._get_system_workflow_kickoff_data(system_template)

    # assert
    data = list(qst)
    assert len(data) == 1
    assert data[0] == kickoff_data.kickoff_data


def test_get_system_workflow_kickoff_data__account_owner__ok():

    # arrange
    user = create_test_user(is_account_owner=True)
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

    kickoff_data = SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ACCOUNT_OWNER,
        order=1,
        kickoff_data={
            "name": "Some workflow for owner",
        }
    )

    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ADMIN,
        order=1,
        kickoff_data={
            "name": "Some workflow for admin",
        }
    )

    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_NON_ADMIN,
        order=1,
        kickoff_data={
            "name": "Some workflow for non admin",
        }
    )
    service = SystemWorkflowService(user=user)

    # act
    qst = service._get_system_workflow_kickoff_data(system_template)

    # assert
    data = list(qst)
    assert len(data) == 1
    assert data[0] == kickoff_data.kickoff_data


def test_get_system_workflow_kickoff_data__admin__ok():

    # arrange
    user = create_test_user(
        is_account_owner=False,
        is_admin=True
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

    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ACCOUNT_OWNER,
        order=1,
        kickoff_data={
            "name": "Some workflow for owner",
        }
    )

    kickoff_data = SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ADMIN,
        order=1,
        kickoff_data={
            "name": "Some workflow for admin",
        }
    )

    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_NON_ADMIN,
        order=1,
        kickoff_data={
            "name": "Some workflow for non admin",
        }
    )
    service = SystemWorkflowService(user=user)

    # act
    qst = service._get_system_workflow_kickoff_data(system_template)

    # assert
    data = list(qst)
    assert len(data) == 1
    assert data[0] == kickoff_data.kickoff_data


def test_get_system_workflow_kickoff_data__not_admin__ok():

    # arrange
    user = create_test_user(
        is_account_owner=False,
        is_admin=False
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

    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ACCOUNT_OWNER,
        order=1,
        kickoff_data={
            "name": "Some workflow for owner",
        }
    )

    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ADMIN,
        order=1,
        kickoff_data={
            "name": "Some workflow for admin",
        }
    )

    kickoff_data = SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_NON_ADMIN,
        order=1,
        kickoff_data={
            "name": "Some workflow for non admin",
        }
    )
    service = SystemWorkflowService(user=user)

    # act
    qst = service._get_system_workflow_kickoff_data(system_template)

    # assert
    data = list(qst)
    assert len(data) == 1
    assert data[0] == kickoff_data.kickoff_data


def get_kickoff_fields_values__user_field__set_current_user():

    # arrange
    account = create_test_account()
    account_owner = create_test_user(account=account)
    user = create_test_user(account=account, email='t@t.t')
    template = create_test_template(user=user, tasks_count=1)
    api_name = 'performer'
    FieldTemplate.objects.create(
        name='Performer',
        type=FieldType.USER,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=api_name
    )
    fields_data = {
        api_name: account_owner.id
    }
    service = SystemWorkflowService(user=user)

    # act
    result = service.get_kickoff_fields_values(
        template=template,
        fields_data=fields_data
    )

    # assert
    assert result[api_name] == user.id


def get_kickoff_fields_values__existent_field_value__ok():

    # arrange
    account = create_test_account()
    user = create_test_user(account=account, email='t@t.t')
    template = create_test_template(user=user, tasks_count=1)
    api_name = 'performer'
    FieldTemplate.objects.create(
        name='Performer',
        type=FieldType.TEXT,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=api_name
    )
    text = 'some text'
    service = SystemWorkflowService(user=user)

    # act
    result = service.get_kickoff_fields_values(
        template=template,
        fields_data={
            api_name: text
        }
    )

    # assert
    assert result[api_name] == text


def get_kickoff_fields_values__default_field_value__ok():

    # arrange
    account = create_test_account()
    user = create_test_user(account=account, email='t@t.t')
    template = create_test_template(user=user, tasks_count=1)
    api_name = 'performer'
    FieldTemplate.objects.create(
        name='Performer',
        type=FieldType.TEXT,
        is_required=True,
        kickoff=template.kickoff_instance,
        template=template,
        api_name=api_name,
        default='some {{user_first_name}} text'
    )
    service = SystemWorkflowService(user=user)

    # act
    result = service.get_kickoff_fields_values(
        template=template
    )

    # assert
    assert result[api_name] == f'some {user.first_name} text'


def test_create_onboarding_workflows__ok(mocker):

    # arrange
    user = create_test_user(is_account_owner=True)
    template_mock = mocker.Mock()
    get_onboarding_templates_for_user_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService._get_onboarding_templates_for_user',
        return_value=[template_mock]
    )
    kickoff_fields_data_mock = mocker.Mock()
    get_kickoff_fields_values_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.get_kickoff_fields_values',
        return_value=kickoff_fields_data_mock
    )
    wf_service_init_mock = mocker.patch.object(
        WorkflowService,
        attribute='__init__',
        return_value=None
    )
    workflow_mock = mocker.Mock()
    wf_service_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowService.create',
        return_value=workflow_mock
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    start_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_workflow'
    )
    service = SystemWorkflowService(user=user)

    # act
    service.create_onboarding_workflows()

    # assert
    get_onboarding_templates_for_user_mock.assert_called_once()
    get_kickoff_fields_values_mock.assert_called_once_with(template_mock)
    wf_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    wf_service_create_mock.assert_called_once_with(
        instance_template=template_mock,
        kickoff_fields_data=kickoff_fields_data_mock,
        workflow_starter=user,
        redefined_performer=user,
    )
    workflow_action_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    start_workflow_mock.assert_called_once_with(workflow_mock)


def test_create_activated_workflows__ok(mocker):

    # arrange
    user = create_test_user(is_account_owner=True)
    system_template = SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'Some template',
            "kickoff": {},
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    "description": "",
                    "api_name": 'task-1',
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
    kickoff_fields_data = {'some-api-name-1': 'some value 1'}
    workflow_name = "Some workflow name"
    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ACCOUNT_OWNER,
        order=1,
        kickoff_data={
            'name': workflow_name,
            'is_urgent': True,
            'kickoff': kickoff_fields_data
        }
    )
    fields_data = {'some-api-name-2': 'some value 2'}
    get_kickoff_fields_values_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.get_kickoff_fields_values',
        return_value=fields_data
    )

    template = create_test_template(user=user, tasks_count=1)
    template.system_template_id = system_template.id
    template.save(update_fields=['system_template_id'])
    wf_service_init_mock = mocker.patch.object(
        WorkflowService,
        attribute='__init__',
        return_value=None
    )
    workflow_mock = mocker.Mock()
    wf_service_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowService.create',
        return_value=workflow_mock
    )
    workflow_action_service_init_mock = mocker.patch.object(
        WorkflowActionService,
        attribute='__init__',
        return_value=None
    )
    start_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_workflow'
    )
    service = SystemWorkflowService(user=user)

    # act
    service.create_activated_workflows()

    # assert
    get_kickoff_fields_values_mock.assert_called_once_with(
        template=template,
        fields_data=kickoff_fields_data
    )
    wf_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    wf_service_create_mock.assert_called_once_with(
        instance_template=template,
        kickoff_fields_data=fields_data,
        workflow_starter=user,
        user_provided_name=workflow_name,
        is_urgent=True,
    )
    workflow_action_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    start_workflow_mock.assert_called_once_with(workflow_mock)


def test_create_activated_workflows__template_not_found__logging_ex(mocker):

    # arrange
    user = create_test_user(is_account_owner=True)
    system_template = SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'Some template',
            "kickoff": {},
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    "description": "",
                    "api_name": 'task-1',
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
    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ACCOUNT_OWNER,
        order=1,
        kickoff_data={
            'name': 'Workflow',
            'is_urgent': True,
            'kickoff': {}
        }
    )
    resolve_exception_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService._resolve_exception',
    )
    wf_service_init_mock = mocker.patch.object(
        WorkflowService,
        attribute='__init__',
        return_value=None
    )
    wf_service_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowService.create'
    )
    start_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_workflow'
    )
    service = SystemWorkflowService(user=user)

    # act
    service.create_activated_workflows()

    # assert
    wf_service_init_mock.assert_not_called()
    wf_service_create_mock.assert_not_called()
    start_workflow_mock.assert_not_called()
    resolve_exception_mock.assert_called_once()


def test_create_activated_workflows__not_sys_kickoff_data__skip(mocker):

    # arrange
    user = create_test_user(is_account_owner=True)
    SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'Some template',
            "kickoff": {},
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    "description": "",
                    "api_name": 'task-1',
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
    resolve_exception_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService._resolve_exception',
    )
    wf_service_init_mock = mocker.patch.object(
        WorkflowService,
        attribute='__init__',
        return_value=None
    )
    wf_service_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowService.create'
    )
    start_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_workflow'
    )
    service = SystemWorkflowService(user=user)

    # act
    service.create_activated_workflows()

    # assert
    wf_service_init_mock.assert_not_called()
    wf_service_create_mock.assert_not_called()
    start_workflow_mock.assert_not_called()
    resolve_exception_mock.assert_not_called()


def test_create_activated_workflows__service_exception__not_create(mocker):

    # arrange
    user = create_test_user(is_account_owner=True)
    system_template = SystemTemplate.objects.create(
        name='One of Task',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'Some template',
            "kickoff": {},
            "tasks": [
                {
                    "name": "Task 1",
                    "number": 1,
                    "description": "",
                    "api_name": 'task-1',
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
    kickoff_fields_data = {'some-api-name-1': 'some value 1'}
    workflow_name = "Some workflow name"
    SystemWorkflowKickoffData.objects.create(
        is_active=True,
        name='test',
        system_template=system_template,
        user_role=SysTemplateType.ONBOARDING_ACCOUNT_OWNER,
        order=1,
        kickoff_data={
            'name': workflow_name,
            'kickoff': kickoff_fields_data
        }
    )
    fields_data = {'some-api-name-2': 'some value 2'}
    get_kickoff_fields_values_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService.get_kickoff_fields_values',
        return_value=fields_data
    )

    template = create_test_template(user=user, tasks_count=1)
    template.system_template_id = system_template.id
    template.save(update_fields=['system_template_id'])
    wf_service_init_mock = mocker.patch.object(
        WorkflowService,
        attribute='__init__',
        return_value=None
    )
    exception = WorkflowServiceException('Some ex')
    wf_service_create_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.WorkflowService.create',
        side_effect=exception
    )
    start_workflow_mock = mocker.patch(
        'pneumatic_backend.processes.services.workflow_action.'
        'WorkflowActionService.start_workflow'
    )
    resolve_exception_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService._resolve_exception',
    )
    service = SystemWorkflowService(user=user)

    # act
    service.create_activated_workflows()

    # assert
    get_kickoff_fields_values_mock.assert_called_once_with(
        template=template,
        fields_data=kickoff_fields_data
    )
    wf_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER
    )
    wf_service_create_mock.assert_called_once_with(
        instance_template=template,
        is_urgent=None,
        kickoff_fields_data=fields_data,
        workflow_starter=user,
        user_provided_name=workflow_name,
    )
    start_workflow_mock.assert_not_called()
    resolve_exception_mock.assert_called_once_with(
        ex=exception,
        system_template_id=system_template.id,
        system_template_name=system_template.name,
    )


def test_create_library_templates__ok(mocker):

    # arrange
    user = create_test_user()
    activated = SystemTemplate.objects.create(
        name='Activated',
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
    onboarding = SystemTemplate.objects.create(
        name='Onboarding',
        type=SysTemplateType.ONBOARDING_ADMIN,
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
    inactive = SystemTemplate.objects.create(
        name='Inactive library',
        type=SysTemplateType.LIBRARY,
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
        is_active=False
    )
    system_template = SystemTemplate.objects.create(
        name='Active library',
        type=SysTemplateType.LIBRARY,
        template={
            "name": 'Active template',
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
    user.account.system_templates.add(
        system_template,
        inactive,
        activated,
        onboarding
    )

    create_template_from_sys_template_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'TemplateService.create_template_from_sys_template'
    )
    resolve_exception_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService._resolve_exception'
    )
    service = SystemWorkflowService(user=user)

    # act
    service.create_library_templates()

    # assert
    create_template_from_sys_template_mock.assert_called_once_with(
        system_template=system_template
    )
    resolve_exception_mock.assert_not_called()


def test_create_library_templates__exception__resolve(mocker):

    # arrange
    user = create_test_user()
    system_template = SystemTemplate.objects.create(
        name='Active library',
        type=SysTemplateType.LIBRARY,
        template={
            "name": 'Active template',
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
    user.account.system_templates.add(system_template)
    ex = Exception('some bad situation')
    create_template_from_sys_template_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'TemplateService.create_template_from_sys_template',
        side_effect=ex
    )
    resolve_exception_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService._resolve_exception'
    )
    service = SystemWorkflowService(user=user)

    # act
    service.create_library_templates()

    # assert
    create_template_from_sys_template_mock.assert_called_once_with(
        system_template=system_template
    )
    resolve_exception_mock.assert_called_once_with(ex)


def test_create_activated_templates__ok(mocker):

    # arrange
    user = create_test_user()
    inactive = SystemTemplate.objects.create(
        name='Activated',
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
        is_active=False
    )
    system_template = SystemTemplate.objects.create(
        name='Activated',
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
    onboarding = SystemTemplate.objects.create(
        name='Onboarding',
        type=SysTemplateType.ONBOARDING_ADMIN,
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
    library = SystemTemplate.objects.create(
        name='Active library',
        type=SysTemplateType.LIBRARY,
        template={
            "name": 'Active template',
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
    user.account.system_templates.add(
        system_template,
        inactive,
        library,
        onboarding
    )

    create_template_from_sys_template_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'TemplateService.create_template_from_sys_template'
    )
    resolve_exception_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService._resolve_exception'
    )
    service = SystemWorkflowService(user=user)

    # act
    service.create_activated_templates()

    # assert
    create_template_from_sys_template_mock.assert_called_once_with(
        system_template=system_template
    )
    resolve_exception_mock.assert_not_called()


def test_create_create_activated_templates__exception__resolve(mocker):

    # arrange
    user = create_test_user()
    system_template = SystemTemplate.objects.create(
        name='Activated',
        type=SysTemplateType.ACTIVATED,
        template={
            "name": 'Active template',
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
    user.account.system_templates.add(system_template)
    ex = Exception('some bad situation')
    create_template_from_sys_template_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.templates.template.'
        'TemplateService.create_template_from_sys_template',
        side_effect=ex
    )
    resolve_exception_mock = mocker.patch(
        'pneumatic_backend.processes.api_v2.services.system_workflows.'
        'SystemWorkflowService._resolve_exception'
    )
    service = SystemWorkflowService(user=user)

    # act
    service.create_activated_templates()

    # assert
    create_template_from_sys_template_mock.assert_called_once_with(
        system_template=system_template
    )
    resolve_exception_mock.assert_called_once_with(ex)
