import pytest

from src.ai.services.response import TaskResponseService
from src.processes.enums import FieldType
from src.processes.models.workflows.fields import TaskField
from src.processes.tests.fixtures import (
    create_test_owner,
    create_test_workflow,
)
from src.storage.enums import AccessType, SourceType
from src.storage.services.exceptions import FileUploadException

pytestmark = pytest.mark.django_db


def _create_file_field(user, api_name='report-1'):
    workflow = create_test_workflow(user=user, tasks_count=1)
    task = workflow.tasks.get(number=1)
    task.output.all().delete()
    TaskField.objects.create(
        task=task,
        api_name=api_name,
        name='Report',
        type=FieldType.FILE,
        workflow=workflow,
        account=user.account,
    )
    return task


def _mock_upload(mocker, **kwargs):
    client_class_mock = mocker.patch(
        'src.ai.services.response.FileServiceClient',
    )
    upload_mock = (
        client_class_mock.return_value.upload_file_with_attachment
    )
    if 'side_effect' in kwargs:
        upload_mock.side_effect = kwargs['side_effect']
    else:
        upload_mock.return_value = 'https://files.test.com/f123'
    return client_class_mock, upload_mock


def test_get_fields_values__file_with_filename__ok(mocker):

    # arrange
    user = create_test_owner()
    task = _create_file_field(user=user)
    client_class_mock, upload_mock = _mock_upload(mocker)
    text = (
        '<field api_name="report-1" name="Report" filename="report.csv">\n'
        'a,b\n1,2\n'
        '</field>'
    )
    service = TaskResponseService(task=task, text=text, user=user)

    # act
    result = service.get_fields_values()

    # assert
    assert result == {
        'report-1': ['[report.csv](https://files.test.com/f123)'],
    }
    client_class_mock.assert_called_once_with(user=user)
    upload_mock.assert_called_once_with(
        file_content=b'a,b\n1,2',
        filename='report.csv',
        content_type='text/csv',
        account=task.account,
        source_type=SourceType.TASK,
        access_type=AccessType.RESTRICTED,
    )


def test_get_fields_values__file_without_filename__api_name_txt(mocker):

    # arrange
    user = create_test_owner()
    task = _create_file_field(user=user)
    _, upload_mock = _mock_upload(mocker)
    text = '<field api_name="report-1" name="Report">content</field>'
    service = TaskResponseService(task=task, text=text, user=user)

    # act
    result = service.get_fields_values()

    # assert
    assert result == {
        'report-1': ['[report-1.txt](https://files.test.com/f123)'],
    }
    upload_mock.assert_called_once_with(
        file_content=b'content',
        filename='report-1.txt',
        content_type='text/plain',
        account=task.account,
        source_type=SourceType.TASK,
        access_type=AccessType.RESTRICTED,
    )


def test_get_fields_values__file_name_without_extension__add_txt(mocker):

    # arrange
    user = create_test_owner()
    task = _create_file_field(user=user)
    _, upload_mock = _mock_upload(mocker)
    text = (
        '<field api_name="report-1" name="Report" filename="notes">'
        'content'
        '</field>'
    )
    service = TaskResponseService(task=task, text=text, user=user)

    # act
    result = service.get_fields_values()

    # assert
    assert result == {
        'report-1': ['[notes.txt](https://files.test.com/f123)'],
    }
    upload_mock.assert_called_once_with(
        file_content=b'content',
        filename='notes.txt',
        content_type='text/plain',
        account=task.account,
        source_type=SourceType.TASK,
        access_type=AccessType.RESTRICTED,
    )


def test_get_fields_values__unknown_extension__default_content_type(
    mocker,
):

    # arrange
    user = create_test_owner()
    task = _create_file_field(user=user)
    _, upload_mock = _mock_upload(mocker)
    text = (
        '<field api_name="report-1" name="Report" filename="data.qwerty">'
        'content'
        '</field>'
    )
    service = TaskResponseService(task=task, text=text, user=user)

    # act
    service.get_fields_values()

    # assert
    upload_mock.assert_called_once_with(
        file_content=b'content',
        filename='data.qwerty',
        content_type='text/plain',
        account=task.account,
        source_type=SourceType.TASK,
        access_type=AccessType.RESTRICTED,
    )


def test_get_fields_values__forbidden_chars__removed(mocker):

    # arrange
    user = create_test_owner()
    task = _create_file_field(user=user)
    _, upload_mock = _mock_upload(mocker)
    text = (
        '<field api_name="report-1" name="Report" '
        'filename="[my]/re:po*rt(1).csv">'
        'content'
        '</field>'
    )
    service = TaskResponseService(task=task, text=text, user=user)

    # act
    result = service.get_fields_values()

    # assert
    assert result == {
        'report-1': ['[myreport1.csv](https://files.test.com/f123)'],
    }
    upload_mock.assert_called_once_with(
        file_content=b'content',
        filename='myreport1.csv',
        content_type='text/csv',
        account=task.account,
        source_type=SourceType.TASK,
        access_type=AccessType.RESTRICTED,
    )


def test_get_fields_values__empty_file_tag__skipped(mocker):

    # arrange
    user = create_test_owner()
    task = _create_file_field(user=user)
    client_class_mock, upload_mock = _mock_upload(mocker)
    text = '<field api_name="report-1" name="Report" filename="a.txt"/>'
    service = TaskResponseService(task=task, text=text, user=user)

    # act
    result = service.get_fields_values()

    # assert
    assert result == {'report-1': []}
    client_class_mock.assert_not_called()
    upload_mock.assert_not_called()


def test_get_fields_values__multiple_files__ok(mocker):

    # arrange
    user = create_test_owner()
    task = _create_file_field(user=user)
    _, upload_mock = _mock_upload(
        mocker,
        side_effect=[
            'https://files.test.com/f1',
            'https://files.test.com/f2',
        ],
    )
    text = (
        '<field api_name="report-1" name="Report" filename="a.txt">'
        'first'
        '</field>\n'
        '<field api_name="report-1" name="Report" filename="b.json">'
        '{"b": 2}'
        '</field>'
    )
    service = TaskResponseService(task=task, text=text, user=user)

    # act
    result = service.get_fields_values()

    # assert
    assert result == {
        'report-1': [
            '[a.txt](https://files.test.com/f1)',
            '[b.json](https://files.test.com/f2)',
        ],
    }
    assert upload_mock.call_count == 2


def test_get_fields_values__upload_error__raise_exception(mocker):

    # arrange
    user = create_test_owner()
    task = _create_file_field(user=user)
    _mock_upload(mocker, side_effect=FileUploadException())
    text = (
        '<field api_name="report-1" name="Report" filename="a.txt">'
        'content'
        '</field>'
    )
    service = TaskResponseService(task=task, text=text, user=user)

    # act
    with pytest.raises(FileUploadException):
        service.get_fields_values()
