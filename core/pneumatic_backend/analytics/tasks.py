from typing import List
from celery import shared_task
from django.contrib.auth import get_user_model
from pneumatic_backend.analytics.mixins import BaseIdentifyMixin

UserModel = get_user_model()


def _identify_users(user_ids: List[int]):

    users = UserModel.objects.select_related(
        'account'
    ).prefetch_related(
        'account__accountsignupdata_set'
    ).prefetch_related(
        'incoming_invites'
    ).by_ids(user_ids).active().order_by('id')

    for user in users:
        BaseIdentifyMixin.identify(user)


@shared_task(ignore_result=True)
def identify_users(user_ids: List[int]):
    _identify_users(user_ids)
