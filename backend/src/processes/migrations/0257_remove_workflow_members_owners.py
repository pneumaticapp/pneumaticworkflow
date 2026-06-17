"""Remove legacy M2M fields members and owners from Workflow.

These fields are fully replaced by Guardian object-level permissions:
  - view_workflow  (replaces members M2M)
  - manage_workflow (replaces owners M2M)

Data was migrated in migration 0256_populate_guardian_workflow_permissions.
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0256_populate_guardian_workflow_permissions'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='workflow',
            name='members',
        ),
        migrations.RemoveField(
            model_name='workflow',
            name='owners',
        ),
    ]
