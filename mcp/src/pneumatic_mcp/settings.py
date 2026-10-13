"""Environment configuration, independent of Django and storage settings."""

import json
from typing import Annotated, Any
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from pneumatic_mcp.files import validate_file_path

READ_SCOPE = "pneumatic:read"
WRITE_SCOPE = "pneumatic:write"
FILES_READ_SCOPE = "files:read"
FILES_WRITE_SCOPE = "files:write"
SCOPE_ORDER = (
    READ_SCOPE,
    WRITE_SCOPE,
    FILES_READ_SCOPE,
    FILES_WRITE_SCOPE,
)
SCOPES = frozenset(SCOPE_ORDER)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="MCP_", extra="ignore", hide_input_in_errors=True
    )

    enabled: bool = False
    public_url: str = "https://my.pneumatic.app/mcp"
    issuer_url: str = "https://my.pneumatic.app"
    backend_url: str = "http://pneumatic-nginx/"
    file_service_url: str = "http://file-service:8000"
    redis_url: SecretStr = SecretStr("redis://redis:6379/5")
    service_secret: SecretStr = SecretStr("")
    port: int = Field(default=8000, ge=1, le=65535)
    allowed_hosts: Annotated[list[str], NoDecode] = Field(default_factory=list)
    allowed_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=list
    )
    connect_timeout: float = Field(default=3, gt=0, le=30)
    read_timeout: float = Field(default=20, gt=0, le=120)
    call_timeout: float = Field(default=30, gt=0, le=180)
    # Uvicorn counts the accepted connection before checking this limit.
    max_concurrency: int = Field(default=32, ge=2, le=512)
    max_request_bytes: int = Field(
        default=256 * 1024, ge=1024, le=4 * 1024 * 1024
    )
    max_response_bytes: int = Field(
        default=2 * 1024 * 1024, ge=1024, le=16 * 1024 * 1024
    )

    @field_validator("enabled", mode="before")
    @classmethod
    def parse_enabled(cls, value: object) -> bool:
        return value is True or value == "yes"

    @field_validator("allowed_hosts", "allowed_origins", mode="before")
    @classmethod
    def parse_allowlist(cls, value: Any) -> Any:
        if isinstance(value, str):
            return (
                json.loads(value)
                if value.startswith("[")
                else value.split(",")
            )
        return value

    @field_validator(
        "public_url", "issuer_url", "backend_url", "file_service_url"
    )
    @classmethod
    def validate_url(cls, value: str) -> str:
        parts = urlsplit(value)
        if (
            parts.scheme not in {"http", "https"}
            or not parts.hostname
            or parts.username
            or parts.password
            or parts.query
            or parts.fragment
            or any(ord(char) < 33 for char in value)
            or (parts.port is not None and not 1 <= parts.port <= 65535)
        ):
            raise ValueError(
                "Expected an HTTP(S) URL without credentials,"
                " query or fragment"
            )
        return value

    @model_validator(mode="after")
    def validate_security(self):
        for value in (self.public_url, self.issuer_url):
            parts = urlsplit(value)
            if parts.scheme != "https" and parts.hostname not in {
                "localhost",
                "127.0.0.1",
                "::1",
            }:
                raise ValueError(
                    "Public resource and issuer URLs require HTTPS"
                )
        if urlsplit(self.public_url).path != "/mcp":
            raise ValueError("MCP_PUBLIC_URL must have exactly the /mcp path")
        public = urlsplit(self.public_url)
        issuer = urlsplit(self.issuer_url)
        if issuer.path or (issuer.scheme, issuer.netloc) != (
            public.scheme,
            public.netloc,
        ):
            raise ValueError(
                "MCP_ISSUER_URL must be the public resource origin"
            )
        if self.enabled and (
            len(self.service_secret.get_secret_value()) < 32
            or not self.service_secret.get_secret_value().strip()
        ):
            raise ValueError(
                "MCP_SERVICE_SECRET must contain at least 32 "
                "characters when enabled"
            )
        for value in self.allowed_hosts + self.allowed_origins:
            if not value or value.strip() != value or "*" in value:
                raise ValueError(
                    "Host and Origin allowlists must contain explicit values"
                )
        return self

    @property
    def hosts(self) -> list[str]:
        return self.allowed_hosts or [urlsplit(self.public_url).netloc]

    @property
    def origins(self) -> list[str]:
        parts = urlsplit(self.public_url)
        return self.allowed_origins or [f"{parts.scheme}://{parts.netloc}"]

    def backend_endpoint(self, path: str) -> str:
        # urljoin(base, '/path') would silently discard an installation's /api/
        # prefix.
        if (
            not path.startswith("/")
            or ".." in path
            or "?" in path
            or "#" in path
        ):
            raise ValueError("Only fixed core API paths may be requested")
        return self.backend_url.rstrip("/") + path

    def file_endpoint(self, path: str) -> str:
        validate_file_path(path=path)
        return self.file_service_url.rstrip("/") + path
