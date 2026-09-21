import pytest

from src.authentication.enums import AuthTokenType
from src.processes.models.templates.system_template import SystemTemplate
from src.processes.services.system_template import SystemTemplateService
from src.processes.tests.fixtures import create_test_owner

pytestmark = pytest.mark.django_db


def test_import_library_templates__two__emit_library_templates_imported(
    mocker,
):

    # arrange
    user = create_test_owner(is_staff=True)
    auth_type = AuthTokenType.API
    service = SystemTemplateService(
        user=user,
        auth_type=auth_type,
    )
    data = [
        {
            'name': 'Performance Appraisal',
            'description': 'The performance appraisal process',
            'category': 'Human Resources',
            'kickoff': {},
            'tasks': [{'number': 1, 'name': 'Establish standards'}],
        },
        {
            'name': 'Vendor Onboarding',
            'description': 'The vendor onboarding process',
            'category': 'Procurement',
            'kickoff': {},
            'tasks': [{'number': 1, 'name': 'Collect documents'}],
        },
    ]
    library_templates_imported_mock = mocker.patch(
        'src.processes.services.system_template.'
        'AuditEventService.library_templates_imported',
    )

    # act
    service.import_library_templates(data=data)

    # assert
    assert SystemTemplate.objects.count() == 2
    library_templates_imported_mock.assert_called_once_with(
        user=user,
        auth_type=auth_type,
        templates_count=2,
    )
