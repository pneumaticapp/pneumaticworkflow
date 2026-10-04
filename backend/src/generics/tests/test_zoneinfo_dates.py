from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfoNotFoundError

import pytest

from src.utils.dates import date_to_tz

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    argnames=('utc_date', 'hour', 'offset', 'fold'),
    argvalues=(
        (
            datetime(
                year=2026,
                month=3,
                day=8,
                hour=7,
                minute=30,
                tzinfo=UTC,
            ),
            1,
            -6,
            0,
        ),
        (
            datetime(
                year=2026,
                month=3,
                day=8,
                hour=8,
                minute=30,
                tzinfo=UTC,
            ),
            3,
            -5,
            0,
        ),
        (
            datetime(
                year=2026,
                month=11,
                day=1,
                hour=6,
                minute=30,
                tzinfo=UTC,
            ),
            1,
            -5,
            0,
        ),
        (
            datetime(
                year=2026,
                month=11,
                day=1,
                hour=7,
                minute=30,
                tzinfo=UTC,
            ),
            1,
            -6,
            1,
        ),
    ),
)
def test_date_to_tz__dst_transition__instant_preserved(
    utc_date: datetime,
    hour: int,
    offset: int,
    fold: int,
):

    # arrange
    zone = 'US/Central'

    # act
    result = date_to_tz(date=utc_date, tz=zone)

    # assert
    assert result.hour == hour
    assert result.utcoffset() == timedelta(hours=offset)
    assert result.fold == fold
    assert result.timestamp() == utc_date.timestamp()


def test_date_to_tz__unknown_zone__explicit_error():

    # arrange
    date = datetime(
        year=2026,
        month=1,
        day=1,
        tzinfo=UTC,
    )
    zone = 'Unknown/Timezone'

    # act
    with pytest.raises(expected_exception=ZoneInfoNotFoundError) as error:
        date_to_tz(date=date, tz=zone)

    # assert
    assert zone in str(error.value)
