from pytz import timezone
from datetime import datetime, timezone as tz
from django.utils import translation
from django.contrib.auth import get_user_model
from src.generics import messages

UserModel = get_user_model()
date_format = '%Y-%m-%dT%H:%M:%S.%fZ'

month_abbreviation_map = {
    1: messages.MSG_GE_0008,
    2: messages.MSG_GE_0009,
    3: messages.MSG_GE_0010,
    4: messages.MSG_GE_0011,
    5: messages.MSG_GE_0012,
    6: messages.MSG_GE_0013,
    7: messages.MSG_GE_0014,
    8: messages.MSG_GE_0015,
    9: messages.MSG_GE_0016,
    10: messages.MSG_GE_0017,
    11: messages.MSG_GE_0018,
    12: messages.MSG_GE_0019,
}


def date_to_tz(
    date: datetime,
    tz: str,
) -> datetime:
    return date.astimezone(timezone(tz))


def date_to_user_fmt(
    date: datetime,
    user: UserModel,
) -> str:
    local_date = date.astimezone(timezone(user.timezone))
    month = date.strftime('%B')
    month_abbreviation = month_abbreviation_map[local_date.month]
    str_date = local_date.strftime(user.date_fmt)
    with translation.override(user.language):
        return str_date.replace(month, str(month_abbreviation))


def date_tsp_to_user_fmt(
    date_tsp: float,
    user: UserModel,
) -> str:
    utc_date = datetime.fromtimestamp(date_tsp, tz=tz.utc)
    return date_to_user_fmt(date=utc_date, user=user)
