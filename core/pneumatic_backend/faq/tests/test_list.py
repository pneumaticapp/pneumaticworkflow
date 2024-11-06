import pytest
from pneumatic_backend.processes.tests.fixtures import (
    create_test_user,
)
from pneumatic_backend.faq.models import FaqItem


pytestmark = pytest.mark.django_db


def test_list__ok(api_client):

    # arrange
    user = create_test_user()
    item_3 = FaqItem.objects.create(
        order=3,
        is_active=True,
        question='Some question 3',
        answer='Some answer 3',
    )
    item_2 = FaqItem.objects.create(
        order=2,
        is_active=True,
        question='Some question 2',
        answer='Some answer 2',
    )
    FaqItem.objects.create(
        order=1,
        is_active=False,
        question='Some question 1',
        answer='Some answer 1',
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.get('/faq')

    # assert
    assert response.status_code == 200
    assert len(response.data) == 2

    data_2 = response.data[0]
    assert data_2['order'] == 2
    assert data_2['question'] == item_2.question
    assert data_2['answer'] == item_2.answer

    data_3 = response.data[1]
    assert data_3['order'] == 3
    assert data_3['question'] == item_3.question
    assert data_3['answer'] == item_3.answer


def test_list__not_auth__permission_denied(api_client):

    # arrange
    FaqItem.objects.create(
        order=3,
        is_active=True,
        question='Some question',
        answer='Some answer',
    )

    # act
    response = api_client.get('/faq')

    # assert
    assert response.status_code == 401
