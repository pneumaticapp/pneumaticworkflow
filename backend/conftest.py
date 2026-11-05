"""Selection and full-suite coverage gate for HTTP contract scenarios."""

import json
from pathlib import Path

import pytest


def pytest_addoption(parser: object) -> None:
    group = parser.getgroup('api-contracts')
    group.addoption('--contract-coverage', action='store_true', default=False)
    group.addoption(
        '--no-contract-coverage', action='store_false',
        dest='contract_coverage',
        help='Disable only the full-suite coverage gate for a focused run.',
    )


def pytest_configure(config: object) -> None:
    config.addinivalue_line(
        'markers',
        'contract_error(method, path): semantic failure with a 2xx/3xx status',
    )
    config.addinivalue_line(
        'markers',
        'contract_success(method, path): verified semantic success for a '
        'token callback which also returns 2xx/3xx on failure',
    )
    path = Path(__file__).parent / 'src/openapi/tests/contract_cases.json'
    manifest = (
        json.loads(path.read_text(encoding='utf-8')) if path.exists()
        else {'cases': []}
    )
    config._api_contract_cases = frozenset(manifest['cases'])


def pytest_collection_modifyitems(config: object, items: list) -> None:
    collected = {item.nodeid for item in items}
    config._api_missing_contract_cases = sorted(
        config._api_contract_cases - collected,
    )


@pytest.fixture(autouse=True)
def selected_contract_scenario(request: object) -> None:
    if request.node.nodeid in request.config._api_contract_cases:
        request.getfixturevalue('validate_http_contracts')


def pytest_sessionfinish(session: object, exitstatus: int) -> None:
    if session.config.getoption('collectonly') or exitstatus in (2, 3, 4):
        return
    contract = getattr(session.config, '_api_http_contract', None)
    if contract is None:
        if session.config.getoption('contract_coverage'):
            session.config._api_contract_failure = (
                'Core contract coverage requires validated HTTP scenarios.'
            )
            session.exitstatus = 1
        return
    from src.openapi.tests.contract_coverage import (  # noqa: PLC0415
        coverage_report,
    )

    report = coverage_report(contract)
    report['missing_selected_cases'] = (
        session.config._api_missing_contract_cases
    )
    session.config.cache.set('api_contracts/core_coverage', report)
    session.config._api_contract_report = report
    if session.config.getoption('contract_coverage') and (
        not report['operation_count'] or report['gaps']
        or report['missing_selected_cases']
    ):
        session.exitstatus = 1


def pytest_terminal_summary(terminalreporter: object) -> None:
    failure = getattr(terminalreporter.config, '_api_contract_failure', None)
    if failure is not None:
        terminalreporter.write_sep('=', failure, red=True)
    report = getattr(terminalreporter.config, '_api_contract_report', None)
    if report is None:
        return
    terminalreporter.write_sep(
        '=',
        f"Core HTTP contracts: {report['covered_operations']}/"
        f"{report['operation_count']} operations; "
        f"{report['paginated_operations']} paginated operations",
    )
    if terminalreporter.config.getoption('contract_coverage'):
        from src.openapi.tests.contract_coverage import (  # noqa: PLC0415
            coverage_errors,
        )
        for message in coverage_errors(report):
            terminalreporter.write_line(message, red=True)
