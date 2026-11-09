from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0146_user_is_ai'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='language',
            field=models.CharField(
                choices=[
                    ('en', 'English'),
                    ('es', 'Spanish'),
                    ('de', 'German'),
                    ('fr', 'French'),
                    ('ru', 'Russian'),
                    ('ar-sy', 'Arabic (Syria)'),
                ],
                default=settings.LANGUAGE_CODE,
                max_length=10,
            ),
        ),
    ]
