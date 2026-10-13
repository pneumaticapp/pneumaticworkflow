from collections.abc import Callable
from types import SimpleNamespace

import pytest

from src.processes.enums import FieldType
from src.processes.models.templates.fields import FieldTemplate
from src.processes.models.templates.template import TemplateIntegrations
from src.processes.models.workflows.fields import TaskField
from src.processes.services.tasks.field import TaskFieldService
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_template,
)
from src.storage.enums import AccessType, SourceType
from src.storage.models import Attachment
from src.storage.utils import get_file_service_file_url

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    'field_type',
    [
        FieldType.TEXT,
        FieldType.STRING,
        FieldType.URL,
    ],
)
@pytest.mark.parametrize('file_scope', [True, False])
def test_complete__remove_existing_text_file_link__requires_write(
    grant: SimpleNamespace,
    delegated_client: Callable,
    task_field: TaskField,
    field_type: str,
    file_scope: bool,
):
    # arrange
    task_field.type = field_type
    task_field.save(update_fields=['type'])
    url = get_file_service_file_url(file_id='old-text-file-1')
    value = url if field_type == FieldType.URL else '[old.txt](' + url + ')'
    TaskFieldService(user=grant.user, instance=task_field).partial_update(
        value=value,
    )
    path = f'/v2/tasks/{task_field.task_id}/complete'
    scopes = ['pneumatic:write']
    if file_scope:
        scopes.append('files:write')
    client = delegated_client(
        tool='complete_task',
        method='POST',
        path=path,
        scopes=scopes,
    )

    # act
    response = client.post(
        path=path,
        data={'output': {task_field.api_name: ''}},
    )
    task_field.refresh_from_db()

    # assert
    if file_scope:
        assert response.status_code == 200, response.content
        assert task_field.value == ''
        assert not Attachment.objects.filter(
            task_id=task_field.task_id,
            file_id='old-text-file-1',
        ).exists()
    else:
        assert response.status_code == 403, response.content
        assert response.json()['required_scopes'] == [
            'pneumatic:write',
            'files:write',
        ]
        assert task_field.value == value
        assert (
            Attachment.objects.filter(
                task_id=task_field.task_id,
                file_id='old-text-file-1',
            ).count()
            == 1
        )


@pytest.mark.parametrize('operation', ['run_workflow', 'complete_task'])
@pytest.mark.parametrize('case', ['foreign', 'restricted', 'scope', 'allowed'])
def test_write__text_file_link__current_scope_and_permission(
    grant: SimpleNamespace,
    delegated_client: Callable,
    task_field: TaskField,
    operation: str,
    case: str,
):
    # arrange
    file_id = 'text-file-link-1'
    account = create_test_account() if case == 'foreign' else grant.account
    access = (
        AccessType.RESTRICTED
        if case == 'restricted'
        else (AccessType.PUBLIC if case == 'foreign' else AccessType.ACCOUNT)
    )
    Attachment.objects.create(
        account=account,
        file_id=file_id,
        access_type=access,
        source_type=SourceType.ACCOUNT,
    )
    link = '[file.txt](' + get_file_service_file_url(file_id=file_id) + ')'
    if operation == 'run_workflow':
        template = create_test_template(user=grant.user, is_active=True)
        TemplateIntegrations.objects.create(
            template=template,
            account=grant.account,
        )
        field = FieldTemplate.objects.create(
            template=template,
            kickoff=template.kickoff_instance,
            account=grant.account,
            api_name='field_text',
            type=FieldType.TEXT,
            name='Text',
        )
        path = f'/templates/{template.pk}/run'
        payload = {'kickoff': {field.api_name: link}}
    else:
        task_field.type = FieldType.TEXT
        task_field.save(update_fields=['type'])
        path = f'/v2/tasks/{task_field.task_id}/complete'
        payload = {'output': {task_field.api_name: link}}
    scopes = ['pneumatic:write'] if case == 'scope' else None
    client = delegated_client(
        tool=operation,
        method='POST',
        path=path,
        scopes=scopes,
    )

    # act
    response = client.post(
        path=path,
        data=payload,
    )

    # assert
    if case == 'allowed':
        assert response.status_code == 200, response.content
        if operation == 'run_workflow':
            workflow = template.workflows.get(pk=response.json()['id'])
            assert workflow.fields.get(api_name=field.api_name).value == link
        else:
            assert (
                Attachment.objects.filter(
                    account=grant.account,
                    file_id=file_id,
                ).count()
                == 2
            )
    else:
        assert response.status_code == 403, response.content
        assert Attachment.objects.filter(file_id=file_id).count() == 1
        if case == 'scope':
            assert response.json()['required_scopes'] == [
                'pneumatic:write',
                'files:read',
                'files:write',
            ]
