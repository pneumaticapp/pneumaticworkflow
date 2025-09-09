from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0003_auto_20240820_1952'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountevent',
            name='contractor',
            field=models.CharField(blank=True, max_length=255, null=True),
        )
    ]
