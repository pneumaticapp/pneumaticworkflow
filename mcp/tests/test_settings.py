import pytest
from pydantic import ValidationError

from pneumatic_mcp.settings import Settings


@pytest.mark.parametrize(
    argnames="public_url,issuer_url",
    argvalues=[
        ("https://my.pneumatic.app/mcp", "https://my.pneumatic.app"),
        ("http://localhost:8123/mcp", "http://localhost:8123"),
        ("http://127.0.0.1:8000/mcp", "http://127.0.0.1:8000"),
        ("http://[::1]:8000/mcp", "http://[::1]:8000"),
    ],
)
def test_settings__supported_origins__ok(public_url: str, issuer_url: str):

    # arrange
    expected_host = public_url.removesuffix("/mcp").split("//")[1]

    # act
    settings = Settings(public_url=public_url, issuer_url=issuer_url)

    # assert
    assert settings.public_url == public_url
    assert settings.issuer_url == issuer_url
    assert settings.hosts == [expected_host]
    assert settings.origins == [issuer_url]


@pytest.mark.parametrize(
    argnames="path",
    argvalues=["/prefix/mcp", "/mcp/", "/MCP", "/", ""],
)
def test_settings__wrong_public_path__validation_error(path: str):

    # arrange
    public_url = f"https://my.pneumatic.app{path}"
    message = "Value error, MCP_PUBLIC_URL must have exactly the /mcp path"

    # act
    with pytest.raises(ValidationError) as ex:
        Settings(public_url=public_url)

    # assert
    assert ex.value.errors(include_input=False)[0]["msg"] == message


@pytest.mark.parametrize(
    argnames="issuer_url",
    argvalues=[
        "https://other.pneumatic.app",
        "https://my.pneumatic.app:8443",
        "https://my.pneumatic.app/path",
        "https://my.pneumatic.app/",
        "https://my.pneumatic.app:443",
    ],
)
def test_settings__inconsistent_issuer__validation_error(issuer_url: str):

    # arrange
    message = "Value error, MCP_ISSUER_URL must be the public resource origin"

    # act
    with pytest.raises(ValidationError) as ex:
        Settings(issuer_url=issuer_url)

    # assert
    assert ex.value.errors(include_input=False)[0]["msg"] == message


@pytest.mark.parametrize(
    argnames="url",
    argvalues=[
        "https://my.pneumatic.app:0/mcp",
        "https://my.pneumatic.app:65536/mcp",
        "https://my.pneumatic.app:invalid/mcp",
        "https://my.pneumatic.app/mcp\n",
        "https://my.pneumatic.app/mcp?token=secret",
        "https://my.pneumatic.app/mcp#fragment",
        "https://user:secret@my.pneumatic.app/mcp",
    ],
)
def test_settings__unsafe_public_url__validation_error(url: str):

    # arrange
    field = "public_url"

    # act
    with pytest.raises(ValidationError) as ex:
        Settings(public_url=url)

    # assert
    assert ex.value.errors(include_input=False)[0]["loc"] == (field,)
    assert "secret" not in str(ex.value)


@pytest.mark.parametrize(argnames="secret", argvalues=["", "short", " " * 32])
def test_settings__invalid_enabled_secret__validation_error(secret: str):

    # arrange
    message = (
        "Value error, MCP_SERVICE_SECRET must contain at least 32 "
        "characters when enabled"
    )

    # act
    with pytest.raises(ValidationError) as ex:
        Settings(enabled=True, service_secret=secret)

    # assert
    assert ex.value.errors(include_input=False)[0]["msg"] == message


def test_settings__disabled_defaults__ok():

    # arrange
    public_url = "https://my.pneumatic.app/mcp"

    # act
    settings = Settings()

    # assert
    assert settings.enabled is False
    assert settings.public_url == public_url
    assert settings.port == 8000


@pytest.mark.parametrize(
    argnames="value,expected",
    argvalues=[
        (None, False),
        ("no", False),
        ("yes", True),
        ("", False),
        ("true", False),
        ("unexpected", False),
    ],
)
def test_settings__enabled_env_without_strict_validation__ok(
    monkeypatch: pytest.MonkeyPatch, value: str | None, expected: bool
):
    # arrange
    if value is None:
        monkeypatch.delenv("MCP_ENABLED", raising=False)
    else:
        monkeypatch.setenv("MCP_ENABLED", value)

    # act
    settings = Settings(service_secret="x" * 32)

    # assert
    assert settings.enabled is expected


def test_settings__custom_port__ok():

    # arrange
    port = 8123

    # act
    settings = Settings(port=port)

    # assert
    assert settings.port == port


@pytest.mark.parametrize(argnames="limit", argvalues=[0, 1])
def test_settings__concurrency_rejecting_all_requests__validation_error(
    limit: int,
):

    # arrange
    field = "max_concurrency"

    # act
    with pytest.raises(ValidationError) as ex:
        Settings(max_concurrency=limit)

    # assert
    assert ex.value.errors(include_input=False)[0]["loc"] == (field,)
