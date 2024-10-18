from celery.task import task
from pneumatic_backend.utils.logging import (
    capture_sentry_message,
    SentryLogLevel
)
import json
import requests
from django.core.serializers.json import DjangoJSONEncoder


@task(autoretry_for=(requests.ConnectionError, requests.HTTPError),
      retry_backoff=True,
      retry_kwargs={'max_retries': 5})
def deliver_webhook(target_url, json_payload):
    try:
        response = requests.post(
            url=target_url,
            data=json_payload,
            headers={'Content-Type': 'application/json'}
        )
    except requests.ConnectionError as e:
        capture_sentry_message(
            message='HttpException sending webhook',
            data={
                'request_url': target_url,
                'exception': str(e)
            },
            level=SentryLogLevel.INFO
        )
    else:
        if not response.ok:
            data = {
                'request_url': target_url,
                'response_status': response.status_code
            }
            if response.status_code != 404:
                content_type = response.headers.get('content-type', '')
                if 'text' in content_type:
                    data['response_text'] = response.text
                elif 'application/json' in content_type:
                    data['response_json'] = response.json()
            capture_sentry_message(
                message='Error sending webhook',
                data=data,
                level=SentryLogLevel.INFO
            )
        if response.status_code >= 500:
            response.raise_for_status()


def deliver_hook_wrapper(target, payload, instance, hook):
    # pylint: disable=unused-argument
    deliver_webhook.delay(target, json.dumps(payload, cls=DjangoJSONEncoder))
