from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0260_auto_20260814_2003'),
    ]

    operations = [
        migrations.AddField(
            model_name='fieldtemplateruleset',
            name='name',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]
