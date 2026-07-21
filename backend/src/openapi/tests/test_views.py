import pytest
from django.test import override_settings

from src.authentication.tokens import PneumaticToken
from src.openapi.views import LOGIN_PATH
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


@override_settings(FRONTEND_URL='https://app.example.com')
def test_docs__anonymous__redirects_to_login(api_client):
    # arrange
    expected_url = f'https://app.example.com{LOGIN_PATH}'

    # act
    response = api_client.get('/api/docs/')

    # assert
    assert response.status_code == 302
    assert response.url == expected_url


@override_settings(FRONTEND_URL='https://app.example.com')
def test_redoc__anonymous__redirects_to_login(api_client):
    # arrange
    expected_url = f'https://app.example.com{LOGIN_PATH}'

    # act
    response = api_client.get('/api/redoc/')

    # assert
    assert response.status_code == 302
    assert response.url == expected_url


def test_schema__anonymous__unauthorized(api_client):
    # arrange
    path = '/api/schema/'

    # act
    response = api_client.get(path)

    # assert
    assert response.status_code == 401


def test_docs__bearer__ok(api_client):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/api/docs/')

    # assert
    assert response.status_code == 200


def test_redoc__bearer__ok(api_client):
    # arrange
    user = create_test_owner()
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/api/redoc/')

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


def test_docs__cookie__ok(api_client):
    # arrange
    user = create_test_owner()
    token = PneumaticToken.create(
        user=user,
        user_agent='Firefox',
        user_ip='192.168.0.1',
    )
    api_client.cookies['token'] = token

    # act
    response = api_client.get('/api/docs/')

    # assert
    assert response.status_code == 200


def test_schema__cookie__ok(api_client):
    # arrange
    user = create_test_owner()
    token = PneumaticToken.create(
        user=user,
        user_agent='Firefox',
        user_ip='192.168.0.1',
    )
    api_client.cookies['token'] = token

    # act
    response = api_client.get('/api/schema/')

    # assert
    assert response.status_code == 200
