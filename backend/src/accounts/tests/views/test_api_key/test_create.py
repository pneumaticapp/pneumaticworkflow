import pytest

from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_create__valid_data__created(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/api-keys',
        data={'name': 'My CI Key'},
    )

    # assert
    assert response.status_code == 201
    assert response.data['name'] == 'My CI Key'
    assert isinstance(response.data['token'], str)
    assert len(response.data['token']) > 16
    assert response.data['prefix'] == (
        response.data['token'][:16]
    )


def test_create__auto_name__name_assigned(api_client, identify_mock):

    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/api-keys',
        data={},
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
    )

    # assert
    assert response.status_code == 401
