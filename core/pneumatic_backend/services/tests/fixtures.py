from django.utils import timezone

from pneumatic_backend.accounts.enums import UserStatus
from pneumatic_backend.accounts.models import Account, UserInvite, User
from pneumatic_backend.processes.models import (
    Workflow,
    Task,
    Template,
    Kickoff,
    FieldTemplate,
    TaskTemplate,
)
from pneumatic_backend.processes.enums import FieldType


def create_test_user(email='test@penumatic.app'):
    account = Account.objects.create(name='Test Company')
    user = User.objects.create(
        account=account,
        email=email,
        phone='79999999999',
        is_admin=True,
        is_account_owner=True,
        first_name='John',
        last_name='CEEEENAAA',
    )
    UserInvite.objects.create(
        email=email,
        account=account,
        invited_user=user,
    )
    return user


def create_invited_user(user, email='test1@pneumatic.app'):
    invited_user = User.objects.create(
        account=user.account,
        email=email,
        phone='79999999999',
        status=UserStatus.INVITED,
    )
    UserInvite.objects.create(
        email=email,
        account=user.account,
        invited_by=user,
        invited_user=invited_user,
    )
    return invited_user


def create_test_template(account, user=None):
    template = Template.objects.create(
        name='Test workflow',
        account=account,
        description='Test desc',
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
    if user:
        template.template_owners.add(user.id)
    for i in range(1, 4):
        task_template = TaskTemplate.objects.create(
            account=account,
            name='Test',
            number=i,
            template=template,
            description=(
                'First line{{%s}}\nSecond line' % kickoff_field.api_name,
            )
        )
        if user:
            task_template.add_raw_performer(user)
    return template


def create_test_workflow(account, user=None):
    template = create_test_template(account, user)
    workflow = Workflow.objects.create(
        name=template.name,
        account=account,
        template=template,
        tasks_count=template.tasks_count,
        status_updated=timezone.now(),
        workflow_starter=user,
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
    return workflow
