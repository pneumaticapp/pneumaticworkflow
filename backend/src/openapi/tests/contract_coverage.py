"""Coverage of validated HTTP exchanges, independent of test file order."""

from collections import defaultdict

METHODS = frozenset({
    'get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace',
})

# These public operations report failure with the same HTTP status as success.
SEMANTIC_ERRORS = frozenset({
    ('/accounts/digest/unsubscribe', 'get'),
    ('/accounts/emails/unsubscribe', 'get'),
    ('/accounts/users/{id}/transfer', 'get'),
})


def coverage_report(contract: object) -> dict:
    observations = defaultdict(list)
    for item in contract.observations:
        observations[item['path'], item['method']].append(item)
    operations = []
    gaps = []
    for path, methods in contract.document['paths'].items():
        for method, operation in methods.items():
            if method not in METHODS:
                continue
            observed = observations[path, method]
            statuses = {item['status'] for item in observed}
            declared = {
                int(code) for code in operation['responses'] if code.isdigit()
            }
            successful = {code for code in declared if 200 <= code < 400}
            missing_success = sorted(successful - statuses)
            missing_error = sorted(
                code for code in declared - statuses if code >= 400
            )
            has_success = any(
                200 <= item['status'] < 400
                and item.get('outcome') == 'success'
                for item in observed
            )
            requires_error = any(code >= 400 for code in declared) or (
                path, method,
            ) in SEMANTIC_ERRORS
            has_error = any(
                item['status'] >= 400 or item.get('outcome') == 'error'
                for item in observed
            )
            pagination = method == 'get' and contract.is_paginated(operation)
            modes = {item['pagination'] for item in observed}
            missing_modes = sorted(
                {'default', 'limit=1'} - modes,
            ) if pagination else []
            entry = {
                'path': path, 'method': method,
                'declared_statuses': sorted(declared),
                'validated_statuses': sorted(statuses),
                'uncovered_statuses': sorted(declared - statuses),
                'missing_success': missing_success, 'has_success': has_success,
                'missing_error': missing_error,
                'requires_error': requires_error, 'has_error': has_error,
                'paginated': pagination, 'missing_modes': missing_modes,
                'cases': sorted({item['case'] for item in observed}),
            }
            operations.append(entry)
            if not has_success or missing_success or missing_error or (
                requires_error and not has_error
            ) or missing_modes:
                gaps.append(entry)
    return {
        'operation_count': len(operations),
        'covered_operations': len(operations) - len(gaps),
        'paginated_operations': sum(item['paginated'] for item in operations),
        'validated_status_pairs': sum(
            len(item['validated_statuses']) for item in operations
        ),
        'declared_status_pairs': sum(
            len(item['declared_statuses']) for item in operations
        ),
        'operations': operations, 'gaps': gaps,
    }


def coverage_errors(report: dict) -> list:
    messages = [
        f"{entry['method'].upper()} {entry['path']}: "
        f"success={entry['has_success']}; "
        f"missing success statuses={entry['missing_success']}; "
        f"missing error statuses={entry['missing_error']}; "
        f"error={entry['requires_error'] and not entry['has_error']}; "
        f"pagination={entry['missing_modes']}"
        for entry in report['gaps']
    ]
    messages.extend(
        f'Selected contract case was not collected: {case}'
        for case in report.get('missing_selected_cases', [])
    )
    if not report.get('operation_count', 1):
        messages.append('Core schema contains no HTTP operations.')
    return messages
