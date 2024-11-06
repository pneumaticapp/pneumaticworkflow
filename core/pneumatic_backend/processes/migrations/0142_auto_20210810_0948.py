# Generated by Django 2.2.24 on 2021-08-10 09:48

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def forward(apps, schema_editor):
    Workflow = apps.get_model('processes', 'Workflow')
    for workflow in Workflow.objects.filter(is_deleted=False):
        members = (
            set(workflow.template.template_owners.values_list(
                'id',
                flat=True
            ))
            if workflow.template else set()
        )
        for task in workflow.tasks.filter(is_deleted=False):
            performers = set(task.responsible.values_list('id', flat=True))
            members = members.union(performers)
        workflow.members.set(members)


def backward(*args, **kwargs):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('processes', '0141_auto_20210802_1139'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflow',
            name='members',
            field=models.ManyToManyField(related_name='workflows', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='workflow',
            name='workflow_starter',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='started_workflow', to=settings.AUTH_USER_MODEL),
        ),
        migrations.RunPython(code=forward, reverse_code=backward),
    ]