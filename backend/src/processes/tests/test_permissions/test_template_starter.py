import pytest
from django.contrib.auth import get_user_model

from src.processes.enums import OwnerRole, OwnerType
from src.processes.models.templates.owner import TemplateOwner
from src.processes.permissions import TemplateAccessPermission
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
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


class TestTemplateAccessPermission:

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

        permission = TemplateAccessPermission()
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
        TemplateOwner.objects.create(
            role=OwnerRole.STARTER,
            template=template,
            type=OwnerType.USER,
            user=starter_user,
            account=account,
        )

        permission = TemplateAccessPermission()
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

        permission = TemplateAccessPermission()
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

        permission = TemplateAccessPermission()
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

        permission = TemplateAccessPermission()
        request = MockRequest(user)
        view = MockView('invalid')

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__nonexistent_template__forbidden(self):
        # arrange
        account = create_test_account()
        user = create_test_user(
            account=account,
            is_account_owner=False,
            is_admin=False,
        )

        permission = TemplateAccessPermission()
        request = MockRequest(user)
        view = MockView(99999)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False

    def test_has_permission__template_viewer_user__ok(self):
        # arrange
        account = create_test_account()
        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        template_owner = create_test_user(
            account=account,
            email='owner@test.com',
            is_admin=True,
        )
        template = create_test_template(template_owner)

        TemplateOwner.objects.create(
            role=OwnerRole.VIEWER,
            template=template,
            type=OwnerType.USER,
            user=viewer_user,
            account=account,
        )

        permission = TemplateAccessPermission()
        request = MockRequest(viewer_user)
        view = MockView(template.id)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_viewer_group__ok(self):
        # arrange
        account = create_test_account()
        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        template_owner = create_test_user(
            account=account,
            email='owner@test.com',
            is_admin=True,
        )
        template = create_test_template(template_owner)
        group = create_test_group(account=account, name='Viewers Group')
        group.users.add(viewer_user)

        TemplateOwner.objects.create(
            role=OwnerRole.VIEWER,
            template=template,
            type=OwnerType.GROUP,
            group=group,
            account=account,
        )

        permission = TemplateAccessPermission()
        request = MockRequest(viewer_user)
        view = MockView(template.id)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_starter_group__ok(self):
        # arrange
        account = create_test_account()
        starter_user = create_test_user(
            account=account,
            email='starter@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        template_owner = create_test_user(
            account=account,
            email='owner@test.com',
            is_admin=True,
        )
        template = create_test_template(template_owner)
        group = create_test_group(account=account, name='Starters Group')
        group.users.add(starter_user)

        TemplateOwner.objects.create(
            role=OwnerRole.STARTER,
            template=template,
            type=OwnerType.GROUP,
            group=group,
            account=account,
        )

        permission = TemplateAccessPermission()
        request = MockRequest(starter_user)
        view = MockView(template.id)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__template_owner_group__ok(self):
        # arrange
        account = create_test_account()
        group_member = create_test_user(
            account=account,
            email='member@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        template_owner = create_test_user(
            account=account,
            email='owner@test.com',
            is_admin=True,
        )
        template = create_test_template(template_owner)
        group = create_test_group(account=account, name='Owners Group')
        group.users.add(group_member)

        TemplateOwner.objects.create(
            role=OwnerRole.OWNER,
            template=template,
            type=OwnerType.GROUP,
            group=group,
            account=account,
        )

        permission = TemplateAccessPermission()
        request = MockRequest(group_member)
        view = MockView(template.id)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is True

    def test_has_permission__deleted_owner__forbidden(self):
        # arrange
        account = create_test_account()
        template_owner = create_test_user(
            account=account,
            email='owner@test.com',
            is_admin=True,
        )
        template = create_test_template(template_owner)
        ex_user = create_test_user(
            account=account,
            email='ex_user@test.com',
            is_admin=False,
            is_account_owner=False,
        )
        TemplateOwner.objects.create(
            role=OwnerRole.STARTER,
            template=template,
            type=OwnerType.USER,
            user=ex_user,
            account=account,
            is_deleted=True,
        )

        permission = TemplateAccessPermission()
        request = MockRequest(ex_user)
        view = MockView(template.id)

        # act
        result = permission.has_permission(request, view)

        # assert
        assert result is False
