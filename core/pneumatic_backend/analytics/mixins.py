import analytics
from typing import Optional
from django.conf import settings


class BaseIdentifyMixin:

    @staticmethod
    def identify(
        user,
        invited_from: Optional[str] = None
    ):

        # TODO need mock calls in the tests

        if (
            settings.PROJECT_CONF['ANALYTICS']
            and settings.ANALYTICS_WRITE_KEY
        ):

            if not invited_from and user.invite:
                invited_from = user.invite.invited_from

            props = {
                'unsubscribed': not user.is_newsletters_subscriber,
                'integrations.intercom.unsubscribed': (
                    not user.is_special_offers_subscriber
                ),
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'avatar': user.photo,
                'account_id': user.account_id,
                'company_name': user.account.name,
                'logo_lg': user.account.logo_lg,
                'is_admin': user.is_admin,
                'is_account_owner': user.is_account_owner,
                'phone': user.phone,
                'created_at': user.account.date_joined,
                'invited_from': invited_from,
                'plan': user.account.billing_plan,
                'status': user.status,
                'type': user.type,
                'lease_level': user.account.lease_level,
                'language': user.language,
                'timezone': user.timezone,
            }
            props.update(user.get_account_signup_data().as_dict())
            analytics.debug = settings.ANALYTICS_DEBUG
            analytics.write_key = settings.ANALYTICS_WRITE_KEY
            analytics.identify(user.id, props)

    @staticmethod
    def group(user, account=None):

        # TODO need mock calls in the tests

        if (
            settings.PROJECT_CONF['ANALYTICS']
            and settings.ANALYTICS_WRITE_KEY
        ):

            if account is None:
                account = user.account
            analytics.debug = settings.ANALYTICS_DEBUG
            analytics.write_key = settings.ANALYTICS_WRITE_KEY
            analytics.group(
                user_id=user.id,
                group_id=account.id,
                traits={
                    'name': account.name,
                    'logo_lg': account.logo_lg,
                    'active_users': account.active_users,
                    'tenants_active_users': account.tenants_active_users,
                    'max_users': account.max_users,
                    'plan': account.billing_plan,
                    'billing_plan': account.billing_plan,
                    'lease_level': account.lease_level,
                    'payment_card_provided': account.payment_card_provided
                }
            )
