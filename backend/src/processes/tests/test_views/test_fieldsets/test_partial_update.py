import pytest
from datetime import timedelta

from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import MSG_A_0035, MSG_A_0037, MSG_A_0041
from src.authentication.enums import AuthTokenType
from src.generics.exceptions import BaseServiceException
from src.processes.enums import (
    FieldSetLayout,
    LabelPosition,
    FieldSetRuleType,
    FieldType,
)
from src.processes.models.templates.fieldset import FieldsetTemplateRule
from src.processes.services.templates.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_fieldset_template,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_partial_update__all_fields__ok(api_client, mocker):

    """ Partial update with full request data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    field_api_name = 'f1'
    fieldset_api_name = 'fs1'
    data = {
        'name': 'Full Updated Fieldset',
        'description': 'Updated description',
        'api_name': fieldset_api_name,
        'order': 10,
        'layout': FieldSetLayout.HORIZONTAL,
        'label_position': LabelPosition.LEFT,
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': field_api_name,
            },
        ],
        'rules': [
            {
                'id': 123,
                'type': FieldSetRuleType.SUM_EQUAL,
                'value': '10',
                'api_name': 'r1',
                'fields': [field_api_name],
            },
        ],
    }
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        name=data['name'],
        description=data['description'],
        order=data['order'],
        label_position=data['label_position'],
        layout=data['layout'],
        kickoff=template.kickoff_instance,
        api_name=data['api_name'],
        rule_type=FieldSetRuleType.SUM_EQUAL,
    )
    field = fieldset.fields.first()
    rule = fieldset.rules.first()
    rule.fields.add(field)
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == fieldset.id
    assert response.data['name'] == data['name']
    assert response.data['description'] == data['description']
    assert response.data['order'] == data['order']
    assert response.data['task'] is None
    assert response.data['label_position'] == data['label_position']
    assert response.data['layout'] == data['layout']
    assert response.data['api_name'] == data['api_name']

    assert len(response.data['fields']) == 1
    assert response.data['fields'][0]['name'] == field.name
    assert response.data['fields'][0]['api_name'] == field.api_name

    assert len(response.data['rules']) == 1
    assert response.data['rules'][0]['type'] == rule.type
    assert response.data['rules'][0]['value'] == rule.value
    assert response.data['rules'][0]['api_name'] == rule.api_name
    assert response.data['rules'][0]['fields'] == [field.api_name]
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        name='Full Updated Fieldset',
        api_name=fieldset_api_name,
        description='Updated description',
        order=10,
        layout=FieldSetLayout.HORIZONTAL,
        label_position=LabelPosition.LEFT,
        rules=data['rules'],
        fields=data['fields'],
    )


def test_partial_update__name__ok(api_client, mocker):

    """ Partial update with minimal request data """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'name': 'Updated Name',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == fieldset.id
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        name=data['name'],
    )


def test_partial_update__task_id__ok(api_client, mocker):

    """ Move fieldset from kickoff to task in one PATCH
     (clear kickoff, set task)."""

    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    task = template.tasks.first()
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    data = {
        'task': task.api_name,
    }
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['task'] == task.api_name
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        task_id=task.id,
    )


def test_partial_update__task_is_null_set_kickoff__ok(api_client, mocker):

    """ Move fieldset from kickoff to task in one PATCH
        (clear kickoff, set task). """

    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data={
            'task': None,
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['task'] is None
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        task=None,
    )


def test_partial_update__with_rule_fields__ok(api_client, mocker):

    """
        Partial update with fields in rule request
        and check fields in response
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    field_api_name = 'f1'
    data = {
        'name': 'Updated Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.STRING,
                'order': 1,
                'api_name': field_api_name,
            },
        ],
        'rules': [
            {
                'id': 123,
                'type': FieldSetRuleType.SUM_EQUAL,
                'value': '10',
                'api_name': 'r1',
                'fields': [field_api_name],
            },
        ],
    }

    # mock FieldSetTemplateService
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    # Pre-add the field to the fieldset for the mock response verification
    field = fieldset.fields.first()
    rule = FieldsetTemplateRule.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='val',
        api_name='r1',
    )
    rule.fields.add(field)

    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    assert response.data['id'] == fieldset.id

    assert len(response.data['rules']) == 1
    assert response.data['rules'][0]['api_name'] == 'r1'
    assert response.data['rules'][0]['fields'] == [field.api_name]

    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        name='Updated Fieldset',
        rules=data['rules'],
        fields=data['fields'],
    )


def test_partial_update__clear_fields__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'name': 'Updated Fieldset',
        'rules': [
            {
                'id': 123,
                'type': FieldSetRuleType.SUM_EQUAL,
                'value': '10',
                'api_name': 'r1',
                'fields': [],
            },
        ],
    }

    # mock FieldSetTemplateService
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        name='Updated Fieldset',
        rules=data['rules'],
    )


def test_partial_update__not_existent__validation_error(api_client, mocker):

    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    task = template.tasks.first()
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    data = {
        'task': 'not-exist',
    }
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = 'Object with api_name=not-exist does not exist.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'task'
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__another_account_task__validation_error(
    api_client,
    mocker,
):

    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    task = template.tasks.first()
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
    )
    another_user = create_test_owner(email='another@test.test')
    another_template = create_test_template(user=another_user, tasks_count=1)
    another_account_task = another_template.tasks.get(number=1)
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    data = {
        'task': another_account_task.api_name,
    }
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = (
        f'Object with api_name={another_account_task.api_name} '
        f'does not exist.'
    )
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'task'
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__another_template_task__validation_error(
    api_client,
    mocker,
):

    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    task = template.tasks.first()
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        task=task,
    )
    another_template = create_test_template(user=user, tasks_count=1)
    another_template_task = another_template.tasks.get(number=1)
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    data = {
        'task': another_template_task.api_name,
    }
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = (
        f'Object with api_name={another_template_task.api_name} '
        f'does not exist.'
    )
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'task'
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__unauthenticated__unauthorized(api_client, mocker):

    """ Unauthenticated request returns 401 """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'name': 'Updated Fieldset',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 401
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__expired_sub__permission_denied(api_client, mocker):

    """ Expired subscription returns 403 """

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__billing_plan__permission_denied(api_client, mocker):

    """ Billing plan permission denied returns 403 """

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__users_limit__permission_denied(api_client, mocker):

    """ Users overlimited returns 403 """

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        max_users=1,
    )
    user = create_test_owner(account=account)
    create_test_not_admin(
        account=account,
        email='extra@pneumatic.app',
    )
    account.active_users = 2
    account.save()
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__non_admin__permission_denied(api_client, mocker):

    """ Non-admin non-owner user returns 403 """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    template = create_test_template(
        user=owner,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    user = create_test_not_admin(account=account)
    data = {
        'name': 'Updated Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 403
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__invalid_name__validation_error(api_client, mocker):

    """ Invalid name field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'name': '',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = 'This field may not be blank.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__invalid_layout__validation_error(api_client, mocker):

    """ Invalid layout field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'layout': 'invalid_layout',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = '"invalid_layout" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'layout'
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__invalid_label_position__validation_error(
    api_client,
    mocker,
):

    """ Invalid label_position field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'label_position': 'invalid_position',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    message = '"invalid_position" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'label_position'
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()


def test_partial_update__service_exception__validation_error(
    api_client,
    mocker,
):
    """Service raises BaseServiceException returns validation error"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    fieldset = create_test_fieldset_template(
        account=account,
        template=template,
        kickoff=template.kickoff_instance,
    )
    data = {
        'name': 'Updated Fieldset',
    }
    error_message = 'Service error occurred'
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
        side_effect=BaseServiceException(message=error_message),
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.patch(
        f'/templates/fieldsets/{fieldset.id}',
        data=data,
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        instance=fieldset,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_partial_update_mock.assert_called_once_with(
        name=data['name'],
    )


def test_partial_update__not_existing_fieldset__not_found(api_client, mocker):

    """ Non-existent fieldset returns 404 """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    nonexistent_id = 999999
    data = {
        'name': 'Updated Fieldset',
    }

    api_client.token_authenticate(user=user)

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_partial_update_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.partial_update',
    )
    # act
    response = api_client.patch(
        f'/templates/fieldsets/{nonexistent_id}',
        data=data,
    )

    # assert
    assert response.status_code == 404
    fieldset_service_init_mock.assert_not_called()
    fieldset_partial_update_mock.assert_not_called()
