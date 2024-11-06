from django.db import migrations


def migrate_generic_workflow(apps, schema_editor):
    pass

class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0048_auto_20200818_1221'),
        ('processes', '0055_auto_20200814_1010'),
        ('processes', '0056_merge_20200817_1211'),
        ('applications', '0010_auto_20200624_1111'),
    ]

    operations = [
        migrations.RunPython(migrate_generic_workflow, reverse_code=migrations.RunPython.noop)
    ]
