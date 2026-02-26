import guardian.management
import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from src.storage.models import Attachment
from unittest.mock import Mock

from src.generics.tests.clients import PneumaticApiClient


def pytest_configure(config):
    guardian.management.create_anonymous_user = Mock()


@pytest.fixture(autouse=True)
def create_attachment_permissions(db):
    """
    Ensure attachment permissions exist in test database.
    Django creates permissions during migrations, but in tests
    they might not be created automatically.
    """
    content_type = ContentType.objects.get_for_model(Attachment)
    Permission.objects.get_or_create(
        codename='access_attachment',
        name='Can access attachment',
        content_type=content_type,
    )


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')


@pytest.fixture
def analysis_mock(mocker):
    return mocker.patch(
        'src.processes.views.workflow.AnalyticService',
    )
