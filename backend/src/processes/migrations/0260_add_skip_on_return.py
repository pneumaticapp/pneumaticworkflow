from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0259_populate_fieldset_title_from_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='skip_on_return',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='tasktemplate',
            name='skip_on_return',
            field=models.BooleanField(default=False),
        ),
    ]
