from django.db import migrations


def fill_status_updated_field(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('processes', '0052_process_status_updated'),
    ]

    operations = [
        migrations.RunPython(fill_status_updated_field, reverse_code=migrations.RunPython.noop)
    ]
