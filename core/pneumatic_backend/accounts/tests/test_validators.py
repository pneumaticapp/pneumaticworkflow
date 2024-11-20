import pytest
from django.contrib.auth import get_user_model
from pneumatic_backend.accounts.tests.fixtures import (
    create_test_user,
    create_test_workflow,
    create_invited_user,
)
from pneumatic_backend.accounts.validators import (
    user_is_performer,
)


UserModel = get_user_model()


class TestCheckPerformer:

    @pytest.mark.django_db
    def test_user_performer_not_empty(self):
        user = create_test_user()
        create_test_workflow(user.account, user)
        result = user_is_performer(user)
        assert result is True

    @pytest.mark.django_db
    def test_user_performer_empty(self):
        user = create_test_user(is_account_owner=True)
        create_test_workflow(user.account)
        result = user_is_performer(user)
        assert result is False

    @pytest.mark.django_db
    def test_user_performer_other_user(self):
        user = create_test_user()
        invited = create_invited_user(user)
        create_test_workflow(account=user.account, user=user)
        result = user_is_performer(invited)
        assert result is False
