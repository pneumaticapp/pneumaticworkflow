"""Add Guardian custom permissions (view_workflow, manage_workflow) to
Workflow model.

Uses RunPython with get_or_create to safely create Permission rows.
This avoids the Django 2.x bug where AlterModelOptions + post_migrate
create_permissions can cause duplicate key violations on test DB setup.
"""

from django.db import migrations


def create_workflow_permissions(apps, schema_editor):
    """Create custom permissions for Guardian object-level access control."""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')
    Workflow = apps.get_model('processes', 'Workflow')

    ct, _ = ContentType.objects.get_or_create(
        app_label='processes',
        model='workflow',
    )

    Permission.objects.get_or_create(
        codename='view_workflow',
        content_type=ct,
        defaults={'name': 'Can view workflow'},
    )
    Permission.objects.get_or_create(
        codename='manage_workflow',
        content_type=ct,
        defaults={'name': 'Can manage workflow lifecycle'},
    )


def remove_workflow_permissions(apps, schema_editor):
    Permission = apps.get_model('auth', 'Permission')
    ContentType = apps.get_model('contenttypes', 'ContentType')
    ct = ContentType.objects.filter(
        app_label='processes',
        model='workflow',
    ).first()
    if ct:
        Permission.objects.filter(
            codename__in=('view_workflow', 'manage_workflow'),
            content_type=ct,
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0254_add_fileattachment_fields'),
        ('contenttypes', '0002_remove_content_type_name'),
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='workflow',
            options={
                'ordering': ['-date_created'],
                'permissions': [
                    ('view_workflow', 'Can view workflow'),
                    ('manage_workflow', 'Can manage workflow lifecycle'),
                ],
            },
        ),
        migrations.RunPython(
            create_workflow_permissions,
            remove_workflow_permissions,
        ),
    ]
