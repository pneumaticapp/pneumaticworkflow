import pytest
from django.contrib.auth import get_user_model
from src.processes.tests.fixtures import (
    create_test_user,
    create_test_template, create_test_account,
)
from src.processes.services.remove_user_from_draft import (
    remove_user_from_draft
)


UserModel = get_user_model()
pytestmark = pytest.mark.django_db


def test_remove_user_from_draft__raw_performer__ok(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user, tasks_count=1)
    template_draft = template.draft
    invalid_draft = {
        "id": 34425,
        "name": "New Template",
        "tasks": [
            {
                "name": "Task 1",
                "number": 1,
                "raw_performers": [
                    {
                        "api_name": 'performer-123',
                        'type': 'user',
                        'source_id': str(user.id)
                    }
                ]
            }
        ],
        "owners": [],
        "kickoff": {
            "id": 35869,
            "fields": [],
            "description": ""
        },
        "is_active": False,
        "is_public": False,
        "public_url": None,
        "updated_by": 8,
        "tasks_count": 0,
        "date_updated": "2022-07-13T14:19:45.475319+00:00",
        "performers_count": 0,
        "public_success_url": None
    }
    template_draft.draft = invalid_draft
    template_draft.save()
    remove_user_mock = mocker.patch(
        'src.processes.services.'
        'remove_user_from_draft.TemplateDraft.remove_user'
    )

    # act
    remove_user_from_draft(
        account_id=user.account_id,
        user_id=user.id
    )

    # assert
    remove_user_mock.assert_called_once_with(user.id)


def test_remove_user_from_draft__owner__ok(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    template = create_test_template(user, tasks_count=1)
    template_draft = template.draft
    invalid_draft = {
        "id": 34425,
        "name": "New Template",
        "tasks": [
            {
                "name": "Task 1",
                "number": 1,
                "raw_performers": []
            }
        ],
        "owners": [
            {
              "api_name": 'owner-123',
              "type": "user",
              "source_id": str(user.id),
            }
        ],
        "kickoff": {
            "id": 35869,
            "fields": [],
            "description": ""
        },
        "is_active": False,
        "is_public": False,
        "public_url": None,
        "updated_by": 8,
        "tasks_count": 0,
        "date_updated": "2022-07-13T14:19:45.475319+00:00",
        "performers_count": 0,
        "public_success_url": None
    }
    template_draft.draft = invalid_draft
    template_draft.save()
    remove_user_mock = mocker.patch(
        'src.processes.services.'
        'remove_user_from_draft.TemplateDraft.remove_user'
    )

    # act
    remove_user_from_draft(
        account_id=user.account_id,
        user_id=user.id
    )

    # assert
    remove_user_mock.assert_called_once_with(user.id)


def test_remove_user_from_draft__tasks_null__not_found(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user, tasks_count=1)
    template_draft = template.draft
    invalid_draft = {
        "id": 34425,
        "name": "New Template",
        "tasks": None,
        "owners": [],
        "kickoff": {
            "id": 35869,
            "fields": [],
            "description": ""
        },
        "is_active": False,
        "is_public": False,
        "public_url": None,
        "updated_by": 8,
        "tasks_count": 0,
        "date_updated": "2022-07-13T14:19:45.475319+00:00",
        "performers_count": 0,
        "public_success_url": None
    }
    template_draft.draft = invalid_draft
    template_draft.save()
    remove_user_mock = mocker.patch(
        'src.processes.services.'
        'remove_user_from_draft.TemplateDraft.remove_user'
    )

    # act
    remove_user_from_draft(
        account_id=user.account_id,
        user_id=user.id
    )

    # assert
    remove_user_mock.assert_not_called()


def test_remove_user_from_draft__not_tasks__not_found(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user, tasks_count=1)
    template_draft = template.draft
    invalid_draft = {
        "id": 34425,
        "name": "New Template",
        "owners": [],
        "kickoff": {
            "id": 35869,
            "fields": [],
            "description": ""
        },
        "is_active": False,
        "is_public": False,
        "public_url": None,
        "updated_by": 8,
        "tasks_count": 0,
        "date_updated": "2022-07-13T14:19:45.475319+00:00",
        "performers_count": 0,
        "public_success_url": None
    }
    template_draft.draft = invalid_draft
    template_draft.save()
    remove_user_mock = mocker.patch(
        'src.processes.services.'
        'remove_user_from_draft.TemplateDraft.remove_user'
    )

    # act
    remove_user_from_draft(
        account_id=user.account_id,
        user_id=user.id
    )

    # assert
    remove_user_mock.assert_not_called()


def test_remove_user_from_draft__owners_null__not_found(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user, tasks_count=1)
    template_draft = template.draft
    invalid_draft = {
        "id": 34425,
        "name": "New Template",
        "tasks": [],
        "owners": None,
        "kickoff": {
            "id": 35869,
            "fields": [],
            "description": ""
        },
        "is_active": False,
        "is_public": False,
        "public_url": None,
        "updated_by": 8,
        "tasks_count": 0,
        "date_updated": "2022-07-13T14:19:45.475319+00:00",
        "performers_count": 0,
        "public_success_url": None
    }
    template_draft.draft = invalid_draft
    template_draft.save()
    remove_user_mock = mocker.patch(
        'src.processes.services.'
        'remove_user_from_draft.TemplateDraft.remove_user'
    )

    # act
    remove_user_from_draft(
        account_id=user.account_id,
        user_id=user.id
    )

    # assert
    remove_user_mock.assert_not_called()


def test_remove_user_from_draft__not_owners__not_found(mocker):

    # arrange
    account = create_test_account()
    user = create_test_user(account=account)
    user_2 = create_test_user(
        account=account,
        is_account_owner=False,
        email='user2@test.test'
    )
    template = create_test_template(user, tasks_count=1)
    template_draft = template.draft
    invalid_draft = {
        "id": 34425,
        "name": "New Template",
        "tasks": [
            {
                "name": "Task 1",
                "number": 1,
                "raw_performers": [
                    {
                        "api_name": 'performer-123',
                        'type': 'user',
                        'source_id': user_2.id
                    }
                ]
            }
        ],
        "kickoff": {
            "id": 35869,
            "fields": [],
            "description": ""
        },
        "is_active": False,
        "is_public": False,
        "public_url": None,
        "updated_by": 8,
        "tasks_count": 0,
        "date_updated": "2022-07-13T14:19:45.475319+00:00",
        "performers_count": 0,
        "public_success_url": None
    }
    template_draft.draft = invalid_draft
    template_draft.save()
    remove_user_mock = mocker.patch(
        'src.processes.services.'
        'remove_user_from_draft.TemplateDraft.remove_user'
    )

    # act
    remove_user_from_draft(
        account_id=user.account_id,
        user_id=user.id
    )

    # assert
    remove_user_mock.assert_not_called()


def test_remove_user_from_draft__draft_null__not_found(mocker):

    # arrange
    user = create_test_user()
    template = create_test_template(user, tasks_count=1)
    template_draft = template.draft

    template_draft.draft = None
    template_draft.save()
    remove_user_mock = mocker.patch(
        'src.processes.services.'
        'remove_user_from_draft.TemplateDraft.remove_user'
    )

    # act
    remove_user_from_draft(
        account_id=user.account_id,
        user_id=user.id
    )

    # assert
    remove_user_mock.assert_not_called()
