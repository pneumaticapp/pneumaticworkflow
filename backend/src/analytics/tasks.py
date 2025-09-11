from celery import shared_task
from typing import List, Optional
from src.analytics.services import AnalyticService
from src.analytics.events import GroupsAnalyticsEvent
from src.authentication.enums import AuthTokenType
from django.contrib.auth import get_user_model
from src.analytics.mixins import BaseIdentifyMixin
import time

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


def _track_user_changes(
    user_ids: List[int],
    text: str,
    **props
):
    emails = UserModel.objects.filter(id__in=user_ids).only_emails()
    for email in emails:
        AnalyticService.groups_updated(
            text=f"{text} {email}.",
            **props
        )


@shared_task(ignore_result=True)
def track_group_analytics(
    event: GroupsAnalyticsEvent,
    user_id: int,
    user_email: str,
    user_first_name: str,
    user_last_name: str,
    group_photo: Optional[str],
    group_users: Optional[List[int]],
    account_id: int,
    group_id: int,
    group_name: str,
    auth_type: AuthTokenType,
    is_superuser: bool,
    new_users_ids: Optional[List[int]] = None,
    removed_users_ids: Optional[List[int]] = None,
    new_name: Optional[str] = None,
    new_photo: Optional[str] = None,
):
    base_text = f'{group_name} (id: {group_id}).'
    common_props = {
        'user_id': user_id,
        'user_email': user_email,
        'user_first_name': user_first_name,
        'user_last_name': user_last_name,
        'group_photo': group_photo,
        'group_users': group_users,
        'account_id': account_id,
        'group_id': group_id,
        'group_name': group_name,
        'auth_type': auth_type,
        'is_superuser': is_superuser,
    }

    if event == GroupsAnalyticsEvent.created:
        AnalyticService.groups_created(
            text=base_text,
            **common_props
        )
        time.sleep(1)
        if new_photo:
            text_photo = f'{base_text} Added group photo (url: {new_photo}).'
            AnalyticService.groups_updated(
                text=text_photo,
                **common_props
            )
        if new_users_ids:
            text_add_user = f"{base_text} Added user:"
            _track_user_changes(
                user_ids=new_users_ids,
                text=text_add_user,
                **common_props
            )

    elif event == GroupsAnalyticsEvent.updated:
        if new_name:
            text_name = f'{base_text} Changed the group name to "{new_name}".'
            AnalyticService.groups_updated(
                text=text_name,
                **common_props
            )

        if new_photo:
            text_photo = f'{base_text} Added group photo (url: {new_photo}).'
            AnalyticService.groups_updated(
                text=text_photo,
                **common_props
            )
        elif new_photo == '':
            text_photo = f'{base_text} Delete group photo.'
            AnalyticService.groups_updated(
                text=text_photo,
                **common_props
            )

        if new_users_ids:
            text_add_user = f"{base_text} Added user:"
            _track_user_changes(
                user_ids=new_users_ids,
                text=text_add_user,
                **common_props
            )

        if removed_users_ids:
            text_remove_user = f"{base_text} Remove user:"
            _track_user_changes(
                user_ids=removed_users_ids,
                text=text_remove_user,
                **common_props
            )

    elif event == GroupsAnalyticsEvent.deleted:
        AnalyticService.groups_deleted(
            text=base_text,
            **common_props)
