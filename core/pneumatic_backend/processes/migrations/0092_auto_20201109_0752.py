# Generated by Django 2.2.16 on 2020-11-09 07:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0091_auto_20201102_1323'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldtemplate',
            name='name',
            field=models.CharField(max_length=120),
        ),
        migrations.AlterField(
            model_name='taskfield',
            name='name',
            field=models.CharField(max_length=120),
        ),
    ]