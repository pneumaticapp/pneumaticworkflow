import hmac
from hashlib import sha256
from django.conf import settings
from rest_framework.request import Request


def get_webhook_hash(
    timestamp: str,
    request_body: bytes
) -> str:

    key_bytes = settings.CUSTOMERIO_WEBHOOK_API_KEY.encode('utf-8')
    api_version = settings.CUSTOMERIO_WEBHOOK_API_VERSION
    msg_bytes = f'{api_version}:{timestamp}:'.encode('utf-8') + request_body
    result = hmac.new(
        key=key_bytes,
        msg=msg_bytes,
        digestmod=sha256
    ).hexdigest()
    return result


def check_webhook_hash(
    request: Request
) -> bool:

    timestamp = str(request.headers.get('X-CIO-Timestamp'))
    request_hash = request.headers.get('X-CIO-Signature')
    if not timestamp or not request_hash or not request.body:
        return False
    valid_hash = get_webhook_hash(
        timestamp=timestamp,
        request_body=request.body
    )
    return valid_hash == request_hash
