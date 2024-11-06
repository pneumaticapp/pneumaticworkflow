import pytest

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.processes.models import (
    Template,
    ConditionTemplate
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user
)
from pneumatic_backend.processes.enums import (
    FieldType,
    PerformerType,
    PredicateOperator
)
pytestmark = pytest.mark.django_db


class TestCopyConditionTemplate:

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__conditions__ok(self, is_active, api_client):

        user = create_test_user()
        api_client.token_authenticate(user)
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()

        request_data = {
            'api_name': 'condition-1',
            'order': 1,
            'action': ConditionTemplate.END_WORKFLOW,
            'rules': [
                {
                    'api_name': 'name-1',
                    'predicates': [
                        {
                            'api_name': 'predicate-1',
                            'field': 'field-1',
                            'field_type': FieldType.USER,
                            'operator': PredicateOperator.EXIST
                        }
                    ]
                }
            ]
        }

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': is_active,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 0,
                            'name': 'Name',
                            'type': FieldType.USER,
                            'api_name': 'field-1',
                            'is_required': True,
                        }
                    ]
                },
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
                        'conditions': [request_data],
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])
        response_1_data = response.data['tasks'][0]['conditions'][0]

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks'][0]['conditions']) == 1
        response_2_data = response.data['tasks'][0]['conditions'][0]
        assert not response_2_data.get('id')
        assert response_2_data['api_name'].startswith('condition-')
        assert response_2_data['api_name'] == response_1_data['api_name']
        assert response_2_data['order'] == request_data['order']
        assert response_2_data['action'] == request_data['action']

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__rules__ok(self, is_active, api_client):

        user = create_test_user()
        api_client.token_authenticate(user)
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()

        request_data = {
            'api_name': 'rule-1',
            'predicates': [
                {
                    'api_name': 'predicate-1',
                    'field': 'field-1',
                    'field_type': FieldType.USER,
                    'operator': PredicateOperator.EXIST
                }
            ]
        }

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': is_active,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 0,
                            'name': 'Name',
                            'type': FieldType.USER,
                            'api_name': 'field-1',
                            'is_required': True,
                        }
                    ]
                },
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
                        'conditions': [
                            {
                                'order': 1,
                                'rules': [request_data],
                                'action': 'skip_task'
                            }
                        ],
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])
        response_1_data = (
            response.data['tasks'][0]['conditions'][0]['rules'][0]
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        # assert
        assert response.status_code == 200
        assert len(response.data['tasks'][0]['conditions'][0]['rules']) == 1
        response_2_data = (
            response.data['tasks'][0]['conditions'][0]['rules'][0]
        )
        assert not response_2_data.get('id')
        assert response_2_data['api_name'].startswith('rule-')
        assert response_2_data['api_name'] == response_1_data['api_name']

    @pytest.mark.parametrize('is_active', [True, False])
    def test_clone__predicates__ok(self, is_active, api_client):

        user = create_test_user()
        api_client.token_authenticate(user)
        account = user.account
        account.billing_plan = BillingPlanType.PREMIUM
        account.save()

        request_data = {
            'api_name': 'predicate-1',
            'field': 'field-1',
            'field_type': FieldType.USER,
            'operator': PredicateOperator.EXIST
        }

        response = api_client.post(
            path='/templates',
            data={
                'name': 'Template',
                'is_active': is_active,
                'template_owners': [user.id],
                'kickoff': {
                    'fields': [
                        {
                            'order': 0,
                            'name': 'Name',
                            'type': FieldType.USER,
                            'api_name': 'field-1',
                            'is_required': True,
                        }
                    ]
                },
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
                        'conditions': [
                            {
                                'order': 1,
                                'api_name': 'condition-1',
                                'action': 'skip_task',
                                'rules': [
                                    {
                                        'api_name': 'rule-1',
                                        'predicates': [request_data]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        )
        template = Template.objects.get(id=response.data['id'])
        response_1_data = (
            response.data['tasks'][0][
                'conditions'
            ][0]['rules'][0]['predicates'][0]
        )

        # act
        response = api_client.post(
            f'/templates/{template.id}/clone'
        )

        # assert
        assert response.status_code == 200
        assert len(
            response.data['tasks'][0][
                'conditions'
            ][0]['rules'][0]['predicates']
        ) == 1
        response_2_data = (
            response.data['tasks'][0][
                'conditions'
            ][0]['rules'][0]['predicates'][0]
        )
        assert not response_2_data.get('id')
        api_name = response.data['kickoff']['fields'][0]['api_name']
        assert response_2_data['api_name'].startswith('predicate-')
        assert response_2_data['api_name'] == response_1_data['api_name']
        assert response_2_data['field'] == api_name
        assert response_2_data['field_type'] == response_1_data['field_type']
        assert response_2_data['operator'] == response_1_data['operator']
