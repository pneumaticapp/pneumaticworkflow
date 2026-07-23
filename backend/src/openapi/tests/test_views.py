import pytest

from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_docs__anonymous__ok(api_client):
    # arrange

    # act
    response = api_client.get('/api/docs/')

    # assert
    assert response.status_code == 200


def test_swagger__anonymous__ok(api_client):
    # arrange

    # act
    response = api_client.get('/api/swagger/')

    # assert
    assert response.status_code == 200


def test_schema__anonymous__ok(api_client):
    # arrange

    # act
    response = api_client.get('/api/schema/')

    # assert
    assert response.status_code == 200


def test_docs__bearer__ok(api_client):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/api/docs/')

    # assert
    assert response.status_code == 200


def test_swagger__bearer__ok(api_client):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/api/swagger/')

    # assert
    assert response.status_code == 200


def test_schema__bearer__ok(api_client):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/api/schema/')

    # assert
    assert response.status_code == 200
