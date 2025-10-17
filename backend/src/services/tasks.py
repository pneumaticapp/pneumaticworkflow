from typing import Any, Dict

from celery import shared_task
from customerio import APIClient, SendEmailRequest
from django.conf import settings

from src.notifications.enums import (
    EmailTemplate,
    cio_template_ids,
)


# TODO: remove in https://my.pneumatic.app/workflows/15592
@shared_task(ignore_result=True)
def send_email_via_customerio(
    user_id: int,
    email: str,
    template_code: EmailTemplate.LITERALS,
    dynamic_data: Dict[str, Any],
):
    client = APIClient(settings.CUSTOMERIO_TRANSACTIONAL_API_KEY)
    message_id = cio_template_ids[template_code]
    request = SendEmailRequest(
        to=email,
        transactional_message_id=message_id,
        message_data=dynamic_data or {},
        identifiers={
            'id': user_id,
        },
    )
    client.send_email(request)
