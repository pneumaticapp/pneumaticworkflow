from datetime import timedelta
from typing import Optional, List
from django.contrib.auth import get_user_model
from django.utils import timezone

from pneumatic_backend.accounts.enums import (
    UserStatus,
    BillingPlanType,
    UserInviteStatus,
)
from pneumatic_backend.accounts.models import (
    Account,
    UserInvite,
    AccountSignupData,
)
from pneumatic_backend.processes.models import (
    Template,
    Kickoff,
    FieldTemplate,
    TaskTemplate,
    Workflow,
    Task,
)
from pneumatic_backend.processes.enums import FieldType
from pneumatic_backend.accounts.models import UserGroup

UserModel = get_user_model()


def create_invited_user(
    user,
    email='test1@pneumatic.app',
    is_admin: bool = True,
    first_name='',
    last_name='',
    status: UserStatus = UserStatus.INVITED
):
    invited_user = UserModel.objects.create(
        account=user.account,
        email=email,
        phone='79999999999',
        status=status,
        is_admin=is_admin,
        first_name=first_name,
        last_name=last_name,
    )
    user_invite = UserInvite(
        email=email,
        account=user.account,
        invited_by=user,
        invited_user=invited_user,
    )
    if status == UserStatus.ACTIVE:
        user_invite.status = UserInviteStatus.ACCEPTED
    else:
        user_invite.status = UserInviteStatus.PENDING
    user_invite.save()
    return invited_user


def create_test_template(
    account,
    template_owners_user=None,
    performer=None,
    is_active=False,
    is_public=False,
    tasks_count=3,
):
    template = Template.objects.create(
        name='Test workflow',
        account=account,
        description='Test desc',
        is_active=is_active,
        is_public=is_public,
        tasks_count=tasks_count
    )
    kickoff = Kickoff.objects.create(
        account_id=account.id,
        template=template,
    )
    kickoff_field = FieldTemplate.objects.create(
        type=FieldType.TEXT,
        name='Past name',
        description='Last description',
        kickoff=kickoff,
        template=template,
    )
    if account.billing_plan == BillingPlanType.FREEMIUM:
        template.template_owners.add(
            *set(account.users.values_list('id', flat=True))
        )
    elif template_owners_user:
        template.template_owners.add(template_owners_user.id)
    if tasks_count:
        for number in range(1, tasks_count+1):
            task_template = TaskTemplate.objects.create(
                account=account,
                name='Test',
                number=number,
                template=template,
                description=(
                    'First line{{%s}}\nSecond line' % kickoff_field.api_name,
                )
            )
            if performer:
                task_template.add_raw_performer(performer)
    return template


def create_test_workflow(
    account: Account,
    user: Optional[UserModel] = None,
    template: Optional[Template] = None,
    tasks_count: int = 3
):
    if template is None:
        template = create_test_template(
            account,
            template_owners_user=user,
            performer=user,
            is_active=True,
            tasks_count=tasks_count
        )
    workflow = Workflow.objects.create(
        workflow_starter=user,
        name=template.name,
        account=account,
        template=template,
        tasks_count=template.tasks_count,
        status_updated=timezone.now(),
    )
    workflow.members.add(
        *set(template.template_owners.values_list('id', flat=True))
    )
    for task_template in template.tasks.all():
        task = Task.objects.create(
            account=workflow.account,
            template_id=task_template.id,
            name=task_template.name,
            number=task_template.number,
            workflow=workflow,
            date_started=timezone.now() if task_template.number == 1 else None,
        )
        task.update_raw_performers_from_task_template(task_template)
        task.update_performers()
        workflow.members.add(*task.performers.all())
    return workflow


def create_test_account(
    name: str = 'Pneumatic',
    plan: BillingPlanType.LITERALS = BillingPlanType.FREEMIUM,
    payment_card_provided: bool = True,
    billing_sync: bool = True
):
    account = Account.objects.create(
        name=name,
        billing_plan=plan,
        billing_sync=billing_sync,
        payment_card_provided=payment_card_provided,
        plan_expiration=(
            timezone.now() + timedelta(days=1)
            if plan in BillingPlanType.PAYMENT_PLANS else
            None
        ),
    )
    AccountSignupData.objects.create(account=account)
    return account


def create_test_user(
    email: str = 'test@penumatic.app',
    is_admin: bool = True,
    is_account_owner: bool = False,
    account: Optional[Account] = None,
    first_name='John',
    last_name='CEEEENAAA',
):
    if account is None:
        account = create_test_account()
    invited_user = UserModel.objects.create(
        account=account,
        email=email,
        phone='79999999999',
        is_admin=is_admin,
        is_account_owner=is_account_owner,
        first_name=first_name,
        last_name=last_name,
    )
    if not is_account_owner:
        UserInvite.objects.create(
            email=email,
            account=account,
            invited_user=invited_user,
        )
    return invited_user


def create_test_owner(
    email='test@penumatic.app',
    account: Optional[Account] = None,
    first_name='John',
    last_name='CEEEENAAA',
):
    if account is None:
        account = create_test_account()
    return UserModel.objects.create(
        account=account,
        email=email,
        phone='79999999999',
        is_admin=True,
        is_account_owner=True,
        first_name=first_name,
        last_name=last_name,
    )


def create_test_group(
    user: UserModel = None,
    name: str = 'Group_test',
    photo: str = None,
    users: Optional[List[UserModel]] = None,
):
    user = user or create_test_user()
    group = UserGroup.objects.create(
        name=name,
        photo=photo,
        account=user.account,
    )
    if users:
        group.users.set(users)
    group.save()
    return group
