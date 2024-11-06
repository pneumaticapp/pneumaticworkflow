# Generated by Django 2.2.28 on 2022-05-24 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='device',
            name='token',
            field=models.TextField(),
        ),
        migrations.AddConstraint(
            model_name='device',
            constraint=models.UniqueConstraint(condition=models.Q(is_deleted=False), fields=('token',), name='device_token_unique'),
        ),
    ]