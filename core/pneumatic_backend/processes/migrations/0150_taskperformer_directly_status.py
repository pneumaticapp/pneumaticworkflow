# Generated by Django 2.2.24 on 2022-01-11 11:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0149_auto_20211124_1630'),
    ]

    operations = [
        migrations.AddField(
            model_name='taskperformer',
            name='directly_status',
            field=models.IntegerField(choices=[(0, 'no status'), (1, 'deleted'), (2, 'created')], default=0),
        ),
    ]
