# Generated by Django 2.2 on 2023-07-24 13:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0008_auto_20230713_1206'),
    ]

    operations = [
        migrations.AddField(
            model_name='price',
            name='min_quantity',
            field=models.PositiveIntegerField(default=0, help_text='minimum quantity, must be less then the "max_quantity"'),
            preserve_default=False,
        ),
    ]
