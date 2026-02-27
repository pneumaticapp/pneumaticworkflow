import pytest
from django.contrib.auth import get_user_model

from src.processes.models.templates.starter import TemplateStarter
from src.processes.permissions import TemplateStarterPermission
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_template,
    create_test_user,
)

UserModel = get_user_model()
pytestmark = pytest.mark.django_db


class MockView:
    def __init__(self, template_id):
        self.kwargs = {'pk': template_id}


class MockRequest:
    def __init__(self, user):
        self.user = user


class TestTemplateStarterPermission:

    def test_has_permission__account_owner__ok(self):
        # arrange
        account = create_test_account()
        account_owner = create_test_user(
            account=account,
            is_account_owner=True,
        )
        template_owner = create_test_user(
            account=account,
            email='owner@test.com',
            is_admin=True,
        )
        template = create_test_template(template_owner)

        permission = TemplateStarterPermission()
        request = MockRequest(account_owner)
        view = MockView(template.id)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_starter__ok(self):
        # arrange
        account = create_test_account()
        starter_user = create_test_user(
            account=account,
            email='starter@test.com',
        )
        template_owner = create_test_user(
            account=account,
            email='owner@test.com',
            is_admin=True,
        )
        template = create_test_template(template_owner)

        # Add user as starter
        TemplateStarter.objects.create(
            template=template,
            type='user',
            user=starter_user,
            account=account,
        )

        permission = TemplateStarterPermission()
        request = MockRequest(starter_user)
        view = MockView(template.id)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_owner__ok(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(
            account=account,
            is_admin=True,
        )
        template = create_test_template(template_owner)

        permission = TemplateStarterPermission()
        request = MockRequest(template_owner)
        view = MockView(template.id)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__no_access__forbidden(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(
            account=account,
            is_admin=True,
        )
        template = create_test_template(template_owner)
        random_user = create_test_user(
            account=account,
            email='random@test.com',
            is_admin=False,
            is_account_owner=False,
        )

        permission = TemplateStarterPermission()
        request = MockRequest(random_user)
        view = MockView(template.id)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__invalid_template_id__forbidden(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)

        permission = TemplateStarterPermission()
        request = MockRequest(user)
        view = MockView('invalid')

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__nonexistent_template__forbidden(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)

        permission = TemplateStarterPermission()
        request = MockRequest(user)
        view = MockView(99999)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False
