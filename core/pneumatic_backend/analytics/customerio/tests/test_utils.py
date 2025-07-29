import hmac
from hashlib import sha256
from pneumatic_backend.analytics.customerio.utils import (
    get_webhook_hash,
    check_webhook_hash
)


def test__get_webhook_hash__ok(mocker):

    # arrange
    api_version = 'v0'
    key = '7c17180b839f288cf043b15813207e85f6a9ff254744893bf0e943192c1a89f5'
    timestamp = '1646141357'
    request_body_bytes = (
        b'{"data":{"action_id":42,"campaign_id":23,"content":"Welcome to the '
        b'club, we are with you.","customer_id":"user-123","delivery_id":'
        b'"RAECAAFwnUSneIa0ZXkmq8EdkAM==","headers":{"Custom-Header":'
        b'["custom-value"]},"identifiers":{"id":"user-123"},"recipient":'
        b'"test@example.com","subject":"Thanks for signing up"},"event_id":'
        b'"01E2EMRMM6TZ12TF9WGZN0WJQT","metric":"sent","object_type":'
        b'"email","timestamp":1646141357}'
    )
    mocker.patch(
        'pneumatic_backend.analytics.customerio.utils.settings',
        CUSTOMERIO_WEBHOOK_API_KEY=key,
        CUSTOMERIO_WEBHOOK_API_VERSION=api_version
    )
    msg = f'{api_version}:{timestamp}:'.encode('utf-8') + request_body_bytes
    valid_result = hmac.new(
        key=key.encode('utf-8'),
        msg=msg,
        digestmod=sha256
    ).hexdigest()

    # act
    util_result = get_webhook_hash(
        timestamp=timestamp,
        request_body=request_body_bytes
    )

    # assert
    assert valid_result == util_result


def test__check_webhook_hash__ok(mocker):

    # arrange
    api_version = 'v0'
    key = 'key'
    request_hash = '123sa'
    timestamp = '1613063089'
    mocker.patch(
        'pneumatic_backend.analytics.customerio.utils.settings',
        CUSTOMERIO_WEBHOOK_API_KEY=key,
        CUSTOMERIO_WEBHOOK_API_VERSION=api_version
    )
    request_body_bytes = (
        b'{"data":{"action_id":42,"campaign_id":23,"content":"Welcome to the '
        b'club, we are with you.","customer_id":"user-123","delivery_id":'
        b'"RAECAAFwnUSneIa0ZXkmq8EdkAM==","headers":{"Custom-Header":'
        b'["custom-value"]},"identifiers":{"id":"user-123"},"recipient":'
        b'"test@example.com","subject":"Thanks for signing up"},"event_id":'
        b'"01E2EMRMM6TZ12TF9WGZN0WJQT","metric":"sent","object_type":'
        b'"email","timestamp":1646141357}'
    )
    request_mock = mocker.Mock(
        headers={
            'X-CIO-Timestamp': timestamp,
            'X-CIO-Signature': request_hash
        },
        body=request_body_bytes
    )
    get_webhook_hash_mock = mocker.patch(
        'pneumatic_backend.analytics.customerio.utils.get_webhook_hash',
        return_value=request_hash
    )

    # act
    result = check_webhook_hash(request_mock)

    # assert
    assert result is True
    get_webhook_hash_mock.assert_called_once_with(
        timestamp=timestamp,
        request_body=request_body_bytes
    )
