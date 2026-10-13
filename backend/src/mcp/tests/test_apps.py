import os
import subprocess
import sys
from pathlib import Path

import pytest

CONFIG_IMPORT = """
from configurations import importer
from django.apps import apps
importer.install()
import src.mcp.apps
import sys
assert not apps.apps_ready
assert 'src.mcp.models' not in sys.modules
assert 'src.authentication.schema' not in sys.modules
"""

STARTUP = """
from unittest.mock import patch
from configurations import importer
importer.install()
import django
with patch(
    'django.db.backends.base.base.BaseDatabaseWrapper.ensure_connection',
    side_effect=AssertionError('Startup must not connect to the database'),
):
    django.setup()
from django.apps import apps
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from src.authentication.services.mcp_auth import (
    DelegationAuthentication, LoginTokenAuthentication,
)
assert apps.models_ready and apps.ready
assert OpenApiAuthenticationExtension.get_match(
    LoginTokenAuthentication(),
).name == 'mcpLoginToken'
assert OpenApiAuthenticationExtension.get_match(
    DelegationAuthentication(),
).name == 'mcpDelegation'
"""


def run_startup(code: str, enabled: str) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        'DJANGO_SETTINGS_MODULE': 'src.settings',
        'DJANGO_CONFIGURATION': 'Testing',
        'ENVIRONMENT': 'Testing',
        'DJANGO_SECRET_KEY': 'local-import-review-key',
        'FRONTEND_URL': 'http://localhost:3000',
        'FORMS_URL': 'http://localhost:3001',
        'BACKEND_URL': 'http://localhost:8000',
        'MCP_ENABLED': enabled,
        'MCP_PUBLIC_URL': 'https://pneumatic.test/mcp',
        'MCP_ISSUER_URL': 'https://pneumatic.test',
        'MCP_SERVICE_SECRET': 'mcp-test-service-secret-32-characters',
        'MCP_FILE_SERVICE_SECRET': 'mcp-test-file-secret-32-characters',
        'MCP_FILE_SERVICE_URL': 'http://file-service:8000',
        'AUTH_REDIS_URL': '',
    }
    return subprocess.run(
        args=[sys.executable, '-c', code],
        cwd=Path(__file__).resolve().parents[3],
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_app_config__import_before_models__ok():
    # arrange
    code = CONFIG_IMPORT

    # act
    result = run_startup(code=code, enabled='no')

    # assert
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('enabled', ['no', 'yes'])
def test_app_config__cold_start_registers_hooks_without_database__ok(
    enabled: str,
):
    # arrange
    code = STARTUP

    # act
    result = run_startup(code=code, enabled=enabled)

    # assert
    assert result.returncode == 0, result.stderr
