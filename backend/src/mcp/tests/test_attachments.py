from collections.abc import Callable
from types import SimpleNamespace

import pytest
from rest_framework.exceptions import NotAuthenticated

from src.generics.tests.clients import PneumaticApiClient
from src.processes.models.workflows.fields import TaskField
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_owner,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize('filter_name', ['task_id', 'workflow_id'])
def test_list_attachments__target_filter__permissions_and_pagination(
    grant: SimpleNamespace,
    delegated_client: Callable,
    task_field: TaskField,
    filter_name: str,
):
    # arrange
    workflow = task_field.workflow
    task = task_field.task
    selected = Attachment.objects.create(
        account=grant.account,
        file_id='selected-file',
        task=task,
        workflow=workflow,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.TASK,
    )
    Attachment.objects.create(
        account=grant.account,
        file_id='restricted-file',
        task=task,
        workflow=workflow,
        access_type=AccessType.RESTRICTED,
        source_type=SourceType.TASK,
    )
    other = create_test_workflow(user=grant.user)
    Attachment.objects.create(
        account=grant.account,
        file_id='other-file',
        task=other.tasks.get(number=1),
        workflow=other,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.TASK,
    )
    client = delegated_client(
        tool='list_attachments',
        method='GET',
        path='/attachments',
    )
    params = {filter_name: getattr(selected, filter_name), 'limit': 1}

    # act
    response = client.get(path='/attachments', data=params)

    # assert
    assert response.status_code == 200, response.content
    assert response.json()['count'] == 1
    assert response.json()['results'][0]['file_id'] == selected.file_id


def test_list_attachments__foreign_public_file__account_isolated(
    grant: SimpleNamespace,
    delegated_client: Callable,
):
    # arrange
    account = create_test_account()
    user = create_test_owner(account=account, email='foreign-owner@test.com')
    workflow = create_test_workflow(user=user)
    Attachment.objects.create(
        account=account,
        file_id='foreign-public-file',
        workflow=workflow,
        access_type=AccessType.PUBLIC,
        source_type=SourceType.WORKFLOW,
    )
    client = delegated_client(
        tool='list_attachments',
        method='GET',
        path='/attachments',
    )

    # act
    response = client.get(
        path='/attachments',
        data={'workflow_id': workflow.pk},
    )

    # assert
    assert response.status_code == 200, response.content
    assert response.json()['count'] == 0
    assert response.json()['results'] == []


def test_list_attachments__anonymous__401(
    api_client: PneumaticApiClient,
):

    # arrange
    path = '/attachments'

    # act
    response = api_client.get(path=path)

    # assert
    assert response.status_code == 401
    assert response.json() == {
        'detail': NotAuthenticated.default_detail,
    }


def test_attachment_detail__anonymous__401(
    api_client: PneumaticApiClient,
    grant: SimpleNamespace,
    task_field: TaskField,
):

    # arrange
    attachment = Attachment.objects.create(
        account=grant.account,
        file_id='detail-file',
        task=task_field.task,
        workflow=task_field.workflow,
        access_type=AccessType.ACCOUNT,
        source_type=SourceType.TASK,
    )
    path = f'/integrations/mcp/attachments/{attachment.pk}'

    # act
    response = api_client.get(path=path)

    # assert
    assert response.status_code == 401
    assert response.json() == {
        'detail': NotAuthenticated.default_detail,
    }


def test_attachment_detail__foreign_account__404(
    grant: SimpleNamespace,
    delegated_client: Callable,
):

    # arrange
    account = create_test_account()
    user = create_test_owner(
        account=account,
        email='foreign-detail@test.com',
    )
    workflow = create_test_workflow(user=user)
    attachment = Attachment.objects.create(
        account=account,
        file_id='foreign-detail-file',
        workflow=workflow,
        access_type=AccessType.PUBLIC,
        source_type=SourceType.WORKFLOW,
    )
    client = delegated_client(
        tool='get_attachment',
        method='GET',
        path=f'/integrations/mcp/attachments/{attachment.pk}',
    )

    # act
    response = client.get(
        path=f'/integrations/mcp/attachments/{attachment.pk}',
    )

    # assert
    assert response.status_code == 404
