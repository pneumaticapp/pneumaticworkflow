from django.db import migrations


def drop_aborted_processes_events(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('processes', '0042_auto_20200702_2146'),
    ]

    operations = [
        migrations.RunPython(drop_aborted_processes_events, reverse_code=migrations.RunPython.noop)
    ]
