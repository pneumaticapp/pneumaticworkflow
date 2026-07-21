import pytest
from drf_spectacular.utils import OpenApiExample

from src.openapi.entities import PermissionDoc
from src.openapi.helpers import (
    access_description,
    error_response,
    with_access_text,
)
from src.openapi.responses import DetailErrorSerializer


def test_access_description__single_key__ok():
    # arrange
    key = 'IsAuthenticated'

    # act
    result = access_description(key)

    # assert
    assert '## Access' in result
    assert (
        f'- {PermissionDoc.IsAuthenticated}' in result
    )


def test_access_description__multiple_keys__ok():
    # arrange
    key_1 = 'UserIsAuthenticated'
    key_2 = 'BillingPlanPermission'

    # act
    result = access_description(key_1, key_2)

    # assert
    assert (
        f'- {PermissionDoc.UserIsAuthenticated}'
        in result
    )
    assert (
        f'- {PermissionDoc.BillingPlanPermission}'
        in result
    )


def test_access_description__custom_intro__used():
    # arrange
    intro = 'Custom intro line'

    # act
    result = access_description(
        'IsAuthenticated',
        intro=intro,
    )

    # assert
    assert intro in result


def test_access_description__default_intro__used():
    # arrange
    expected_intro = 'Who can call this endpoint:'

    # act
    result = access_description('IsAuthenticated')

    # assert
    assert expected_intro in result


def test_access_description__unknown_key__raises():
    # arrange
    key = 'NonExistentKey'

    # act
    with pytest.raises(ValueError) as ex:
        access_description(key)

    # assert
    assert key in str(ex.value)


def test_with_access_text__non_empty__prepended():
    # arrange
    description = 'Some endpoint info.'
    access = '## Access\n- Authenticated user'

    # act
    result = with_access_text(description, access)

    # assert
    assert result == f'{description}\n\n{access}'


def test_with_access_text__empty__returns_access():
    # arrange
    access = '## Access\n- Authenticated user'

    # act
    result = with_access_text('', access)

    # assert
    assert result == access


def test_with_access_text__whitespace__returns_access():
    # arrange
    access = '## Access\n- Authenticated user'

    # act
    result = with_access_text('   \n  ', access)

    # assert
    assert result == access


def test_error_response__ok():
    # arrange
    description = 'Unauthorized'
    example = OpenApiExample(
        'Unauthorized',
        value={
            'detail': (
                'Authentication credentials '
                'were not provided.'
            ),
        },
    )

    # act
    result = error_response(
        DetailErrorSerializer,
        description,
        example,
    )

    # assert
    assert result.description == description
    assert result.response is DetailErrorSerializer
    assert result.examples == [example]
