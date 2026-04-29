# Generated manually for hierarchical approval workflow

import django.db.models.deletion
from django.db import migrations, models
import src.generics.mixins.models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0249_auto_20260403_1221'),
    ]

    operations = [
        migrations.CreateModel(
            name='TaskTemplateHierarchyConfig',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('task_template', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hierarchy_config', to='processes.TaskTemplate')),
                ('max_depth', models.PositiveIntegerField(blank=True, help_text='Maximum number of hierarchy levels. NULL means unlimited (up to system limit).', null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
            ],
            options={
                'ordering': ['id'],
            },
            bases=(src.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
        migrations.CreateModel(
            name='TaskHierarchyContext',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_deleted', models.BooleanField(default=False)),
                ('task', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='hierarchy_context', to='processes.Task')),
                ('base_api_name', models.CharField(help_text='api_name of the original TaskTemplate step. Used to group clones and for frontend mapping.', max_length=200)),
                ('current_depth', models.PositiveIntegerField(help_text='Current depth in the hierarchy chain (1-based).')),
                ('max_depth', models.PositiveIntegerField(blank=True, help_text='Max depth copied from config. NULL means unlimited (up to SYSTEM_MAX_DEPTH).', null=True)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.Account')),
            ],
            options={
                'ordering': ['current_depth'],
            },
            bases=(src.generics.mixins.models.SoftDeleteMixin, models.Model),
        ),
    ]
