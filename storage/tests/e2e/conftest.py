# Import fixtures from parent conftest
from tests.conftest import (  # noqa: F401
    mock_download_use_case_get_metadata,
    mock_download_use_case_get_stream,
    mock_http_client_check_permission,
)

pytest_plugins = [
    'tests.fixtures.common',
    'tests.fixtures.e2e',
]
