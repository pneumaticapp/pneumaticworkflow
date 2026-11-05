"""Check HTTP contracts alongside the existing API behavior tests."""

from unittest.mock import patch
from typing import Any

from django.db.backends.base.base import BaseDatabaseWrapper
from django.http import HttpResponse
from drf_spectacular.generators import SchemaGenerator
import pytest

from src.generics.tests.clients import PneumaticApiClient
from src.openapi.tests.http_contracts import HttpContract


@pytest.fixture(scope='session')
def http_contract(pytestconfig) -> HttpContract:
    with patch.object(
        BaseDatabaseWrapper, 'ensure_connection',
        side_effect=AssertionError('Schema generation must not query the DB'),
    ):
        document = SchemaGenerator().get_schema(request=None, public=True)
    contract = HttpContract(document)
    pytestconfig._api_http_contract = contract
    return contract


@pytest.fixture
def validate_http_contracts(monkeypatch, http_contract, request) -> None:
    original = PneumaticApiClient.generic
    semantic_errors = frozenset(
        (marker.args[1], marker.args[0])
        for marker in request.node.iter_markers('contract_error')
    )
    semantic_successes = frozenset(
        (marker.args[1], marker.args[0])
        for marker in request.node.iter_markers('contract_success')
    )
    assert not semantic_errors & semantic_successes

    def checked_request(
        client: PneumaticApiClient, method: str, path: str, data: Any = '',
        content_type: str = 'application/octet-stream', secure: bool = False,
        **extra: Any,
    ) -> HttpResponse:
        response = original(
            client, method, path, data=data,
            content_type=content_type, secure=secure, **extra,
        )
        body = data.encode('utf-8') if isinstance(data, str) else data
        http_contract.exchange(
            response, body, case=request.node.nodeid,
            semantic_errors=semantic_errors,
            semantic_successes=semantic_successes,
        )
        return response

    monkeypatch.setattr(PneumaticApiClient, 'generic', checked_request)


@pytest.fixture
def contract_api_client(validate_http_contracts) -> PneumaticApiClient:
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')
