"""Tests for GuestToken mutable default safety."""

from src.shared_kernel.auth.guest_token import GuestToken


class TestGuestTokenDefaults:
    """Test GuestToken default_factory for payload."""

    def test_payload__two_instances__independent_dicts(self):
        """Two GuestToken instances do not share payload dict."""
        # arrange
        token_a = GuestToken()
        token_b = GuestToken()

        # act
        token_a.payload['key'] = 'value_a'

        # assert — token_b must NOT have the key
        assert 'key' not in token_b.payload
        assert token_a.payload is not token_b.payload

    def test_payload__default__empty_dict(self):
        """Default payload is an empty dict."""
        # act
        token = GuestToken()

        # assert
        assert token.payload == {}
        assert isinstance(token.payload, dict)

    def test_token__default__none(self):
        """Default token is None."""
        # act
        token = GuestToken()

        # assert
        assert token.token is None

    def test_str__no_token__empty_string(self):
        """String representation with no token is empty."""
        # act & assert
        assert str(GuestToken()) == ''
