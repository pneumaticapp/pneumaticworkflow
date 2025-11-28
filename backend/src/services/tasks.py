from typing import Any, Dict

from celery import shared_task

from src.notifications.clients import get_email_client
from src.notifications.enums import EmailTemplate


# TODO: remove in https://my.pneumatic.app/workflows/15592
@shared_task(ignore_result=True)
def send_email_via_customerio(
    user_id: int,
    email: str,
    template_code: EmailTemplate.LITERALS,
    dynamic_data: Dict[str, Any],
):
    email_client = get_email_client()
    email_client.send_email(
        to=email,
        template_code=template_code,
        message_data=dynamic_data or {},
        user_id=user_id,
    )
