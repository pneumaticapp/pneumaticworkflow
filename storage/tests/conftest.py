"""Root conftest — registers fixture plugins."""

import os

os.environ['DEBUG'] = 'True'

pytest_plugins = [
    'tests.fixtures.common',
    'tests.fixtures.integration',
    'tests.fixtures.unit',
]
