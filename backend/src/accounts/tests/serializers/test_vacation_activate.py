import pytest

from src.accounts.enums import AbsenceStatus
from src.accounts.messages import (
    MSG_A_0049,
    MSG_A_0050,
    MSG_A_0051,
)
from src.accounts.serializers.user import (
    VacationActivateSerializer,
)
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_admin,
    create_test_owner,
)


pytestmark = pytest.mark.django_db


def test_validate__ok():

    """
    Valid data passes validation.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    data = {
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.VACATION,
    }

    # act
    slz = VacationActivateSerializer(
        data=data,
        context={'vacation_user': owner, 'user': owner},
    )

    # assert
    assert slz.is_valid() is True


def test_validate__self_delegation__error():

    """
    Cannot delegate to yourself.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    data = {
        'substitute_user_ids': [owner.id],
        'absence_status': AbsenceStatus.VACATION,
    }

    # act
    slz = VacationActivateSerializer(
        data=data,
        context={'vacation_user': owner, 'user': owner},
    )

    # assert
    assert slz.is_valid() is False
    assert 'substitute_user_ids' in slz.errors
    assert str(MSG_A_0049) in str(
        slz.errors['substitute_user_ids'],
    )


def test_validate__missing_users__error():

    """
    Non-existent users trigger validation error.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    data = {
        'substitute_user_ids': [99999],
        'absence_status': AbsenceStatus.VACATION,
    }

    # act
    slz = VacationActivateSerializer(
        data=data,
        context={'vacation_user': owner, 'user': owner},
    )

    # assert
    assert slz.is_valid() is False
    assert 'substitute_user_ids' in slz.errors
    assert str(MSG_A_0050([99999])) in str(
        slz.errors['substitute_user_ids'],
    )


def test_validate__empty_list__error():

    """
    Empty substitute list triggers validation error.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    data = {
        'substitute_user_ids': [],
        'absence_status': AbsenceStatus.VACATION,
    }

    # act
    slz = VacationActivateSerializer(
        data=data,
        context={'vacation_user': owner, 'user': owner},
    )

    # assert
    assert slz.is_valid() is False
    assert 'substitute_user_ids' in slz.errors
    assert str(MSG_A_0051) in str(
        slz.errors['substitute_user_ids'],
    )


def test_validate__absence_active__error():

    """
    Cannot activate with absence_status=ACTIVE.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    data = {
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.ACTIVE,
    }

    # act
    slz = VacationActivateSerializer(
        data=data,
        context={'vacation_user': owner, 'user': owner},
    )

    # assert
    assert slz.is_valid() is False
    assert 'absence_status' in slz.errors


def test_validate__sick_leave__ok():

    """
    SICK_LEAVE is a valid absence_status.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    data = {
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.SICK_LEAVE,
    }

    # act
    slz = VacationActivateSerializer(
        data=data,
        context={'vacation_user': owner, 'user': owner},
    )

    # assert
    assert slz.is_valid() is True
    assert slz.validated_data['absence_status'] == (
        AbsenceStatus.SICK_LEAVE
    )


def test_validate__default_status__ok():

    """
    Default absence_status is VACATION.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    data = {
        'substitute_user_ids': [substitute.id],
    }

    # act
    slz = VacationActivateSerializer(
        data=data,
        context={'vacation_user': owner, 'user': owner},
    )

    # assert
    assert slz.is_valid() is True
    assert slz.validated_data['absence_status'] == (
        AbsenceStatus.VACATION
    )


def test_validate__multiple_substitutes__ok():

    """
    Multiple valid substitutes pass validation.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    sub1 = create_test_admin(
        account=account,
        email='sub1@pneumatic.app',
    )
    sub2 = create_test_admin(
        account=account,
        email='sub2@pneumatic.app',
    )
    data = {
        'substitute_user_ids': [sub1.id, sub2.id],
    }

    # act
    slz = VacationActivateSerializer(
        data=data,
        context={'vacation_user': owner, 'user': owner},
    )

    # assert
    assert slz.is_valid() is True
    assert set(slz.validated_data['substitute_user_ids']) == {
        sub1.id,
        sub2.id,
    }


def test_validate__vacation_dates__ok():

    """
    vacation_start_date and vacation_end_date pass through.
    """

    # arrange
    account = create_test_account()
    owner = create_test_owner(account=account)
    substitute = create_test_admin(
        account=account,
        email='sub@pneumatic.app',
    )
    data = {
        'substitute_user_ids': [substitute.id],
        'absence_status': AbsenceStatus.VACATION,
        'vacation_start_date': '2026-04-01',
        'vacation_end_date': '2026-04-15',
    }

    # act
    slz = VacationActivateSerializer(
        data=data,
        context={'vacation_user': owner, 'user': owner},
    )

    # assert
    assert slz.is_valid() is True
    assert str(
        slz.validated_data['vacation_start_date'],
    ) == '2026-04-01'
    assert str(
        slz.validated_data['vacation_end_date'],
    ) == '2026-04-15'
