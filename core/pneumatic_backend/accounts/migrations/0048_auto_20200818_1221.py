# Generated by Django 2.2.15 on 2020-08-18 12:21

from django.db import migrations, models
import django.db.models.deletion
from pneumatic_backend.generics.mixins.models import SoftDeleteMixin


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0047_user_last_digest_send_time'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccountWorkflowTemplates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('is_workflow_added', models.BooleanField(default=False)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
                ('workflow_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='processes.WorkflowTemplate')),
            ],
            options={
                'abstract': False,
            },
            bases=(SoftDeleteMixin, models.Model),
        ),
        migrations.AddField(
            model_name='account',
            name='templates',
            field=models.ManyToManyField(related_name='account_workflow_templates', through='accounts.AccountWorkflowTemplates', to='processes.WorkflowTemplate'),
        ),
    ]