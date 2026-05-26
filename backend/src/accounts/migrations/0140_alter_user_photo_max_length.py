from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0139_remove_account_external_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='photo',
            field=models.URLField(blank=True, max_length=2048, null=True),
        ),
    ]
