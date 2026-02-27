import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from src.processes.enums import ViewerType
from src.processes.models.templates.viewer import TemplateViewer
from src.processes.tests.fixtures import (
    create_test_account,
    create_test_group,
    create_test_template,
    create_test_user,
)

UserModel = get_user_model()

pytestmark = pytest.mark.django_db


class TestTemplateViewer:

    def test_create_user_viewer__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user)
        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )

        # act
        viewer = TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        # assert
        assert viewer.template == template
        assert viewer.type == ViewerType.USER
        assert viewer.user == viewer_user
        assert viewer.group is None
        assert viewer.account == account
        assert not viewer.is_deleted
        assert viewer.api_name.startswith('viewer')

    def test_create_group_viewer__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user)
        group = create_test_group(account=account, name='Test Group')

        # act
        viewer = TemplateViewer.objects.create(
            template=template,
            type=ViewerType.GROUP,
            group=group,
            account=account,
        )

        # assert
        assert viewer.template == template
        assert viewer.type == ViewerType.GROUP
        assert viewer.user is None
        assert viewer.group == group
        assert viewer.account == account
        assert not viewer.is_deleted
        assert viewer.api_name.startswith('viewer')

    def test_create_duplicate_api_name__constraint_error(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user)
        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )

        # Create first viewer
        TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
            api_name='test_viewer',
        )

        # act & assert
        with pytest.raises(IntegrityError):
            TemplateViewer.objects.create(
                template=template,
                type=ViewerType.USER,
                user=viewer_user,
                account=account,
                api_name='test_viewer',
            )

    def test_soft_delete__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user)
        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )
        viewer = TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        # act
        viewer.delete()

        # assert
        viewer.refresh_from_db()
        assert viewer.is_deleted

    def test_template_viewers_relation__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user)
        viewer_user1 = create_test_user(
            account=account,
            email='viewer1@test.com',
        )
        _viewer_user2 = create_test_user(
            account=account,
            email='viewer2@test.com',
        )
        group = create_test_group(account=account, name='Test Group')

        # act
        user_viewer = TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user1,
            account=account,
        )
        group_viewer = TemplateViewer.objects.create(
            template=template,
            type=ViewerType.GROUP,
            group=group,
            account=account,
        )

        # assert
        viewers = template.viewers.all()
        assert len(viewers) == 2
        assert user_viewer in viewers
        assert group_viewer in viewers

    def test_ordering__ok(self):
        # arrange
        account = create_test_account()
        user = create_test_user(account=account)
        template = create_test_template(user=user)
        viewer_user = create_test_user(
            account=account,
            email='viewer@test.com',
        )
        group = create_test_group(account=account, name='Test Group')

        # act
        group_viewer = TemplateViewer.objects.create(
            template=template,
            type=ViewerType.GROUP,
            group=group,
            account=account,
        )
        user_viewer = TemplateViewer.objects.create(
            template=template,
            type=ViewerType.USER,
            user=viewer_user,
            account=account,
        )

        # assert
        viewers = list(TemplateViewer.objects.all())
        # Ordered by type (group before user alphabetically)
        assert viewers[0] == group_viewer
        assert viewers[1] == user_viewer
