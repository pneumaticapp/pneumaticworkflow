from django.db import migrations


def update_attachment_permission(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')

    try:
        content_type = ContentType.objects.get(
            app_label='storage',
            model='attachment',
        )
    except ContentType.DoesNotExist:
        return

    Permission.objects.filter(
        content_type=content_type,
        codename='view_file_attachment',
    ).update(
        codename='view_attachment',
        name='Can view attachment',
    )


def reverse_update_attachment_permission(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    Permission = apps.get_model('auth', 'Permission')

    try:
        content_type = ContentType.objects.get(
            app_label='storage',
            model='attachment',
        )
    except ContentType.DoesNotExist:
        return

    Permission.objects.filter(
        content_type=content_type,
        codename='view_attachment',
    ).update(
        codename='view_file_attachment',
        name='Can view file attachment',
    )


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0003_remove_attachment_dates'),
    ]

    operations = [
        migrations.RunPython(
            update_attachment_permission,
            reverse_update_attachment_permission,
        ),
    ]
