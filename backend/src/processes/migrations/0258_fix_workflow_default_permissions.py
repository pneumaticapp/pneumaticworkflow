"""Exclude 'view' from Workflow.default_permissions to avoid
clash with our custom 'view_workflow' permission (Django auth.E005).

Django 2.1+ auto-generates view_<model> permissions. Our custom
'view_workflow' clashes with the auto-generated one. Setting
default_permissions = ('add', 'change', 'delete') prevents this.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0257_remove_workflow_members_owners'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='workflow',
            options={
                'default_permissions': ('add', 'change', 'delete'),
                'ordering': ['-date_created'],
                'permissions': [
                    ('view_workflow', 'Can view workflow'),
                    (
                        'manage_workflow',
                        'Can manage workflow lifecycle',
                    ),
                ],
            },
        ),
    ]
