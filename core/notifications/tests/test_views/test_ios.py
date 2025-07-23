import pytest
from pneumatic_backend.notifications.models import UserNotifications
from pneumatic_backend.processes.tests.fixtures import create_test_user

pytestmark = pytest.mark.django_db


def test_reset_push_counter__ok(mocker, api_client):

    # arrange
    user = create_test_user()
    counter = UserNotifications.objects.create(
        user=user,
        count_unread_push_in_ios_app=5
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=True
    )

    # act
    response = api_client.post('/notifications/ios/reset-push-counter')

    # assert
    assert response.status_code == 204
    counter.refresh_from_db()
    assert counter.count_unread_push_in_ios_app == 0


def test_reset_push_counter__disable_push__permission_error(
    mocker,
    api_client
):

    # arrange
    user = create_test_user()
    counter = UserNotifications.objects.create(
        user=user,
        count_unread_push_in_ios_app=5
    )
    api_client.token_authenticate(user)
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=False
    )

    # act
    response = api_client.post('/notifications/ios/reset-push-counter')

    # assert
    assert response.status_code == 403
    counter.refresh_from_db()
    assert counter.count_unread_push_in_ios_app == 5
