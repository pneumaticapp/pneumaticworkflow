import pytest
from datetime import timedelta
from django.utils import timezone
from pneumatic_backend.processes.enums import (
    WorkflowEventType,
    WorkflowStatus,
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
    create_test_template,
    create_test_workflow,
    create_test_event,
)
from pneumatic_backend.processes.services.workflow_action import (
    WorkflowActionService,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def replica_mock(mocker):
    mocker.patch('django.conf.settings.REPLICA', 'default')
    yield


def test_titles_by_events__response_data_templates__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
    assert response.data[0]['name'] == template.name
    assert response.data[0]['workflows_count'] == 1


def test_titles_by_events__completed_workflow__ok(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(
        user=user,
        template=template,
        status=WorkflowStatus.DONE
    )
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles_by_events__ended_workflow__ok(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)
    WorkflowActionService().end_process(
        workflow=workflow,
        user=user,
        by_condition=False,
    )

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles_by_events__workflow_deleted__not_found(api_client):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)
    api_client.token_authenticate(user)
    workflow.delete()

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_events__not_event__not_found(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    create_test_workflow(user=user, template=template)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_events__not_workflows__not_found(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    create_test_template(user=user, is_active=True)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_events__default_ordering_by_most_popular__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template_1 = create_test_template(user=user, is_active=True)
    workflow_1 = create_test_workflow(user=user, template=template_1)
    create_test_event(workflow=workflow_1, user=user)
    template_2 = create_test_template(user=user, is_active=True)
    workflow_2_1 = create_test_workflow(user=user, template=template_2)
    create_test_event(workflow=workflow_2_1, user=user)
    workflow_2_2 = create_test_workflow(user=user, template=template_2)
    create_test_event(workflow=workflow_2_2, user=user)
    workflow_2_3 = create_test_workflow(user=user, template=template_2)
    create_test_event(workflow=workflow_2_3, user=user)
    template_3 = create_test_template(user=user, is_active=True)
    workflow_3_1 = create_test_workflow(user=user, template=template_3)
    create_test_event(workflow=workflow_3_1, user=user)
    workflow_3_2 = create_test_workflow(user=user, template=template_3)
    create_test_event(workflow=workflow_3_2, user=user)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == template_2.id
    assert response.data[1]['id'] == template_3.id
    assert response.data[2]['id'] == template_1.id


def test_titles_by_events__default_second_ordering_by_name__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template_1 = create_test_template(user=user, is_active=True, name='One')
    workflow_1 = create_test_workflow(user=user, template=template_1)
    create_test_event(workflow=workflow_1, user=user)
    template_2 = create_test_template(user=user, is_active=True, name='Two')
    workflow_2 = create_test_workflow(user=user, template=template_2)
    create_test_event(workflow=workflow_2, user=user)
    template_3 = create_test_template(user=user, is_active=True, name='Three')
    workflow_3 = create_test_workflow(user=user, template=template_3)
    create_test_event(workflow=workflow_3, user=user)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == template_1.id
    assert response.data[1]['id'] == template_3.id
    assert response.data[2]['id'] == template_2.id


def test_titles_by_events__calc_most_popular_by_status_running_only__ok(
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template_1 = create_test_template(user=user, is_active=True)
    workflow_1_1 = create_test_workflow(
        user=user,
        template=template_1,
        status=WorkflowStatus.DONE
    )
    create_test_event(workflow=workflow_1_1, user=user)
    workflow_1_2 = create_test_workflow(
        user=user,
        template=template_1,
        status=WorkflowStatus.DONE
    )
    create_test_event(workflow=workflow_1_2, user=user)
    create_test_template(user=user, is_active=True)
    template_2 = create_test_template(user=user, is_active=True)
    workflow_2_1 = create_test_workflow(
        user=user,
        template=template_2,
        status=WorkflowStatus.DELAYED
    )
    create_test_event(workflow=workflow_2_1, user=user)
    workflow_2_2 = create_test_workflow(
        user=user,
        template=template_2,
        status=WorkflowStatus.DELAYED
    )
    create_test_event(workflow=workflow_2_2, user=user)
    template_3 = create_test_template(user=user, is_active=True)
    workflow_3 = create_test_workflow(user=user, template=template_3)
    create_test_event(workflow=workflow_3, user=user)
    workflow_3.delete()
    template_4 = create_test_template(user=user, is_active=True)
    workflow_4 = create_test_workflow(user=user, template=template_4)
    create_test_event(workflow=workflow_4, user=user)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert response.data[0]['id'] == template_4.id
    assert response.data[1]['id'] == template_1.id
    assert response.data[2]['id'] == template_2.id


def test_titles_by_events__filter_datetime__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template_1 = create_test_template(user=user, is_active=True)
    workflow_1 = create_test_workflow(user=user, template=template_1)
    create_test_event(
        workflow=workflow_1,
        user=user,
        data_create=timezone.now() - timedelta(hours=1),
    )
    template_2 = create_test_template(user=user, is_active=True)
    workflow_2_1 = create_test_workflow(user=user, template=template_2)
    create_test_event(workflow=workflow_2_1, user=user)
    workflow_2_2 = create_test_workflow(user=user, template=template_2)
    create_test_event(workflow=workflow_2_2, user=user)
    workflow_2_3 = create_test_workflow(user=user, template=template_2)
    create_test_event(workflow=workflow_2_3, user=user)
    template_3 = create_test_template(user=user, is_active=True)
    workflow_3 = create_test_workflow(user=user, template=template_3)
    create_test_event(
        workflow=workflow_3,
        user=user,
        data_create=timezone.now() + timedelta(hours=1),
    )
    date_from = timezone.now() - timedelta(minutes=2)
    date_to = timezone.now() + timedelta(minutes=2)

    # act
    response = api_client.get(
        '/templates/titles-by-events',
        data={
            'event_date_from': date_from,
            'event_date_to': date_to,
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template_2.id


def test_titles_by_events__date_from__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        data_create=timezone.now() + timedelta(hours=1)
    )

    # act
    response = api_client.get(
        '/templates/titles-by-events',
        data={'event_date_from': timezone.now() - timedelta(hours=1)}
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles_by_events__date_from_blank__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        name='First',
        user=user,
        is_active=True
    )
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        data_create=timezone.now() + timedelta(days=1)
    )
    template_2 = create_test_template(
        name='Second',
        user=user,
        is_active=True
    )
    workflow_2 = create_test_workflow(user=user, template=template_2)
    create_test_event(
        workflow=workflow_2,
        user=user,
        data_create=timezone.now() - timedelta(days=1)
    )

    # act
    response = api_client.get(
        '/templates/titles-by-events?event_date_from='
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template.id
    assert response.data[1]['id'] == template_2.id


def test_titles_by_events__date_to__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        data_create=timezone.now() - timedelta(hours=1)
    )

    # act
    response = api_client.get(
        '/templates/titles-by-events',
        data={'event_date_to': timezone.now() + timedelta(hours=1)}
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles_by_events__date_to_blank__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(
        name='First',
        user=user,
        is_active=True
    )
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        data_create=timezone.now() + timedelta(days=1)
    )
    template_2 = create_test_template(
        name='Second',
        user=user,
        is_active=True
    )
    workflow_2 = create_test_workflow(user=user, template=template_2)
    create_test_event(
        workflow=workflow_2,
        user=user,
        data_create=timezone.now() - timedelta(days=1)
    )

    # act
    response = api_client.get(
        '/templates/titles-by-events?event_date_to='
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template.id
    assert response.data[1]['id'] == template_2.id


def test_titles_by_events__empty_string_datetime__ok(api_client):

    # arrange
    date_from = ''
    date_to = ''
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get(
        '/templates/titles-by-events',
        data={
            'event_date_from': date_from,
            'event_date_to': date_to,
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_titles_by_events__invalid_date_period__not_show(api_client):

    # arrange
    date_from = timezone.now() + timedelta(minutes=1)
    date_to = timezone.now() - timedelta(minutes=1)
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get(
        '/templates/titles-by-events',
        data={
            'event_date_from': date_from,
            'event_date_to': date_to,
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


@pytest.mark.parametrize(
    "date_from",
    [
        timezone.now().strftime('%Y-%m-%d'),
        "undefined",
        'DELETE+FROM+accounts_user',
    ],
)
def test_titles_by_events__invalid_date_from__validation_error(
    api_client,
    date_from
):

    # arrange
    message = (
        'Datetime has wrong format. Use one of these formats instead:'
        ' YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get(
        '/templates/titles-by-events',
        data={'event_date_from': date_from}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'event_date_from'
    assert response.data['details']['reason'] == message


@pytest.mark.parametrize(
    "date_to",
    [
        timezone.now().strftime('%Y-%m-%d'),
        "undefined",
        'DELETE+FROM+accounts_user',
    ],
)
def test_titles_by_events__invalid_date_to__validation_error(
    api_client,
    date_to
):

    # arrange
    message = (
        'Datetime has wrong format. Use one of these formats instead:'
        ' YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get(
        '/templates/titles-by-events',
        data={'event_date_to': date_to}
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'event_date_to'
    assert response.data['details']['reason'] == message


def test_titles_by_events__incorrect_datetime__validation_error(api_client):

    # arrange
    message = (
        'Datetime has wrong format. Use one of these formats instead:'
        ' YYYY-MM-DDThh:mm[:ss[.uuuuuu]][+HH:MM|-HH:MM|Z].'
    )
    date_from = 'undefined'
    date_to = 'undefined'
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get(
        '/templates/titles-by-events',
        data={
            'event_date_from': date_from,
            'event_date_to': date_to,
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'event_date_from'
    assert response.data['details']['reason'] == message


@pytest.mark.parametrize(
    "type_event",
    [
        WorkflowEventType.COMMENT,
        WorkflowEventType.TASK_COMPLETE,
        WorkflowEventType.RUN,
        WorkflowEventType.COMPLETE,
        WorkflowEventType.ENDED,
        WorkflowEventType.TASK_REVERT,
        WorkflowEventType.REVERT,
        WorkflowEventType.URGENT,
        WorkflowEventType.NOT_URGENT,
        WorkflowEventType.TASK_PERFORMER_CREATED,
        WorkflowEventType.TASK_PERFORMER_DELETED,
        WorkflowEventType.FORCE_DELAY,
        WorkflowEventType.FORCE_RESUME,
        WorkflowEventType.DUE_DATE_CHANGED,
    ],
)
def test_titles_by_events__allowed_type_event__ok(api_client, type_event):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=type_event
    )

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


@pytest.mark.parametrize(
    "type_event",
    [
        WorkflowEventType.DELAY,
        WorkflowEventType.ENDED_BY_CONDITION,
        WorkflowEventType.TASK_START,
        WorkflowEventType.TASK_SKIP,
        WorkflowEventType.TASK_SKIP_NO_PERFORMERS,
    ],
)
def test_titles_by_events__disallow_type_event__not_show(
    api_client,
    type_event
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(
        workflow=workflow,
        user=user,
        type_event=type_event
    )

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_events__user_failed_authenticate__permission_denied(
    api_client
):

    # arrange
    user = create_test_user()
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 401


def test_titles_by_events__user_not_receive_data_another_account__not_show(
    api_client
):

    # arrange
    user = create_test_user()
    user_2 = create_test_user(email='test@test.test')
    api_client.token_authenticate(user_2)
    template = create_test_template(user=user, is_active=True)
    workflow = create_test_workflow(user=user, template=template)
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_titles_by_events__template_is_active_false__ok(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    workflow = create_test_workflow(user=user)
    create_test_event(workflow=workflow, user=user)

    # act
    response = api_client.get('/templates/titles-by-events')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == workflow.template_id
