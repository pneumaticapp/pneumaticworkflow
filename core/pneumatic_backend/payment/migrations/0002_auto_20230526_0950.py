# Generated by Django 2.2 on 2023-05-26 09:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='price',
            name='billing_period',
            field=models.CharField(blank=True, choices=[('daily', 'daily'), ('weekly', 'weekly'), ('monthly', 'monthly'), ('yearly', 'yearly')], help_text='For "Recurring" price type only', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='price',
            name='trial_days',
            field=models.PositiveIntegerField(blank=True, help_text='For "Recurring" price type only', null=True),
        ),
    ]
