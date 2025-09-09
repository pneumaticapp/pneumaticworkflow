import pytest
from pneumatic_backend.pages.models import Page
from pneumatic_backend.pages.enums import PageType


pytestmark = pytest.mark.django_db


def test_list_public_page__ok(api_client):

    # arrange
    page_1 = Page.objects.create(
        title='Test title 1',
        description='Test desc 2',
        slug=PageType.SIGNIN
    )
    page_2 = Page.objects.create(
        title='Test title 2',
        description='Test desc 2',
        slug=PageType.RESET_PASSWORD
    )
    Page.objects.create(
        title='Test title 3',
        description='Test desc 3',
        slug='not-public'
    )

    # act
    response = api_client.get(f'/pages/public')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2
    page_data_1 = response.data[0]
    assert page_data_1['slug'] == page_1.slug
    assert page_data_1['title'] == page_1.title
    assert page_data_1['description'] == page_1.description

    page_data_2 = response.data[1]
    assert page_data_2['slug'] == page_2.slug
    assert page_data_2['title'] == page_2.title
    assert page_data_2['description'] == page_2.description
