from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0157_auto_20220420_1243'),
    ]

    operations = [
        migrations.RunPython(
            code=migrations.RunPython.noop,
            reverse_code=migrations.RunPython.noop
        ),
    ]
