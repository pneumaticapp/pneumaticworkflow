# Generated by Django 2.2.15 on 2020-08-25 14:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0056_merge_20200817_1211'),
    ]

    operations = [
        migrations.AlterField(
            model_name='process',
            name='status_updated',
            field=models.DateTimeField(db_index=True),
        ),
    ]
