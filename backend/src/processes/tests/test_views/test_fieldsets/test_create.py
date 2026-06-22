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
    FieldSetRuleType, FieldType,
)
from src.processes.models.templates.fieldset import (
    FieldsetTemplate,
    FieldsetTemplateRuleOld,
)
from src.processes.models.templates.fields import FieldTemplate

from src.processes.services.fieldsets.fieldset import (
    FieldSetTemplateService,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_not_admin,
    create_test_owner,
    create_test_template,
)

pytestmark = pytest.mark.django_db


def test_create_fieldset__all_fields__ok(api_client, mocker):

    """
        Create fieldset with all fields in request
        and check all fields in response
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    task = template.tasks.first()

    data = {
        'name': 'All Fields Fieldset',
        'title': 'All Fields Title',
        'description': 'Description',
        'label_position': LabelPosition.LEFT,
        'layout': FieldSetLayout.HORIZONTAL,
        'api_name': 'fieldset_api_name',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.TEXT,
                'order': 1,
                'api_name': 'f1',
            },
        ],
        'rules': [
            {
                'type': FieldSetRuleType.SUM_EQUAL,
                'value': '10',
                'api_name': 'r1',
                'fields': [],
            },
        ],
    }

    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name=data['name'],
        title=data['title'],
        description=data['description'],
        label_position=data['label_position'],
        layout=data['layout'],
        api_name=data['api_name'],
    )
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        task=task,
        name='Field 1',
        type='text',
        order=1,
        api_name='f1',
        fieldset=fieldset,
    )
    rule = FieldsetTemplateRuleOld.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='10',
        api_name='r1',
    )
    rule.fields.add(field)
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['id'] == fieldset.id
    assert response.data['name'] == data['name']
    assert response.data['title'] == data['title']
    assert response.data['description'] == data['description']
    assert response.data['label_position'] == data['label_position']
    assert response.data['layout'] == data['layout']
    assert response.data['api_name'] == data['api_name']

    assert len(response.data['fields']) == 1
    assert response.data['fields'][0]['name'] == 'Field 1'
    assert response.data['fields'][0]['api_name'] == 'f1'

    assert len(response.data['rules']) == 1
    assert response.data['rules'][0]['type'] == FieldSetRuleType.SUM_EQUAL
    assert response.data['rules'][0]['api_name'] == 'r1'

    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        title=data['title'],
        description=data['description'],
        layout=data['layout'],
        label_position=data['label_position'],
        api_name=data['api_name'],
        rules=data['rules'],
        fields=data['fields'],
    )


def test_create_fieldset__min_data__ok(api_client, mocker):

    """Create fieldset with minimal request data"""

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    data = {
        'name': 'Minimal Fieldset',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Minimal Fieldset',
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name='Minimal Fieldset',
        rules=[],
        fields=[],
    )


def test_create_fieldset__set_api_name__ok(api_client, mocker):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    data = {
        'name': 'Minimal Fieldset',
        'api_name': 'fs1',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name='Minimal Fieldset',
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    assert response.data['title'] == ''
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        api_name=data['api_name'],
        rules=[],
        fields=[],
    )


def test_create_fieldset__rule_with_one_field__ok(api_client, mocker):

    """
    Create fieldset with fields in rule request and check fields in response
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    template.tasks.first()
    field_api_name = 'f1'
    data = {
        'name': 'All Fields Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.STRING,
                'order': 2,
                'api_name': field_api_name,
            },
            {
                'name': 'Field 2',
                'type': FieldType.URL,
                'order': 1,
                'api_name': 'f2',
            },
        ],
        'rules': [
            {
                'type': FieldSetRuleType.SUM_EQUAL,
                'value': '10',
                'fields': [field_api_name],
            },
        ],
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name=data['name'],
    )
    field = FieldTemplate.objects.create(
        account=account,
        template=template,
        api_name=field_api_name,
        fieldset=fieldset,
    )
    rule = FieldsetTemplateRuleOld.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='10',
    )
    rule.fields.add(field)

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201

    assert len(response.data['rules']) == 1
    assert response.data['rules'][0]['fields'] == [field_api_name]

    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        rules=data['rules'],
        fields=data['fields'],
    )


def test_create_fieldset__rule_with_two_fields__ok(api_client, mocker):

    """
    Create fieldset with fields in rule request and check fields in response
    """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    field_1_api_name = 'f1'
    field_2_api_name = 'f2'
    data = {
        'name': 'All Fields Fieldset',
        'fields': [
            {
                'name': 'Field 1',
                'type': FieldType.STRING,
                'order': 2,
                'api_name': field_1_api_name,
            },
            {
                'name': 'Field 2',
                'type': FieldType.URL,
                'order': 1,
                'api_name': field_2_api_name,
            },
        ],
        'rules': [
            {
                'type': FieldSetRuleType.SUM_EQUAL,
                'value': '10',
                'fields': [field_2_api_name, field_1_api_name],
            },
        ],
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name=data['name'],
    )
    field_1 = FieldTemplate.objects.create(
        account=account,
        template=template,
        api_name=field_1_api_name,
        fieldset=fieldset,
    )
    field_2 = FieldTemplate.objects.create(
        account=account,
        template=template,
        api_name=field_2_api_name,
        fieldset=fieldset,
    )
    rule = FieldsetTemplateRuleOld.objects.create(
        account=account,
        fieldset=fieldset,
        type=FieldSetRuleType.SUM_EQUAL,
        value='10',
    )
    rule.fields.set([field_1, field_2])

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201

    assert len(response.data['rules']) == 1
    assert response.data['rules'][0]['fields'] == [
        field_1_api_name,
        field_2_api_name,
    ]

    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        rules=data['rules'],
        fields=data['fields'],
    )


def test_create_fieldset__unauthenticated__unauthorized(api_client, mocker):

    """Unauthenticated request returns 401"""

    # arrange
    data = {
        'name': 'New Fieldset',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 401
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create_fieldset__expired_sub__permission_denied(api_client, mocker):

    """Expired subscription returns 403"""

    # arrange
    account = create_test_account(
        plan=BillingPlanType.PREMIUM,
        plan_expiration=timezone.now() - timedelta(days=1),
    )
    user = create_test_owner(account=account)
    data = {
        'name': 'New Fieldset',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create_fieldset__billing_plan__permission_denied(api_client, mocker):

    """ Billing plan permission denied returns 403 """

    # arrange
    account = create_test_account(plan=None)
    user = create_test_owner(account=account)
    data = {
        'name': 'New Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0041
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create_fieldset__users_limit__permission_denied(api_client, mocker):

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
    data = {
        'name': 'New Fieldset',
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0037
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create_fieldset__non_admin__permission_denied(api_client, mocker):

    """ Non-admin non-owner user returns 403 """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_not_admin(account=account)
    data = {
        'name': 'New Fieldset',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 403
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create_fieldset__admin__ok(api_client, mocker):

    """ Admin (non-owner) user can create fieldset """

    # arrange
    account = create_test_account()
    create_test_owner(account=account)
    user = create_test_admin(account=account)
    template = create_test_template(
        user=user,
        tasks_count=1,
    )
    data = {
        'name': 'New Fieldset',
    }
    fieldset = FieldsetTemplate.objects.create(
        account=account,
        template=template,
        name=data['name'],
    )
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        return_value=fieldset,
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 201
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name=data['name'],
        rules=[],
        fields=[],
    )


def test_create_fieldset__blank_name__validation_error(api_client, mocker):

    """ Invalid name field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
    }

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = 'This field is required.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'name'
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create_fieldset__invalid_layout__validation_error(api_client, mocker):

    """ Invalid layout field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Test Fieldset',
        'layout': 'invalid_layout',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = '"invalid_layout" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'layout'
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create_fieldset__invalid_label_position__validation_error(
    api_client,
    mocker,
):

    """ Invalid label_position field returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Test Fieldset',
        'label_position': 'invalid_position',
    }
    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )

    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
    )
    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    message = '"invalid_position" is not a valid choice.'
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'label_position'
    fieldset_service_init_mock.assert_not_called()
    fieldset_service_create_mock.assert_not_called()


def test_create_fieldset__service_exception__validation_error(
    api_client,
    mocker,
):
    """ Service raises BaseServiceException returns validation error """

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    data = {
        'name': 'Test Fieldset',
    }
    error_message = 'Service error occurred'

    fieldset_service_init_mock = mocker.patch.object(
        FieldSetTemplateService,
        attribute='__init__',
        return_value=None,
    )
    fieldset_service_create_mock = mocker.patch(
        'src.processes.views.fieldset.FieldSetTemplateService.'
        'create_shared_fieldset',
        side_effect=BaseServiceException(message=error_message),
    )

    api_client.token_authenticate(user=user)

    # act
    response = api_client.post('/fieldsets', data=data)

    # assert
    assert response.status_code == 400
    assert response.data['message'] == error_message
    fieldset_service_init_mock.assert_called_once_with(
        user=user,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )
    fieldset_service_create_mock.assert_called_once_with(
        name='Test Fieldset',
        rules=[],
        fields=[],
    )
