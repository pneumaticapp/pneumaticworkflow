import pytest
from pneumatic_backend.navigation.tests.fixtures import create_test_menu
from pneumatic_backend.processes.tests.fixtures import create_test_user

pytestmark = pytest.mark.django_db


def test_menu__ok(api_client):

    # arrange
    user = create_test_user()
    menu = create_test_menu()
    first_item = menu.items.get(order=1)
    second_item = menu.items.get(order=2)
    second_item.show = False
    second_item.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/navigation/menu/{menu.slug}')

    # assert
    assert response.status_code == 200
    assert response.data['slug'] == menu.slug
    assert response.data['label'] == menu.label
    assert response.data['link'] == menu.link
    items = response.data['items']
    assert len(items) == 1
    assert items[0]['label'] == first_item.label
    assert items[0]['link'] == first_item.link
    assert items[0]['order'] == first_item.order


def test_menu__ordering__ok(api_client):

    # arrange
    user = create_test_user()
    menu = create_test_menu(count_items=3)
    first_item = menu.items.get(order=1)
    second_item = menu.items.get(order=2)
    third_item = menu.items.get(order=3)
    first_item.order = 2
    first_item.save()
    second_item.order = 1
    second_item.save()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/navigation/menu/{menu.slug}')

    # assert
    assert response.status_code == 200
    items = response.data['items']
    assert len(items) == 3
    assert items[0]['label'] == second_item.label
    assert items[0]['order'] == 1
    assert items[1]['label'] == first_item.label
    assert items[1]['order'] == 2
    assert items[2]['label'] == third_item.label
    assert items[2]['order'] == 3


def test_menu__not_auth__permission_denied(api_client):

    # arrange
    menu = create_test_menu()

    # act
    response = api_client.get(f'/navigation/menu/{menu.slug}')

    # assert
    assert response.status_code == 401


def test_menu__empty_items__ok(api_client):

    # arrange
    user = create_test_user()
    menu = create_test_menu(count_items=0)
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/navigation/menu/{menu.slug}')

    # assert
    assert response.status_code == 200
    assert response.data['slug'] == menu.slug
    assert response.data['label'] == menu.label
    assert response.data['link'] == menu.link
    items = response.data['items']
    assert len(items) == 0


def test_menu__not_exists__not_found(api_client):

    # arrange
    user = create_test_user()
    api_client.token_authenticate(user)

    # act
    response = api_client.get(f'/navigation/menu/help-center')

    # assert
    assert response.status_code == 404
