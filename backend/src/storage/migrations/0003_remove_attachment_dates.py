from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_migrate_file_attachments'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attachment',
            name='date_created',
        ),
        migrations.RemoveField(
            model_name='attachment',
            name='date_updated',
        ),
    ]
