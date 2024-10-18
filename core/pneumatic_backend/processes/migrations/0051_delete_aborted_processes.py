from django.db import migrations


def delete_aborted_processes(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('processes', '0050_merge_20200731_1230'),
    ]

    operations = [
        migrations.RunPython(delete_aborted_processes, reverse_code=migrations.RunPython.noop)
    ]
