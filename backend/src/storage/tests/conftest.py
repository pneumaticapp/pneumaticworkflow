import pytest
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType

from src.generics.tests.clients import PneumaticApiClient
from src.storage.models import Attachment


@pytest.fixture(autouse=True)
def create_attachment_permissions(db):
    """
    Ensure attachment permissions exist in test database.
    Django creates permissions during migrations, but in tests
    they might not be created automatically.
    """
    content_type = ContentType.objects.get_for_model(Attachment)
    Permission.objects.get_or_create(
        codename='view_attachment',
        name='Can view attachment',
        content_type=content_type,
    )


@pytest.fixture
def api_client():
    return PneumaticApiClient(HTTP_USER_AGENT='Mozilla/5.0')
