"""Fixtures of the endpoint tests.

Only tests.fixtures.e2e is imported here: tests.fixtures.unit is
already registered as a plugin by the root conftest.
"""

from tests.fixtures.e2e import (  # noqa: F401
    auth_headers,
    e2e_client,
    mock_auth_middleware,
    mock_download_response,
    mock_http_client,
    mock_storage_service,
    mock_upload_response,
)
