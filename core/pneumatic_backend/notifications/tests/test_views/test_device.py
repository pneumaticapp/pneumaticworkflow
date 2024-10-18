import pytest
from pneumatic_backend.notifications.models import Device, UserNotifications
from pneumatic_backend.processes.tests.fixtures import create_test_user


pytestmark = pytest.mark.django_db


def test_create__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=True
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    token = 'fcm_token'

    # act
    response = api_client.post(
        '/notifications/device',
        data={'token': token},

    )

    # assert
    assert response.status_code == 200
    assert Device.objects.get(
        token=token,
        user=user,
        description='Firefox'
    )
    assert UserNotifications.objects.get(
        user=user,
        count_unread_push_in_ios_app=0
    )


def test_create__disable_push__permission_error(mocker, api_client):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=False
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    token = 'fcm_token'

    # act
    response = api_client.post(
        '/notifications/device',
        data={'token': token},

    )

    # assert
    assert response.status_code == 403


def test_create__duplicate_user_token__update_date(mocker, api_client):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=True
    )
    user = create_test_user()
    api_client.token_authenticate(user)
    token = 'fcm_token'
    api_client.post('/notifications/device', data={'token': token})
    device = Device.objects.get(token=token)
    date_updated = device.date_updated

    # act
    response = api_client.post(
        '/notifications/device',
        data={'token': token},
    )

    # assert
    assert response.status_code == 200
    device = Device.objects.get(token=token)
    assert device.user_id == user.id
    assert device.date_updated > date_updated


def test_create__duplicate_token_other_user__update_user(mocker, api_client):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=True
    )
    user = create_test_user()
    other_user = create_test_user(email='other_user@pneumatic.app')
    token = 'fcm_token'

    api_client.token_authenticate(user)
    api_client.post(
        '/notifications/device',
        data={'token': token},
    )
    api_client.token_authenticate(other_user)

    # act
    response = api_client.post(
        '/notifications/device',
        data={'token': token},
    )

    # assert
    assert response.status_code == 200
    device = Device.objects.get(token=token)
    assert device.user_id == other_user.id


def test_destroy__ok(mocker, api_client):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=True
    )
    user = create_test_user()
    token = 'fcm_token'
    Device.objects.create(token=token, user=user)

    api_client.token_authenticate(user)

    # act
    response = api_client.delete(
        f'/notifications/device/{token}',
    )

    # assert
    assert response.status_code == 204
    assert Device.objects.filter(token=token).exists() is False


def test_destroy__disable_push__permission_error(mocker, api_client):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=False
    )
    user = create_test_user()
    token = 'fcm_token'
    Device.objects.create(token=token, user=user)

    api_client.token_authenticate(user)

    # act
    response = api_client.delete(
        f'/notifications/device/{token}',
    )

    # assert
    assert response.status_code == 403
    assert Device.objects.filter(token=token).exists()


def test_destroy__another_user__not_found(mocker, api_client):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=True
    )
    user = create_test_user()
    another_user = create_test_user(
        email='another_user@pneumatic.app'
    )
    token = 'fcm_token'
    Device.objects.create(token=token, user=user)

    api_client.token_authenticate(another_user)

    # act
    response = api_client.delete(
        f'/notifications/device/{token}',
    )

    # assert
    assert response.status_code == 404
    assert Device.objects.filter(token=token).exists()


@pytest.mark.parametrize(
    'method', ['get', 'put', 'patch'],
)
def test_not_allowed_methods(mocker, api_client, method):

    # arrange
    mocker.patch(
        'pneumatic_backend.notifications.views.PushPermission.has_permission',
        return_value=True
    )
    user = create_test_user()
    token = 'fcm_token'
    api_client.token_authenticate(user)

    # act
    response = getattr(api_client, method)(
        f'/notifications/device/{token}',
    )

    # assert
    assert response.status_code == 405
