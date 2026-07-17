

def test_webhook__ok(api_client, mocker):

    # arrange
    data = {
      "id": "evt_2Zj5zzFU3a9abcZ1aYYYaaZ1",
      "type": "some type",
      "object": "event",
      "api_version": "2022-11-15",
      "created": 1633887337,
      "data": {
        "object": {},
      },
    }
    task_mock = mocker.patch(
        'src.payment.views.handle_webhook.delay',
    )
    has_permission_mock = mocker.patch(
        'src.payment.views.StripeWebhookPermission'
        '.has_permission',
        return_value=True,
    )

    # act
    response = api_client.post(
        path='/payment/stripe/webhooks',
        data=data,
    )

    # assert
    assert response.status_code == 204
    has_permission_mock.assert_called_once()
    task_mock.assert_called_once_with(
        data=data,
    )
