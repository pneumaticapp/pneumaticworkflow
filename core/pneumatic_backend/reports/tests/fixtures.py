from datetime import timedelta
from typing import Optional

from django.contrib.auth import get_user_model
from django.utils import timezone

from pneumatic_backend.accounts.enums import BillingPlanType
from pneumatic_backend.accounts.models import (
    Account,
    UserInvite,
    AccountSignupData,
)
from pneumatic_backend.processes.models import (
    Template,
    TaskTemplate,
    Workflow,
    Task,
)


UserModel = get_user_model()


def create_test_account(
    name: str = 'Test Company',
    plan: BillingPlanType = BillingPlanType.FREEMIUM,
    payment_card_provided: bool = True,
):
    account = Account.objects.create(
        name=name,
        billing_plan=plan,
        plan_expiration=(
            timezone.now() + timedelta(days=1)
            if plan in BillingPlanType.PAYMENT_PLANS else
            None
        ),
        payment_card_provided=payment_card_provided,
    )
    AccountSignupData.objects.create(account=account)
    return account


def create_test_user(
    email: str = 'test@pneumatic.app',
    is_admin: bool = True,
    is_account_owner: bool = False,
    account: Optional[Account] = None,
):
    if account is None:
        account = create_test_account()
    return UserModel.objects.create(
        account=account,
        email=email,
        phone='79999999999',
        is_admin=is_admin,
        is_account_owner=is_account_owner
    )


def create_invited_user(user, email='test1@pneumatic.app'):
    invited_user = UserModel.objects.create(
        account=user.account,
        email=email,
        phone='79999999999',
    )
    UserInvite.objects.create(
        email=email,
        account=user.account,
        invited_user=invited_user,
    )
    return invited_user


def create_test_template(
    user,
    is_active=False,
    tasks_count: int = 3,
    name: str = 'Test workflow'
):
    account = user.account
    template = Template.objects.create(
        name=name,
        account=account,
        description='Test desc',
        is_active=is_active,
        tasks_count=tasks_count
    )
    task_data = {
        'account': account,
        'name': 'Test',
        'template': template
    }
    if account.billing_plan == BillingPlanType.FREEMIUM:
        template.template_owners.set(
            account.get_user_ids(include_invited=True)
        )
    else:
        template.template_owners.add(user.id)

    if tasks_count:
        for number in range(1, tasks_count + 1):
            task_data['number'] = number
            task_template = TaskTemplate.objects.create(**task_data)
            task_template.add_raw_performer(user)
    return template


def create_test_workflow(
    user,
    template: Template = None,
    tasks_count: int = 3,
):
    now = timezone.now()
    if not template:
        template = create_test_template(user, tasks_count=tasks_count)
    workflow = Workflow.objects.create(
        name=template.name,
        description=template.description,
        account_id=template.account_id,
        tasks_count=template.tasks_count,
        template=template,
        status_updated=now,
        workflow_starter=user,
    )
    workflow.members.add(
        *set(template.template_owners.values_list('id', flat=True))
    )
    for task_template in template.tasks.all():
        date_started = now if task_template.number == 1 else None
        task = Task.objects.create(
            account=workflow.account,
            template_id=task_template.id,
            name=task_template.name,
            description=task_template.description,
            workflow=workflow,
            number=task_template.number,
            date_started=date_started,
            date_first_started=date_started,
            require_completion_by_all=task_template.require_completion_by_all,
        )
        task.update_raw_performers_from_task_template(task_template)
        task.update_performers()
        workflow.members.add(*task.performers.all())

    return workflow
