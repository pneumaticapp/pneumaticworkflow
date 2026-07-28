import pytest
from django.conf import settings

from src.ai.models import AIAgent
from src.processes.enums import (
    OwnerRole,
    OwnerType,
    PerformerType,
)
from src.processes.messages import template as messages
from src.processes.models.templates.task import TaskTemplate
from src.processes.models.workflows.task import TaskPerformer
from src.processes.services.versioning.schemas import (
    RawPerformerTemplateSchemaV1,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_template,
    create_test_user,
    create_test_workflow,
)
from src.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def ai_performers_enabled(mocker):
    mocker.patch.dict(
        settings.PROJECT_CONF,
        {'AI_PERFORMERS': True},
    )


def _setup_user():
    user = create_test_user(is_account_owner=True)
    account = user.account
    account.ai_performers_enabled = True
    account.save(update_fields=['ai_performers_enabled'])
    return user


def _create_agent(account, name='Analyst', **kwargs):
    return AIAgent.objects.create(
        account=account,
        name=name,
        model_slug='test/model',
        **kwargs,
    )


def _template_data(user, raw_performers, task_api_name='task-1'):
    return {
        'name': 'Template',
        'is_active': True,
        'owners': [
            {
                'role': OwnerRole.OWNER,
                'type': OwnerType.USER,
                'source_id': user.id,
            },
        ],
        'kickoff': {},
        'tasks': [
            {
                'number': 1,
                'name': 'First step',
                'api_name': task_api_name,
                'raw_performers': raw_performers,
            },
        ],
    }


def test_create__ai_performer__ok(api_client):

    # arrange
    user = _setup_user()
    agent = _create_agent(user.account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data=_template_data(
            user=user,
            raw_performers=[
                {
                    'type': PerformerType.AI,
                    'source_id': agent.id,
                },
            ],
        ),
    )

    # assert
    assert response.status_code == 200
    data = response.json()
    raw_performer_data = data['tasks'][0]['raw_performers'][0]
    assert raw_performer_data['type'] == PerformerType.AI
    assert raw_performer_data['source_id'] == str(agent.id)
    assert raw_performer_data['label'] == f'AI agent: {agent.name}'
    task = TaskTemplate.objects.get(api_name='task-1')
    raw_performer = task.raw_performers.get()
    assert raw_performer.type == PerformerType.AI
    assert raw_performer.ai_agent_id == agent.id


def test_create__ai_and_human_performers__validation_error(api_client):

    # arrange
    user = _setup_user()
    agent = _create_agent(user.account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data=_template_data(
            user=user,
            raw_performers=[
                {
                    'type': PerformerType.AI,
                    'source_id': agent.id,
                },
                {
                    'type': PerformerType.USER,
                    'source_id': user.id,
                },
            ],
        ),
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == (
        messages.MSG_PT_0077(name='First step')
    )
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['details']['api_name'] == 'task-1'


def test_create__feature_disabled__validation_error(api_client):

    # arrange
    user = create_test_user(is_account_owner=True)
    agent = _create_agent(user.account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data=_template_data(
            user=user,
            raw_performers=[
                {
                    'type': PerformerType.AI,
                    'source_id': agent.id,
                },
            ],
        ),
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PT_0076
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_create__foreign_account_agent__validation_error(api_client):

    # arrange
    user = _setup_user()
    foreign_account = create_test_account()
    agent = _create_agent(foreign_account)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data=_template_data(
            user=user,
            raw_performers=[
                {
                    'type': PerformerType.AI,
                    'source_id': agent.id,
                },
            ],
        ),
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PT_0034
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_create__inactive_agent__validation_error(api_client):

    # arrange
    user = _setup_user()
    agent = _create_agent(user.account, is_active=False)
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data=_template_data(
            user=user,
            raw_performers=[
                {
                    'type': PerformerType.AI,
                    'source_id': agent.id,
                },
            ],
        ),
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PT_0034
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_create__agent_id_not_a_number__validation_error(api_client):

    # arrange
    user = _setup_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data=_template_data(
            user=user,
            raw_performers=[
                {
                    'type': PerformerType.AI,
                    'source_id': 'not-a-number',
                },
            ],
        ),
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PT_0033
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_create__agent_id_not_set__validation_error(api_client):

    # arrange
    user = _setup_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        path='/templates',
        data=_template_data(
            user=user,
            raw_performers=[
                {
                    'type': PerformerType.AI,
                    'source_id': None,
                },
            ],
        ),
    )

    # assert
    assert response.status_code == 400
    assert response.data['message'] == messages.MSG_PT_0075
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR


def test_update__ai_performer__syncs_active_workflow(api_client, mocker):

    """ End to end: replacing the performer of an active template
        with an AI agent reaches the running workflow task through
        the version sync AND dispatches an agent run right away """

    # arrange
    mocker.patch(
        'src.processes.services.templates.'
        'integrations.TemplateIntegrationsService.template_updated',
    )
    run_ai_performer_mock = mocker.patch(
        'src.ai.tasks.run_ai_performer.delay',
    )
    user = _setup_user()
    agent = _create_agent(user.account)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    workflow = create_test_workflow(user=user, template=template)
    task = workflow.tasks.get(number=1)
    assert TaskPerformer.objects.filter(task=task, user=user).exists()
    api_client.token_authenticate(user)
    data = api_client.get(f'/templates/{template.id}').data
    data['tasks'][0]['raw_performers'] = [
        {
            'type': PerformerType.AI,
            'source_id': agent.id,
        },
    ]

    # act
    response = api_client.put(
        f'/templates/{template.id}',
        data=data,
    )

    # assert
    assert response.status_code == 200
    performer = TaskPerformer.objects.get(task=task, ai_agent=agent)
    assert performer.type == PerformerType.AI
    assert not TaskPerformer.objects.filter(
        task=task,
        user=user,
    ).exists()
    run_ai_performer_mock.assert_called_once_with(
        task_id=task.id,
        agent_id=agent.id,
    )


def test_version_schema__ai_performer__includes_ai_agent_id():

    # arrange
    user = _setup_user()
    agent = _create_agent(user.account)
    template = create_test_template(
        user=user,
        tasks_count=1,
        is_active=True,
    )
    task_template = template.tasks.get(number=1)
    raw_performer = task_template.add_raw_performer(
        ai_agent_id=agent.id,
        performer_type=PerformerType.AI,
    )

    # act
    data = RawPerformerTemplateSchemaV1(instance=raw_performer).data

    # assert
    assert data['type'] == PerformerType.AI
    assert data['ai_agent_id'] == agent.id
