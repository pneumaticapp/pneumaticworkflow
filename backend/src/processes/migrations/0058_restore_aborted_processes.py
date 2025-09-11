from django.db import migrations


def restore_aborted_processes(apps, schema_editor):
    process_model = apps.get_model('processes', 'Process')
    process_model.objects.raw(
        'UPDATE processes_process SET is_deleted = FALSE WHERE status = 2',
    )


class Migration(migrations.Migration):
    dependencies = [
        ('processes', '0057_auto_20200825_1400'),
    ]

    operations = [
        migrations.RunPython(restore_aborted_processes, reverse_code=migrations.RunPython.noop)
    ]
