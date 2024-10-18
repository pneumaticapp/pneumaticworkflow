import pytest
from pneumatic_backend.processes.models import (
    SystemTemplateCategory,
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)


pytestmark = pytest.mark.django_db


def test_list__not_exist__empty_result(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/templates/system/categories')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 0


def test_list__ok(api_client):

    user = create_test_user()
    api_client.token_authenticate(user)

    category_2 = SystemTemplateCategory.objects.create(
        name='Sales',
        order=2,
        icon='https://some.com/img.jpg',
        color='#fff',
        template_color='#eaeaea',
        is_active=True
    )
    category_1 = SystemTemplateCategory.objects.create(
        name='Onboarding',
        order=1,
        icon='https://some.com/img1.jpg',
        color='#000',
        template_color='#cecece',
        is_active=True
    )
    SystemTemplateCategory.objects.create(
        name='Onboarding',
        order=3,
        icon='https://some.com/img1.jpg',
        color='#000',
        template_color='#ffffff',
        is_active=False
    )

    # act
    response = api_client.get('/templates/system/categories')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    data_1 = response.data[0]
    assert data_1['name'] == category_1.name
    assert data_1['id'] == category_1.id
    assert data_1['order'] == category_1.order
    assert data_1['icon'] == category_1.icon
    assert data_1['color'] == category_1.color
    assert data_1['template_color'] == category_1.template_color

    data_2 = response.data[1]
    assert data_2['name'] == category_2.name
    assert data_2['id'] == category_2.id
    assert data_2['order'] == category_2.order
    assert data_2['icon'] == category_2.icon
    assert data_2['color'] == category_2.color
    assert data_2['template_color'] == category_2.template_color
