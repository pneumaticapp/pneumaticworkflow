import pytest
from django.utils import timezone

from src.accounts.enums import BillingPlanType
from src.accounts.messages import (
    MSG_A_0035,
)
from src.authentication.enums import AuthTokenType
from src.processes.enums import (
    FieldType,
    OwnerRole,
    OwnerType,
    PerformerType,
    TemplateType,
)
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.fields import FieldTemplateSelection
from src.processes.models.templates.owner import TemplateOwner
from src.processes.models.templates.template import Template
from src.processes.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_dataset,
    create_test_group,
    create_test_owner,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_list__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    response_1 = api_client.post(
        path='/templates',
        data={
            'name': 'Template 1',
            'is_active': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'fields': [],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                },
            ],
        },
    )
    active_template = Template.objects.get(id=response_1.data['id'])

    wf_name_template = '{{date}} Template 1'
    response_2 = api_client.post(
        path='/templates',
        data={
            'name': 'Template 1',
            'wf_name_template': wf_name_template,
            'is_active': False,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                },
            ],
        },
    )
    draft_template = Template.objects.get(id=response_2.data['id'])

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2

    assert response.data[0]['id'] == active_template.id
    assert response.data[0]['owners'][0]['source_id'] == str(user.id)
    assert response.data[0]['wf_name_template'] is None

    assert response.data[1]['id'] == draft_template.id
    assert response.data[1]['owners'][0]['source_id'] == str(user.id)
    assert response.data[1]['wf_name_template'] is None


def test_list__wf_name_template__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    wf_name_template = '{{date}} Template 1'
    api_client.post(
        path='/templates',
        data={
            'name': 'Template 1',
            'wf_name_template': wf_name_template,
            'is_active': True,
            'owners': [
                {
                    'type': OwnerType.USER,
                    'source_id': user.id,
                    'role': OwnerRole.OWNER,
                },
            ],
            'kickoff': {
                'fields': [],
            },
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id,
                        },
                    ],
                },
            ],
        },
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    assert response.data[0]['wf_name_template'] == wf_name_template


def test_list__template_owners__ok(api_client):

    # arrange
    any_user = create_test_user(email='test@bou.tr')
    create_test_template(
        user=any_user,
        tasks_count=1,
        is_active=True,
    )
    account = create_test_account(plan=BillingPlanType.FREEMIUM)
    user = create_test_user(account=account)
    user2 = create_test_user(
        account=account,
        email='t@t.t',
    )
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.OWNER,
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=user2.id,
    )
    api_client.token_authenticate(user2)

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    owners = response.data[0]['owners']
    assert owners[0]['source_id'] == str(user.id)
    assert owners[1]['source_id'] == str(user2.id)


def test_list__template_owners_is_deleted__ok(api_client):

    # arrange
    user = create_test_user()
    create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    TemplateOwner.objects.filter(user_id=user.id).delete()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__subscription_expired__forbidden(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    account.plan_expiration = timezone.now()
    account.save()
    api_client.token_authenticate(user)
    create_test_template(user, is_active=True)
    create_test_template(user, is_active=True)

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 403
    assert response.data['detail'] == MSG_A_0035


def test_list_ordering_name(api_client):

    user = create_test_user()
    template_one = create_test_template(user)
    template_two = create_test_template(user)
    template_one.name = 'Aa1'
    template_one.save()
    template_two.name = 'Bb2'
    template_two.save()

    api_client.token_authenticate(user)
    response = api_client.get('/templates?ordering=name')

    assert response.status_code == 200

    assert response.data[0]['id'] == template_one.id
    assert response.data[1]['id'] == template_two.id


def test_list_ordering_invert_name(api_client):

    # arrange
    user = create_test_user()
    template_one = create_test_template(user, name='Aa1')
    template_two = create_test_template(user, name='Bb2')
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates?ordering=-name')

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == template_two.id
    assert response.data[1]['id'] == template_one.id


def test_list_invalid_ordering__validation_error(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user=user)
    create_test_template(user)

    # act
    response = api_client.get(
        path='/templates?ordering=DROP OWNED BY CURRENT_USER',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == (
        ErrorCode.VALIDATION_ERROR
    )


def test_list_ordering_date(api_client):
    user = create_test_user()
    template_one = create_test_template(user)
    template_two = create_test_template(user)

    api_client.token_authenticate(user)
    response = api_client.get('/templates?ordering=date')

    assert response.status_code == 200

    assert response.data[0]['id'] == template_one.id
    assert response.data[1]['id'] == template_two.id
    assert template_two.date_created > template_one.date_created


def test_list_ordering_invert_date(api_client):

    user = create_test_user()
    template_one = create_test_template(
        user=user,
        is_active=True,
    )
    template_two = create_test_template(user)
    template_three = create_test_template(user)
    api_client.token_authenticate(user)

    response = api_client.get('/templates?ordering=-date')

    assert response.status_code == 200
    assert response.data[0]['id'] == template_one.id
    assert response.data[1]['id'] == template_three.id
    assert response.data[2]['id'] == template_two.id
    assert template_two.date_created > template_one.date_created
    assert template_three.date_created > template_two.date_created


def test_list__search_name__ok(api_client):

    # arrange
    user = create_test_owner()
    template = create_test_template(user)
    create_test_template(user, name='Not search name')
    search_text = template.name
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates?search={search_text}')

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == template.id


def test_list__search_description__ok(api_client):

    # arrange
    user = create_test_owner()
    search_text = 'search'
    template = create_test_template(user, tasks_count=1)
    template.description = search_text
    template.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates?search={search_text}')

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == template.id


def test_list__search_task_name__ok(api_client):

    # arrange
    user = create_test_owner()
    template = create_test_template(user)
    another_template = create_test_template(user)
    another_template.tasks.update(name='Not search name')
    search_text = template.tasks.get(number=1).name
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates?search={search_text}')

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == template.id


def test_list__search_by_performer__ok(api_client):

    # arrange
    user = create_test_owner()
    invited = create_invited_user(user)
    template = create_test_template(user)
    create_test_template(invited)
    search_text = user.email
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates?search={search_text}')

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == template.id


def test_list__search_priority_1__ok(api_client):

    """ Search priority:
        1. Template name (weight C);
        2. Template description (weight D);
    """

    # arrange
    user = create_test_owner()
    search_text = 'search'

    template_1 = create_test_template(
        user=user,
        tasks_count=1,
        name=search_text,
    )

    create_test_template(user=user)

    template_2 = create_test_template(user=user, tasks_count=1)
    template_2.description = search_text
    template_2.save()

    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_1.id
    assert response.data[1]['id'] == template_2.id


def test_list__search_priority_2__ok(api_client):

    """ Search priority:
        1. Template name (weight C);
        2. Template Task name (weight D);
    """

    # arrange
    user = create_test_owner()
    search_text = 'search'

    template_2 = create_test_template(user=user, tasks_count=1)
    template_2.tasks.update(name=search_text)

    template_1 = create_test_template(
        user=user,
        tasks_count=1,
        name=search_text,
    )
    create_test_template(user=user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_1.id
    assert response.data[1]['id'] == template_2.id


def test_list__search_priority_3__ok(api_client):

    """ Search priority:
        1. Template name (weight C);
        2. Template Task description (weight D);
    """

    # arrange
    user = create_test_owner()
    search_text = 'search'

    template_2 = create_test_template(user=user, tasks_count=1)
    template_2.tasks.update(description=search_text)

    template_1 = create_test_template(
        user=user,
        tasks_count=1,
        name=search_text,
    )
    create_test_template(user=user)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates?search={search_text}')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_1.id
    assert response.data[1]['id'] == template_2.id


def test_list__track_analytics(api_client, mocker):

    # arrange
    user = create_test_user()
    create_test_template(user)
    search_text = 'some text'

    analysis_mock = mocker.patch(
        'src.analysis.services.AnalyticService.'
        'search_search',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/templates?search={search_text}')

    # assert
    assert response.status_code == 200
    analysis_mock.assert_called_once_with(
        user=user,
        page='templates',
        search_text=search_text,
        is_superuser=False,
        auth_type=AuthTokenType.USER,
    )


def test_list__ordering_usage(api_client):

    # arrange
    user = create_test_user()

    template_one = create_test_template(user)
    create_test_workflow(user, template=template_one)
    create_test_workflow(user, template=template_one)
    template_two = create_test_template(user)
    template_three = create_test_template(user)
    create_test_workflow(user, template=template_three)
    create_test_workflow(user, template=template_three)
    create_test_workflow(user, template=template_three)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/templates?ordering=-usage')

    # assert
    assert response.status_code == 200

    assert response.data[0]['id'] == template_three.id
    assert response.data[1]['id'] == template_one.id
    assert response.data[2]['id'] == template_two.id


def test_list__ordering_usage_tasks_count__ok(api_client):

    # arrange
    user = create_test_user()

    template = create_test_template(user, tasks_count=3)
    create_test_workflow(user, template=template)
    create_test_workflow(user, template=template)

    api_client.token_authenticate(user=user)

    # act
    response = api_client.get('/templates?ordering=-usage')

    # assert
    assert response.status_code == 200
    template_data = response.data[0]
    assert template_data['id'] == template.id


def test_list__filter_is_not_public__ok(
    api_client,
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        is_public=False,
    )
    create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )

    # act
    response = api_client.get('/templates?is_public=false')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['is_public'] is False


def test_list__filter_is_public_is_embedded__ok(
    api_client,
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_user(account=account)
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        is_embedded=True,
        is_public=True,
    )
    create_test_template(
        user=user,
        is_active=True,
        is_public=False,
    )

    # act
    response = api_client.get('/templates?is_public=true')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['is_public'] is True
    assert response.data[0]['is_embedded'] is True


def test_list__default_filter_is_public__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )
    create_test_template(
        user=user,
        is_active=True,
        is_public=False,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2


def test_list__invalid_filter_is_public__validation_error(
    api_client,
):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_template(
        user=user,
        is_active=True,
        is_public=True,
    )

    # act
    response = api_client.get(
        path='/templates?is_public=DROP OWNED BY CURRENT_USER',
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == (
        ErrorCode.VALIDATION_ERROR
    )


def test_list__user_is_performer_in_draft__empty_list(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    admin_user = create_test_user(
        account=user.account,
        email='admin@test.test',
        is_account_owner=False,
    )
    user.account.billing_plan = BillingPlanType.PREMIUM
    user.account.save()
    request_data_1 = {
        'name': 'Template 1',
        'is_active': True,
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step changed',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
            {
                'number': 2,
                'name': 'First step changed',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }
    request_data_2 = {
        'is_active': True,
        'name': 'Template 2',
        'owners': [
            {
                'type': OwnerType.USER,
                'source_id': user.id,
                'role': OwnerRole.OWNER,
            },
        ],
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step changed',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
            {
                'number': 2,
                'name': 'First step changed',
                'raw_performers': [
                    {
                        'type': PerformerType.USER,
                        'source_id': user.id,
                    },
                ],
            },
        ],
    }

    response = api_client.post(
        path='/templates',
        data=request_data_1,
    )
    template_1_id = response.data['id']
    response.data['is_active'] = False
    response.data['tasks'][0]['raw_performers'].append({
        'type': PerformerType.USER,
        'source_id': admin_user.id,
    })
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    api_client.put(
        path=f'/templates/{template_1_id}',
        data=response.data,
    )
    response = api_client.post(
        path='/templates',
        data=request_data_2,
    )
    template_2_id = response.data['id']
    response.data['is_active'] = False
    response.data['tasks'][1]['raw_performers'] = [{
        'type': PerformerType.USER,
        'source_id': admin_user.id,
    }]
    api_client.put(
        path=f'/templates/{template_2_id}',
        data=response.data,
    )
    api_client.token_authenticate(admin_user)

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__exclude_onboarding__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_template(
        user,
        type_=TemplateType.ONBOARDING_NON_ADMIN,
    )
    create_test_template(
        user,
        type_=TemplateType.ONBOARDING_ADMIN,
    )
    create_test_template(
        user,
        type_=TemplateType.ONBOARDING_ACCOUNT_OWNER,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__pagination__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_template(user, is_active=True)
    create_test_template(user, is_active=True)
    template = create_test_template(user, is_active=True)
    create_test_template(user, is_active=True)

    # act
    response = api_client.get(
        path='/templates',
        data={
            'limit': 1,
            'offset': 2,
            'ordering': 'date',
        },
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 4
    assert len(response.data['results']) == 1
    assert response.data['results'][0]['id'] == template.id


def test_list__template_starter_user__in_list(api_client):
    """
    Template starter (user) should see template in list.
    Starters can run workflows and see templates in Run Workflow list.
    """

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    owner = create_test_user(
        account=account,
        is_account_owner=True,
    )
    starter_user = create_test_user(
        account=account,
        email='starter@test.test',
        is_account_owner=False,
    )
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.STARTER,
        template=template,
        account=account,
        type=OwnerType.USER,
        user_id=starter_user.id,
    )
    api_client.token_authenticate(starter_user)

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_list__template_starter_group__in_list(api_client):
    """
    Template starter (via group) should see template in list.
    Starters can run workflows and see templates in Run Workflow list.
    """

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    owner = create_test_user(
        account=account,
        is_account_owner=True,
    )
    starter_user = create_test_user(
        account=account,
        email='starter@test.test',
        is_account_owner=False,
    )
    group = create_test_group(
        account=account,
        users=[starter_user],
    )
    template = create_test_template(
        user=owner,
        is_active=True,
    )
    TemplateOwner.objects.create(
        role=OwnerRole.STARTER,
        template=template,
        account=account,
        type=OwnerType.GROUP,
        group=group,
    )
    api_client.token_authenticate(starter_user)

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_list__kickoff_field_selection_type_has_selections(api_client):

    """
    GET /templates returns selections for a kickoff field
    with a selection type (e.g. DROPDOWN).
    FieldTemplateListSerializer.to_representation keeps 'selections'
    when field type is in TYPES_WITH_SELECTIONS.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    selection_field = FieldTemplate.objects.create(
        name='Dropdown field',
        type=FieldType.DROPDOWN,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='dropdown-field-1',
        account=user.account,
    )
    selection = FieldTemplateSelection.objects.create(
        field_template=selection_field,
        template=template,
        value='Option A',
        api_name='selection-1',
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == FieldType.DROPDOWN
    assert 'selections' in field_data
    assert len(field_data['selections']) == 1
    assert field_data['selections'][0] == selection.value


def test_list__kickoff_field_non_selection_type_no_selections_key(
    api_client,
):

    """
    GET /templates does NOT include 'selections' keys for
    kickoff fields with a non-selection type (e.g. STRING).
    FieldTemplateListSerializer.to_representation strips these keys.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    FieldTemplate.objects.create(
        name='String field',
        type=FieldType.STRING,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='string-field-1',
        account=user.account,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == FieldType.STRING
    assert 'selections' not in field_data


def test_list__kickoff_field_with_dataset__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    dataset = create_test_dataset(account=account, items_count=1)
    dataset_item = dataset.items.first()
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    FieldTemplate.objects.create(
        name='Dropdown with dataset',
        type=FieldType.DROPDOWN,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='dropdown-field-1',
        account=user.account,
        dataset=dataset,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == FieldType.DROPDOWN
    assert field_data['selections'][0] == dataset_item.value


def test_list__kickoff_field_with_dataset_and_selections__ok(api_client):

    # arrange
    account = create_test_account()
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    dataset = create_test_dataset(account=account, items_count=1)
    dataset_item = dataset.items.first()
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field_template = FieldTemplate.objects.create(
        name='Dropdown',
        type=FieldType.DROPDOWN,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='dropdown-field-1',
        account=user.account,
        dataset=dataset,
    )
    selection = FieldTemplateSelection.objects.create(
        field_template=field_template,
        value='Some value',
        template=template,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    field_data = response.data[0]['kickoff']['fields'][0]
    assert len(field_data['selections']) == 2
    assert field_data['selections'][0] == selection.value
    assert field_data['selections'][1] == dataset_item.value


def test_list__kickoff_field_description_none_returns_empty_string(
    api_client,
):

    """
    GET /templates converts a None description to an empty string
    for kickoff fields in the list serializer.
    FieldTemplateListSerializer.to_representation coerces None -> ''.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Text field',
        type=FieldType.TEXT,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='text-field-1',
        account=user.account,
        description=None,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['api_name'] == field.api_name
    assert field_data['description'] == ''


def test_list__kickoff_field_description_non_empty(api_client):

    """
    GET /templates returns the actual description string
    when it is set on a kickoff field.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    description = 'Some description text'
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Text field',
        type=FieldType.TEXT,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='text-field-1',
        account=user.account,
        description=description,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['api_name'] == field.api_name
    assert field_data['description'] == description


@pytest.mark.parametrize(
    'field_type', FieldType.TYPES_WITH_SELECTIONS,
)
def test_list__kickoff_field_all_selection_types_include_selections(
    field_type,
    api_client,
):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Selection field',
        type=field_type,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='field-1',
        account=user.account,
    )
    selection = FieldTemplateSelection.objects.create(
        field_template=field,
        template=template,
        value='Value 1',
        api_name='selection-1',
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['type'] == field_type
    assert field_data['selections'][0] == selection.value


def test_list__kickoff_field_required_fields_present(api_client):

    """
    GET /templates returns all expected fields from
    FieldTemplateListSerializer: name, type, is_required, is_hidden,
    description, api_name, and order.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Required field',
        type=FieldType.NUMBER,
        description='Field desc',
        kickoff=kickoff,
        template=template,
        order=3,
        api_name='number-field-1',
        account=user.account,
        is_required=True,
        is_hidden=False,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['name'] == field.name
    assert field_data['type'] == FieldType.NUMBER
    assert field_data['is_required'] is True
    assert field_data['is_hidden'] is False
    assert field_data['description'] == field.description
    assert field_data['api_name'] == field.api_name
    assert field_data['order'] == field.order


def test_list__kickoff_field_multiple_selections_ordered(api_client):

    """
    GET /templates returns all selections of a kickoff field
    in the correct order (ordered by pk per FieldTemplateSelection Meta).
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Radio field',
        type=FieldType.RADIO,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='radio-field-1',
        account=user.account,
    )
    FieldTemplateSelection.objects.create(
        field_template=field,
        template=template,
        value='First',
        api_name='selection-1',
    )
    FieldTemplateSelection.objects.create(
        field_template=field,
        template=template,
        value='Second',
        api_name='selection-2',
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert len(field_data['selections']) == 2
    assert field_data['selections'][0] == 'First'
    assert field_data['selections'][1] == 'Second'


def test_list__kickoff_multiple_fields_ordered_by_order_desc(api_client):

    """
    GET /templates returns kickoff fields ordered by order descending
    (per FieldTemplate Meta: ordering = ['-order']).
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field_order_1 = FieldTemplate.objects.create(
        name='Field order 1',
        type=FieldType.STRING,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='string-field-1',
        account=user.account,
    )
    field_order_3 = FieldTemplate.objects.create(
        name='Field order 3',
        type=FieldType.NUMBER,
        kickoff=kickoff,
        template=template,
        order=3,
        api_name='number-field-1',
        account=user.account,
    )
    field_order_2 = FieldTemplate.objects.create(
        name='Field order 2',
        type=FieldType.TEXT,
        kickoff=kickoff,
        template=template,
        order=2,
        api_name='text-field-1',
        account=user.account,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 3
    assert fields[0]['api_name'] == field_order_3.api_name
    assert fields[1]['api_name'] == field_order_2.api_name
    assert fields[2]['api_name'] == field_order_1.api_name


def test_list__kickoff_field_is_hidden_true(api_client):

    """
    GET /templates correctly serializes is_hidden=True
    for a kickoff field of a non-selection type.
    """

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    kickoff = template.kickoff_instance
    field = FieldTemplate.objects.create(
        name='Hidden field',
        type=FieldType.STRING,
        kickoff=kickoff,
        template=template,
        order=1,
        api_name='string-field-1',
        account=user.account,
        is_hidden=True,
        is_required=False,
    )

    # act
    response = api_client.get('/templates')

    # assert
    assert response.status_code == 200
    fields = response.data[0]['kickoff']['fields']
    assert len(fields) == 1
    field_data = fields[0]
    assert field_data['api_name'] == field.api_name
    assert field_data['is_hidden'] is True
    assert field_data['is_required'] is False
