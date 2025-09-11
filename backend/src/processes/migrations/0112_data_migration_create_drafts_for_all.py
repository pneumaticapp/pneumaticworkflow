from django.db import migrations


def forwards(apps, schema_editor):
    pass

def backwards(*args, **kwards):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0111_data_migration_drafts'),
    ]

    operations = [
        migrations.RunPython(
            code=forwards,
            reverse_code=backwards,
            atomic=True
        )
    ]
