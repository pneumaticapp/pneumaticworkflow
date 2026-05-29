"""Tests for GuestToken mutable default safety."""

from src.shared_kernel.auth.guest_token import GuestToken


def test_payload__two_instances__independent_dicts():

    # arrange
    token_a = GuestToken()
    token_b = GuestToken()

    # act
    token_a.payload['key'] = 'value_a'

    # assert
    assert 'key' not in token_b.payload
    assert token_a.payload is not token_b.payload


def test_payload__default__empty_dict():

    # act
    token = GuestToken()

    # assert
    assert token.payload == {}
    assert isinstance(token.payload, dict)


def test_token__default__none():

    # act
    token = GuestToken()

    # assert
    assert token.token is None


def test_str__no_token__empty_string():

    # act
    result = str(GuestToken())

    # assert
    assert result == ''
