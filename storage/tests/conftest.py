"""Root conftest — registers fixture plugins."""

pytest_plugins = [
    'tests.fixtures.common',
    'tests.fixtures.integration',
    'tests.fixtures.unit',
]
