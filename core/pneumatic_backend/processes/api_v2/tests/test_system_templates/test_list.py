import pytest
from pneumatic_backend.processes.enums import SysTemplateType
from pneumatic_backend.processes.models import (
    SystemTemplate,
    SystemTemplateCategory
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)


pytestmark = pytest.mark.django_db


def test_list__ordering_by_name__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    template_2 = SystemTemplate.objects.create(
        is_active=True,
        name='B template',
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Clients requests processing',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                },
                {
                    'name': 'Responsing to client',
                    'number': 3,
                },
                {
                    'name': 'Creating report',
                    'number': 4,
                }
            ],
        }
    )
    category = SystemTemplateCategory.objects.create(
        is_active=True,
        name='Some category'
    )
    template_1 = SystemTemplate.objects.create(
        is_active=True,
        name='A template',
        description='',
        type=SysTemplateType.LIBRARY,
        category=category,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    SystemTemplate.objects.create(
        is_active=True,
        name='Second template',
        type=SysTemplateType.ACTIVATED,
        category=category,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    response = api_client.get('/templates/system')

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_1.id
    assert response.data[0]['name'] == template_1.name
    assert response.data[0]['category'] == category.id
    assert response.data[0]['description'] == template_1.description

    assert response.data[1]['id'] == template_2.id
    assert response.data[1]['name'] == template_2.name
    assert response.data[1]['category'] is None
    assert response.data[1]['description'] is None


def test_system_templates_list_paginated(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    template_data = {
        'name': 'Clients requests processing',
        'kickoff': {},
        'tasks': [
            {
                'name': 'Checking data',
                'number': 1,
            },
            {
                'name': 'Finding reasons of request',
                'number': 2,
            }
        ],
    }
    SystemTemplate.objects.create(
        is_active=True,
        name='First template',
        description='Very beginning of templates',
        template=template_data
    )
    SystemTemplate.objects.create(
        is_active=True,
        name='Second template',
        description='123',
        template=template_data
    )

    response = api_client.get('/templates/system?limit=1&offset=0')

    assert response.status_code == 200
    assert response.data['count'] == 2
    assert len(response.data['results']) == 1


def test_system_templates__only_library_type_library__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    SystemTemplate.objects.create(
        is_active=True,
        name='Second template',
        description='',
        type=SysTemplateType.ACTIVATED,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    SystemTemplate.objects.create(
        is_active=True,
        name='Second template',
        description='',
        type=SysTemplateType.ONBOARDING_ACCOUNT_OWNER,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    SystemTemplate.objects.create(
        is_active=True,
        name='Second template',
        description='',
        type=SysTemplateType.ONBOARDING_ADMIN,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    SystemTemplate.objects.create(
        is_active=True,
        name='Second template',
        description='',
        type=SysTemplateType.ONBOARDING_NON_ADMIN,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    response = api_client.get('/templates/system')

    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__filter_by_search__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    template_1 = SystemTemplate.objects.create(
        is_active=True,
        name='A foo Search text here bar',
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Clients requests processing',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                },
                {
                    'name': 'Responsing to client',
                    'number': 3,
                },
                {
                    'name': 'Creating report',
                    'number': 4,
                }
            ],
        }
    )
    template_2 = SystemTemplate.objects.create(
        is_active=True,
        name='C Second template',
        description='bla bla Search text here bla bla',
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    SystemTemplate.objects.create(
        is_active=True,
        name='A Third template',
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    template_3 = SystemTemplate.objects.create(
        is_active=True,
        name='Z template',
        description='bla bla Se arc h te xt here bla bla Search bla text',
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    response = api_client.get('/templates/system?search=Search text')

    assert response.status_code == 200
    assert len(response.data) == 3
    assert response.data[0]['id'] == template_1.id
    assert response.data[1]['id'] == template_2.id
    assert response.data[2]['id'] == template_3.id


def test_list__filter_by_search_find_union_result__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    template_1 = SystemTemplate.objects.create(
        is_active=True,
        name='Accounts found',
        description=(
            "some words"
        ),
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Accounts Data',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                }
            ]
        }
    )
    template_2 = SystemTemplate.objects.create(
        is_active=True,
        name='Info Payable',
        description=(
            "process is a critical business function"
        ),
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Accounts Payable',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                }
            ]
        }
    )
    response = api_client.get('/templates/system?search=Payable Account')

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_1.id
    assert response.data[1]['id'] == template_2.id


def test_list__filter_by_search_find_union_by_prefix__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    template_1 = SystemTemplate.objects.create(
        is_active=True,
        name='Accounts found',
        description="some words",
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Accounts Data',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                }
            ]
        }
    )
    template_2 = SystemTemplate.objects.create(
        is_active=True,
        name='Info Payable',
        description="process is a critical business function",
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Accounts Payable',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                }
            ]
        }
    )
    response = api_client.get('/templates/system?search=fou pa')

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_1.id
    assert response.data[1]['id'] == template_2.id


def test_list__filter_by_search_by_prefix__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    SystemTemplate.objects.create(
        is_active=True,
        name='Accounts found',
        description="some words",
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Accounts Data',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                }
            ]
        }
    )
    template_2 = SystemTemplate.objects.create(
        is_active=True,
        name='Info Payable',
        description="process is a critical business function",
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Accounts Payable',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                }
            ]
        }
    )
    response = api_client.get('/templates/system?search=fun')

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template_2.id


def test_list__filter_by_search_by_part__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    template = SystemTemplate.objects.create(
        is_active=True,
        name='Accounts Payable',
        description=(
            "The Accounts Payable process is a critical business function"
        ),
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Accounts Payable',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                }
            ]
        }
    )
    response = api_client.get('/templates/system?search=Payab Accounts')

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id


def test_list__filter_by_category__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    category_1 = SystemTemplateCategory.objects.create(
        is_active=True,
        order=1,
        name='First category'
    )
    category_2 = SystemTemplateCategory.objects.create(
        is_active=True,
        order=2,
        name='Second category'
    )
    SystemTemplateCategory.objects.create(
        is_active=True,
        order=2,
        name='Third category'
    )
    template_1 = SystemTemplate.objects.create(
        is_active=True,
        name='First template',
        description='',
        type=SysTemplateType.LIBRARY,
        category=category_1,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    SystemTemplate.objects.create(
        is_active=True,
        name='Second template',
        type=SysTemplateType.LIBRARY,
        category=category_2,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    SystemTemplate.objects.create(
        is_active=True,
        name='Third template',
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    template_4 = SystemTemplate.objects.create(
        is_active=True,
        name='Fourth template',
        category=category_1,
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Clients requests processing',
            'description': 'template desc',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                },
                {
                    'name': 'Responsing to client',
                    'number': 3,
                },
                {
                    'name': 'Creating report',
                    'number': 4,
                }
            ],
        }
    )
    response = api_client.get(f'/templates/system?category={category_1.id}')

    assert response.status_code == 200
    assert len(response.data) == 2
    assert response.data[0]['id'] == template_1.id
    assert response.data[1]['id'] == template_4.id


def test_list__filter_by_category_and_search__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)
    category = SystemTemplateCategory.objects.create(
        is_active=True,
        order=1,
        name='First category'
    )
    template = SystemTemplate.objects.create(
        is_active=True,
        name='First template',
        description='Some Search content here',
        type=SysTemplateType.LIBRARY,
        category=category,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )
    SystemTemplate.objects.create(
        is_active=True,
        name='Search content',
        description='Some Search content here',
        type=SysTemplateType.LIBRARY,
        template={
            'name': 'Clients requests processing',
            'kickoff': {},
            'tasks': [
                {
                    'name': 'Checking data',
                    'number': 1,
                },
                {
                    'name': 'Finding reasons of request',
                    'number': 2,
                }
            ],
        }
    )

    response = api_client.get(
        f'/templates/system?category={category.id}&search=Search content'
    )

    assert response.status_code == 200
    assert len(response.data) == 1
    assert response.data[0]['id'] == template.id
