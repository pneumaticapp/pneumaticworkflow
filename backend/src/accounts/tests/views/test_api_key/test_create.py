import pytest

from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_create__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/api-keys',
        data={'name': 'My CI Key'},
        format='json',
    )

    # assert
    assert response.status_code == 201
    assert response.data['name'] == 'My CI Key'
    assert isinstance(response.data['key'], str)
    assert len(response.data['key']) > 16
    assert response.data['prefix'] == (
        response.data['key'][:16]
    )


def test_create__auto_name__ok(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/api-keys',
        data={},
        format='json',
    )

    # assert
    assert response.status_code == 201
    assert response.data['name'] == 'API Key #1'


def test_create__name_too_long__validation_error(
    api_client,
    identify_mock,
):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/api-keys',
        data={'name': 'A' * 201},
        format='json',
    )

    # assert
    assert response.status_code == 400
    assert 'name' in response.data


def test_create__not_authenticated__unauthorized(
    api_client,
    identify_mock,
):

    # arrange

    # act
    response = api_client.post(
        '/accounts/api-keys',
        data={'name': 'Key'},
        format='json',
    )

    # assert
    assert response.status_code == 401
