import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.models import (
    ChecklistTemplateSelection,
    ChecklistTemplate
)
from pneumatic_backend.processes.enums import (
    PerformerType,
)
from pneumatic_backend.utils.validation import ErrorCode
from pneumatic_backend.processes.messages.workflow import (
    MSG_PW_0056,
)
from pneumatic_backend.processes.messages import template as messages


pytestmark = pytest.mark.django_db


def test_create__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    selections_data = [
        {
            'api_name': 'cl-selection-1',
            'value': 'some value 1'
        }
    ]
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': [
                        {
                            'api_name': 'checklist-1',
                            'selections': selections_data
                        }
                    ],
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks'][0]['checklists'][0]['selections']) == 1
    checklist_data = response.data['tasks'][0]['checklists'][0]
    data = checklist_data['selections'][0]
    assert data.get('id') is None
    assert data['api_name'] == 'cl-selection-1'

    template_id = response.data['id']
    checklist = ChecklistTemplate.objects.get(
        api_name=checklist_data['api_name'],
        template_id=template_id
    )
    assert ChecklistTemplateSelection.objects.filter(
        api_name='cl-selection-1',
        value='some value 1',
        template_id=template_id,
        checklist=checklist
    ).exists()


def test_create__generate_api_name__ok(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    api_name = 'generated-api-name'
    mocker.patch(
        'pneumatic_backend.processes.models.templates.'
        'checklist.ChecklistTemplateSelection._create_api_name',
        return_value=api_name
    )
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    selections_data = [
        {
            'value': 'some value 1'
        }
    ]

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': [
                        {
                            'api_name': 'checklist-1',
                            'selections': selections_data
                        }
                    ],
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    checklist_data = response.data['tasks'][0]['checklists'][0]
    data = checklist_data['selections'][0]
    template_id = response.data['id']

    assert data['api_name'] == api_name
    checklist = ChecklistTemplate.objects.get(
        api_name=checklist_data['api_name'],
        template_id=template_id
    )
    assert ChecklistTemplateSelection.objects.filter(
        api_name=api_name,
        value='some value 1',
        template_id=template_id,
        checklist=checklist
    ).exists()


def test_create__draft__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    selections_data = [
        {
            'api_name': 'cl-selection-1',
            'value': 'some value 1'
        }
    ]

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': False,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': [
                        {
                            'api_name': 'checklist-1',
                            'selections': selections_data
                        }
                    ],
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks'][0]['checklists'][0]['selections']) == 1
    data = response.data['tasks'][0]['checklists'][0]['selections'][0]
    assert data.get('id') is None
    assert data['api_name'] == 'cl-selection-1'
    assert data['value'] == 'some value 1'


def test_create__with_equal_api_names_in_one_checklist__create_last(
    mocker,
    api_client,
):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    api_name = 'cl-selection-1'
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )
    selections_data = [
        {
            'api_name': api_name,
            'value': 'some value 1'
        },
        {
            'api_name': api_name,
            'value': 'some value 2'
        }
    ]

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': [
                        {
                            'api_name': 'checklist-1',
                            'selections': selections_data
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 200
    assert len(response.data['tasks'][0]['checklists'][0]['selections']) == 1
    data = response.data['tasks'][0]['checklists'][0]['selections'][0]
    assert data['api_name'] == api_name


def test_create__equal_api_names_in_different_checklists__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    step = 'First step'
    checklist_item_api_name = 'cl-selection-1'
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': step,
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ],
                    'checklists': [
                        {
                            'api_name': 'checklist-1',
                            'selections': [
                                {
                                    'api_name': checklist_item_api_name,
                                    'value': 'some value 1'
                                }
                            ]
                        },
                        {
                            'api_name': 'checklist-2',
                            'selections': [
                                {
                                    'api_name': checklist_item_api_name,
                                    'value': 'some value 2'
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    message = messages.MSG_PT_0048(
        step_name=step,
        api_name=checklist_item_api_name
    )
    assert response.data['message'] == message
    assert response.data['details']['reason'] == message
    assert response.data['details']['api_name'] == checklist_item_api_name


def test_create__limit_exceeded__ok(api_client, mocker):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)
    selections_data = [
        {
            'api_name': 'cl-selection-1',
            'value': 'a' * 2001
        }
    ]
    mocker.patch(
        'pneumatic_backend.analytics.services.AnalyticService'
        '.checklist_created'
    )

    # act
    response = api_client.post(
        path='/templates',
        data={
            'name': 'Template',
            'template_owners': [user.id],
            'is_active': True,
            'kickoff': {},
            'tasks': [
                {
                    'number': 1,
                    'name': 'First step',
                    'checklists': [
                        {
                            'api_name': 'checklist-1',
                            'selections': selections_data
                        }
                    ],
                    'raw_performers': [
                        {
                            'type': PerformerType.USER,
                            'source_id': user.id
                        }
                    ]
                }
            ]
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_PW_0056
    assert response.data['details']['reason'] == MSG_PW_0056
    assert response.data['details']['api_name'] == 'cl-selection-1'
