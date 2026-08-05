from src.openapi.auth_extensions import PneumaticTokenScheme


def test_get_security_definition__ok(mocker):
    # arrange
    expected = {
        'type': 'http',
        'scheme': 'bearer',
    }
    build_mock = mocker.patch(
        'src.openapi.auth_extensions'
        '.build_bearer_security_scheme_object',
        return_value=expected,
    )
    extension = object.__new__(PneumaticTokenScheme)

    # act
    result = extension.get_security_definition(None)

    # assert
    build_mock.assert_called_once_with(
        header_name='HTTP_AUTHORIZATION',
        token_prefix='Bearer',
    )
    assert result is expected
