from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0145_apikey_secure_storage'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_ai',
            field=models.BooleanField(default=False),
        ),
    ]
