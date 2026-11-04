"""OpenAPI imports must be safe before Django settings are configured."""

import os
from pathlib import Path
import subprocess
import sys

from django.apps import apps
from drf_spectacular.extensions import (
    OpenApiAuthenticationExtension,
    OpenApiSerializerFieldExtension,
    OpenApiViewExtension,
)
import pytest


def test_reference__import_without_settings__loads_static_content() -> None:
    # arrange
    environment = os.environ.copy()
    environment.pop('DJANGO_SETTINGS_MODULE', None)
    environment.pop('DJANGO_CONFIGURATION', None)
    backend = Path(__file__).resolve().parents[3]
    script = """
import sys
import src.openapi
assert not any(name.startswith(('django', 'rest_framework', 'drf_spectacular'))
               for name in sys.modules)
from src.openapi.reference import API_DESCRIPTION, HEADER_SECURITY_SCHEMES
assert API_DESCRIPTION and HEADER_SECURITY_SCHEMES
assert not any(name.startswith(('django', 'rest_framework', 'drf_spectacular'))
               for name in sys.modules)
"""

    # act
    result = subprocess.run(
        [sys.executable, '-c', script], cwd=str(backend),
        env=environment, capture_output=True, text=True, timeout=30,
        check=False,
    )

    # assert
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize('extension_base,module', [
    (OpenApiAuthenticationExtension, 'src.openapi.auth_extensions'),
    (OpenApiSerializerFieldExtension, 'src.openapi.field_extensions'),
    (OpenApiViewExtension, 'src.openapi.view_extensions'),
])
def test_django_setup__registers_extensions_once(
    extension_base, module,
) -> None:
    # arrange
    registered = [
        extension for extension in extension_base._registry
        if extension.__module__ == module
    ]

    # act
    apps.get_app_config('openapi').ready()
    current = [
        extension for extension in extension_base._registry
        if extension.__module__ == module
    ]

    # assert
    assert registered
    assert current == registered
