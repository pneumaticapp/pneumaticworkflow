from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0100_auto_20201218_1046'),
    ]

    operations = [
        migrations.RunSQL('UPDATE processes_task SET name_template = name;')
    ]
