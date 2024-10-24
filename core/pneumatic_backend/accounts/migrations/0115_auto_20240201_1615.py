# Generated by Django 2.2 on 2024-02-01 16:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0114_contact_account'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='billing_sync',
            field=models.BooleanField(default=True, verbose_name='Stripe synchronization'),
        ),
        migrations.AlterField(
            model_name='account',
            name='trial_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='account',
            name='trial_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
