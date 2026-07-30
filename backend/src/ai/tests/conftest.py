import guardian.management
import pytest
from unittest.mock import Mock

from src.generics.tests.clients import PneumaticApiClient


def pytest_configure(config):
    guardian.management.create_anonymous_user = Mock()


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture(autouse=True)
def immediate_on_commit(mocker):

    """ Dispatch publishes AI runs via transaction.on_commit; test
        transactions never commit, so run callbacks immediately """

    return mocker.patch(
        'src.ai.dispatch.transaction.on_commit',
        side_effect=lambda func, using=None: func(),
    )
