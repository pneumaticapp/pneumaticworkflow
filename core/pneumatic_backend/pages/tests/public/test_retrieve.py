import pytest
from pneumatic_backend.pages.models import Page
from pneumatic_backend.pages.enums import PageType


pytestmark = pytest.mark.django_db


def test_retrieve_public_page__existent__ok(api_client):

    # arrange
    page = Page.objects.create(
        title='Test title',
        description='Test desc',
        slug=PageType.SIGNIN
    )

    # act
    response = api_client.get(f'/pages/public/{PageType.SIGNIN}')

    # assert
    assert response.status_code == 200
    assert response.data['title'] == page.title
    assert response.data['description'] == page.description


def test_retrieve_public_page__empty_description__ok(api_client):

    # arrange
    page = Page.objects.create(
        title='Test title',
        slug=PageType.SIGNIN
    )

    # act
    response = api_client.get(f'/pages/public/{PageType.SIGNIN}')

    # assert
    assert response.status_code == 200
    assert response.data['title'] == page.title
    assert response.data['description'] == ''


def test_retrieve_public_page_not_existent__not_found(api_client):

    # arrange
    Page.objects.create(
        title='Test title',
        description='Test desc',
        slug=PageType.SIGNIN
    )

    # act
    response = api_client.get(f'/pages/public/blabla')

    # assert
    assert response.status_code == 404
