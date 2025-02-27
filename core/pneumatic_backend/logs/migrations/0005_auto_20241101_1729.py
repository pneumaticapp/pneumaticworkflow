# Generated by Django 2.2 on 2024-11-01 17:29

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0004_auto_20240820_1953'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountevent',
            name='account',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='accounts.Account'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='accountevent',
            name='event_type',
            field=models.CharField(choices=[('api', 'api'), ('databus', 'databus'), ('webhook', 'webhook')], default='api', max_length=100),
        ),
    ]
