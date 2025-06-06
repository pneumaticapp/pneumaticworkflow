# Generated by Django 2.2 on 2023-08-25 15:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0108_account_tmp_subscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='billing_period',
            field=models.CharField(choices=[('day', 'day'), ('week', 'week'), ('month', 'month'), ('year', 'year')], default=None, max_length=255, null=True),
        ),
        migrations.RunSQL("""
            UPDATE accounts_account
            SET billing_period = 'month'
            WHERE billing_plan != 'free' 
              AND plan_expiration IS NOT NULL;
        """)
    ]
