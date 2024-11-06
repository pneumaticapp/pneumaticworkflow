import pytest

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.accounts.messages import MSG_A_0004
from pneumatic_backend.accounts.tests.fixtures import (
    create_invited_user,
    create_test_account,
    create_test_owner,
    create_test_user
)
from pneumatic_backend.processes.enums import FieldType, PredicateOperator
from pneumatic_backend.processes.models import (
    Condition,
    ConditionTemplate,
    FieldTemplate,
    Predicate,
    PredicateTemplate,
    Rule,
    RuleTemplate
)
from pneumatic_backend.processes.tests.fixtures import (
    create_test_template,
    create_test_workflow
)
from pneumatic_backend.utils.validation import ErrorCode

pytestmark = pytest.mark.django_db


def test_reassign__count_workflows__ok(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    create_test_template(
        user=old_user,
        is_active=True
    )
    create_test_workflow(old_user)
    create_test_workflow(user)
    deleted_template = create_test_template(
        user=old_user,
        is_active=True
    )
    api_client.token_authenticate(user)
    api_client.delete(f'/templates/{deleted_template.id}')

    api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # act
    response = api_client.get(
        f'/accounts/users/{new_user.id}/count-workflows',
    )

    # assert
    assert response.status_code == 200
    assert response.data['count'] == 3


def test_reassign__workflow__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=old_user,
        is_active=True,
    )
    workflow = create_test_workflow(
        template=template,
        user=old_user,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )
    workflow.refresh_from_db()
    task = workflow.tasks.get(number=1)
    members = workflow.members.all()

    # assert
    assert response.status_code == 204
    assert members.count() == 1
    assert members.first() == new_user
    assert task.raw_performers.count() == 1
    assert task.raw_performers.count()
    assert task.raw_performers.first().user == new_user
    assert task.performers.count() == 1
    assert task.performers.first() == new_user


def test_reassign__workflow_already_assigned__ok(
    api_client
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=old_user,
        is_active=True
    )
    task_template = template.tasks.get(number=1)
    task_template.add_raw_performer(new_user)
    workflow = create_test_workflow(
        template=template,
        user=old_user,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )
    workflow.refresh_from_db()
    task = workflow.tasks.get(number=1)
    members = workflow.members.all()

    # assert
    assert response.status_code == 204
    assert members.count() == 1
    assert members.first() == new_user
    assert task.raw_performers.count() == 1
    assert task.raw_performers.count()
    assert task.raw_performers.first().user == new_user
    assert task.performers.count() == 1
    assert task.performers.first() == new_user


def test_reassign__template__ok(
    api_client,
):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=old_user,
        is_active=True,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )
    template.refresh_from_db()
    template_task = template.tasks.get(number=1)

    # assert
    assert response.status_code == 204
    assert template.template_owners.count() == 1
    assert template.template_owners.first() == new_user
    assert template_task.raw_performers.count() == 1
    assert template_task.raw_performers.first().user == new_user


def test_reassign_template__already_assigned__ok(
    api_client,
):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=old_user,
        is_active=True,
    )
    template.template_owners.add(new_user)
    template_task = template.tasks.get(number=1)
    template_task.add_raw_performer(new_user)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )
    template_task = template.tasks.get(number=1)

    # assert
    assert response.status_code == 204
    assert template.template_owners.count() == 1
    assert template.template_owners.first() == new_user
    assert template_task.raw_performers.count() == 1
    assert template_task.raw_performers.first().user == new_user


def test_reassign__new_user_from_another_acc__validation_error(
    mocker,
    api_client,
):
    # arrange
    account_owner = create_test_owner()
    user = create_invited_user(account_owner)
    another_account_user = create_test_user(
        email='newuser@pneumatic.app'
    )
    api_client.token_authenticate(account_owner)
    service_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.'
        'ReassignService.reassign_everywhere'
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': user.id,
            'new_user': another_account_user.id,
        }
    )

    # assert
    message = (
        'Invalid pk "%s" - object does not exist.'
        % another_account_user.id
    )
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'new_user'
    assert response.data['details']['reason'] == message
    service_mock.assert_not_called()


def test_reassign__old_user_from_another_acc__validation_error(
    mocker,
    api_client,
):
    # arrange
    account_owner = create_test_owner()
    user = create_invited_user(account_owner)
    another_account_user = create_test_user(
        email='newuser@pneumatic.app'
    )
    service_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.'
        'ReassignService.reassign_everywhere'
    )
    api_client.token_authenticate(account_owner)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': another_account_user.id,
            'new_user': user.id,
        }
    )

    # assert
    message = (
        'Invalid pk "%s" - object does not exist.'
        % another_account_user.id
    )
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'old_user'
    assert response.data['details']['reason'] == message
    service_mock.assert_not_called()


def test_reassign__to_the_same_user__validation_error(
    mocker,
    api_client,
):
    # arrange
    user = create_test_owner()
    old_user = create_invited_user(user)
    create_test_template(
        user=old_user,
        is_active=True,
    )
    create_test_workflow(old_user)
    create_test_workflow(user)
    service_mock = mocker.patch(
        'pneumatic_backend.accounts.views.users.'
        'ReassignService.reassign_everywhere'
    )
    api_client.token_authenticate(user)

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': old_user.id,
        }
    )

    # assert
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == MSG_A_0004
    service_mock.assert_not_called()


def test_reassign__condition_template__ok(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    output_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        kickoff=template.kickoff_instance,
        template=template,
    )
    task_template_1 = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=task_template_1,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule_1 = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_1,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field=output_field.api_name,
        value=old_user.id,
        template=template,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    template.refresh_from_db()
    assert response.status_code == 204
    assert template.predicates.count() == 1
    assert template.predicates.first().value == str(new_user.id)


def test_reassign__new_user_is_used_in_condition_template___ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    output_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        kickoff=template.kickoff_instance,
        template=template,
    )
    task_template_1 = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=task_template_1,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule_1 = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_1,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field=output_field.api_name,
        value=old_user.id,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_1,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field=output_field.api_name,
        value=new_user.id,
        template=template,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    template.refresh_from_db()
    assert response.status_code == 204
    assert template.predicates.count() == 1
    assert template.predicates.first().value == str(new_user.id)


def test_reassign__new_user_from_another_condition_template__ok(
    api_client
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    output_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        kickoff=template.kickoff_instance,
        template=template,
    )
    task_template_1 = template.tasks.get(number=1)
    task_template_2 = template.tasks.get(number=2)
    condition_template_1 = ConditionTemplate.objects.create(
        task=task_template_1,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    condition_template_2 = ConditionTemplate.objects.create(
        task=task_template_2,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule_1 = RuleTemplate.objects.create(
        condition=condition_template_1,
        template=template,
    )
    rule_2 = RuleTemplate.objects.create(
        condition=condition_template_2,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_1,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field=output_field.api_name,
        value=old_user.id,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule_2,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field=output_field.api_name,
        value=new_user.id,
        template=template,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    template.refresh_from_db()
    rule_1.refresh_from_db()
    rule_2.refresh_from_db()
    assert response.status_code == 204
    assert template.predicates.count() == 2
    assert rule_1.predicates.count() == 1
    assert rule_1.predicates.first().value == str(new_user.id)
    assert rule_2.predicates.count() == 1
    assert rule_2.predicates.first().value == str(new_user.id)


def test_reassign__another_operator_in_condition_template__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')

    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    output_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        kickoff=template.kickoff_instance,
        template=template,
    )
    task_template = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=task_template,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    predicate_1 = PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field=output_field.api_name,
        value=old_user.id,
        template=template,
    )
    predicate_2 = PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=FieldType.USER,
        field=output_field.api_name,
        value=new_user.id,
        template=template,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    template.refresh_from_db()
    predicate_1.refresh_from_db()
    predicate_2.refresh_from_db()
    assert response.status_code == 204
    assert template.predicates.count() == 2
    assert predicate_1.value == str(new_user.id)
    assert predicate_2.value == str(new_user.id)


def test_reassign__user_another_acc_in_condition_template__validation_error(
    api_client
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    old_user = create_invited_user(user)
    account_2 = create_test_account(name='Test', plan=BillingPlanType.PREMIUM)
    new_user = create_test_user(email='test2@penumatic.app', account=account_2)
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    output_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        kickoff=template.kickoff_instance,
        template=template,
    )
    task_template = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=task_template,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field=output_field.api_name,
        value=old_user.id,
        template=template,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    message = f'Invalid pk "{new_user.id}" - object does not exist.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'new_user'
    assert response.data['details']['reason'] == message


def test_reassign__another_field_type_in_condition_template__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    output_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        kickoff=template.kickoff_instance,
        template=template,
    )
    task_template = template.tasks.get(number=1)
    condition_template = ConditionTemplate.objects.create(
        task=task_template,
        action=ConditionTemplate.SKIP_TASK,
        order=0,
        template=template,
    )
    rule = RuleTemplate.objects.create(
        condition=condition_template,
        template=template,
    )
    predicate = PredicateTemplate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.TEXT,
        field=output_field.api_name,
        value=old_user.id,
        template=template,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    template.refresh_from_db()
    predicate.refresh_from_db()
    assert response.status_code == 204
    assert template.predicates.count() == 1
    assert predicate.value == str(old_user.id)


def test_reassign__condition__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=old_user,
        is_active=True,
    )
    workflow = create_test_workflow(
        template=template,
        user=old_user,
    )
    first_task = workflow.tasks.first()
    condition = Condition.objects.create(
        task=first_task,
        action=Condition.SKIP_TASK,
        order=1,
        template_id=template.id,
    )
    first_rule = Rule.objects.create(
        condition=condition,
        template_id=template.id,
    )
    predicate = Predicate.objects.create(
        rule=first_rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field='hero-1',
        value=old_user.id,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    predicate.refresh_from_db()
    assert response.status_code == 204
    assert predicate.value == str(new_user.id)


def test_reassign__new_user_is_used_in_condition__ok(api_client):
    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=old_user,
        is_active=True,
    )
    workflow = create_test_workflow(
        template=template,
        user=old_user,
    )
    first_task = workflow.tasks.first()
    condition = Condition.objects.create(
        task=first_task,
        action=Condition.SKIP_TASK,
        order=1,
        template_id=template.id,
    )
    first_rule = Rule.objects.create(
        condition=condition,
        template_id=template.id,
    )
    Predicate.objects.create(
        rule=first_rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field='hero-1',
        value=old_user.id,
        template_id=template.id,
    )
    Predicate.objects.create(
        rule=first_rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field='hero-1',
        value=new_user.id,
        template_id=template.id,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    first_rule.refresh_from_db()
    assert response.status_code == 204
    assert first_rule.predicates.count() == 1
    assert first_rule.predicates.first().value == str(new_user.id)


def test_reassign__new_user_from_another_conditions__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=old_user,
        is_active=True,
    )
    workflow = create_test_workflow(
        template=template,
        user=old_user,
    )
    task_1 = workflow.tasks.get(number=1)
    task_2 = workflow.tasks.get(number=2)
    condition_1 = Condition.objects.create(
        task=task_1,
        action=Condition.SKIP_TASK,
        order=1,
        template_id=template.id,
    )
    condition_2 = Condition.objects.create(
        task=task_2,
        action=Condition.SKIP_TASK,
        order=1,
        template_id=template.id,
    )
    rule_1 = Rule.objects.create(
        condition=condition_1,
        template_id=template.id,
    )
    rule_2 = Rule.objects.create(
        condition=condition_2,
        template_id=template.id,
    )
    Predicate.objects.create(
        rule=rule_1,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field='hero-1',
        value=old_user.id,
    )
    Predicate.objects.create(
        rule=rule_2,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field='hero-1',
        value=old_user.id,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    template.refresh_from_db()
    rule_1.refresh_from_db()
    rule_2.refresh_from_db()
    assert response.status_code == 204
    assert rule_1.predicates.count() == 1
    assert rule_1.predicates.first().value == str(new_user.id)
    assert rule_2.predicates.count() == 1
    assert rule_2.predicates.first().value == str(new_user.id)


def test_reassign__another_operator_in_condition__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)
    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=user,
        is_active=True,
    )
    workflow = create_test_workflow(
        template=template,
        user=old_user,
    )
    first_task = workflow.tasks.first()
    condition = Condition.objects.create(
        task=first_task,
        action=Condition.SKIP_TASK,
        order=1,
        template_id=template.id,
    )
    rule = Rule.objects.create(
        condition=condition,
        template_id=template.id,
    )
    predicate_1 = Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field='hero-1',
        value=old_user.id,
    )
    predicate_2 = Predicate.objects.create(
        rule=rule,
        operator=PredicateOperator.NOT_EQUAL,
        field_type=FieldType.USER,
        field='hero-1',
        value=old_user.id,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    rule.refresh_from_db()
    predicate_1.refresh_from_db()
    predicate_2.refresh_from_db()
    assert response.status_code == 204
    assert rule.predicates.count() == 2
    assert predicate_1.value == str(new_user.id)
    assert predicate_2.value == str(new_user.id)


def test_reassign__user_another_account_in_condition__validation_error(
    api_client
):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    old_user = create_invited_user(user)
    account_2 = create_test_account(name='Test', plan=BillingPlanType.PREMIUM)
    new_user = create_test_user(email='test2@penumatic.app', account=account_2)
    api_client.token_authenticate(user)
    template = create_test_template(
        user=user,
        is_active=True,
        tasks_count=2
    )
    workflow = create_test_workflow(
        template=template,
        user=old_user,
    )
    first_task = workflow.tasks.first()
    condition = Condition.objects.create(
        task=first_task,
        action=Condition.SKIP_TASK,
        order=1,
        template_id=template.id,
    )
    first_rule = Rule.objects.create(
        condition=condition,
        template_id=template.id,
    )
    Predicate.objects.create(
        rule=first_rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.USER,
        field='hero-1',
        value=old_user.id,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    message = f'Invalid pk "{new_user.id}" - object does not exist.'
    assert response.status_code == 400
    assert response.data['code'] == ErrorCode.VALIDATION_ERROR
    assert response.data['message'] == message
    assert response.data['details']['name'] == 'new_user'
    assert response.data['details']['reason'] == message


def test_reassign__another_field_type_in_condition__ok(api_client):

    # arrange
    account = create_test_account(plan=BillingPlanType.PREMIUM)
    user = create_test_owner(account=account)
    api_client.token_authenticate(user)

    old_user = create_invited_user(user)
    new_user = create_invited_user(user, email='newuser@pneumatic.app')
    template = create_test_template(
        user=user,
        is_active=True,
    )
    workflow = create_test_workflow(
        template=template,
        user=old_user,
    )
    first_task = workflow.tasks.first()
    condition = Condition.objects.create(
        task=first_task,
        action=Condition.SKIP_TASK,
        order=1,
        template_id=template.id,
    )
    first_rule = Rule.objects.create(
        condition=condition,
        template_id=template.id,
    )
    predicate = Predicate.objects.create(
        rule=first_rule,
        operator=PredicateOperator.EQUAL,
        field_type=FieldType.TEXT,
        field='hero-1',
        value=old_user.id,
    )

    # act
    response = api_client.post(
        '/accounts/users/reassign',
        data={
            'old_user': old_user.id,
            'new_user': new_user.id,
        }
    )

    # assert
    first_rule.refresh_from_db()
    predicate.refresh_from_db()
    assert response.status_code == 204
    assert first_rule.predicates.count() == 1
    assert predicate.value == str(old_user.id)
