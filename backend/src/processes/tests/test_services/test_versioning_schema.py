import pytest
from src.processes.enums import PerformerType
from src.processes.models.templates.raw_performer import RawPerformerTemplate
from src.processes.services.versioning.schemas import (
    RawPerformerTemplateSchemaV1,
)
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_template,
)


pytestmark = pytest.mark.django_db


def test_raw_performer_schema__manager__includes_source_task_api_name():
    """
    RawPerformerTemplateSchemaV1 must serialize source_task_api_name
    so that MANAGER performers preserve their link to the source step
    during process versioning/updates.
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=2)
    task_template_1 = template.tasks.get(number=1)
    task_template_2 = template.tasks.get(number=2)

    raw_performer = RawPerformerTemplate.objects.create(
        template=template,
        task=task_template_2,
        account=user.account,
        type=PerformerType.MANAGER,
        source_task_api_name=task_template_1.api_name,
        api_name='raw-performer-mgr-1',
    )

    # act
    serialized = RawPerformerTemplateSchemaV1(raw_performer).data

    # assert
    assert 'source_task_api_name' in serialized
    assert serialized['source_task_api_name'] == task_template_1.api_name
    assert serialized['type'] == PerformerType.MANAGER


def test_raw_performer_schema__user__source_task_api_name_null():
    """
    USER type has null source_task_api_name — schema serializes it as None.
    """

    # arrange
    user = create_test_owner()
    template = create_test_template(user=user, tasks_count=1)
    task_template = template.tasks.get(number=1)

    raw_performer = RawPerformerTemplate.objects.create(
        template=template,
        task=task_template,
        account=user.account,
        type=PerformerType.USER,
        user=user,
        api_name='raw-performer-usr-1',
    )

    # act
    serialized = RawPerformerTemplateSchemaV1(raw_performer).data

    # assert
    assert serialized['source_task_api_name'] is None
    assert serialized['type'] == PerformerType.USER
