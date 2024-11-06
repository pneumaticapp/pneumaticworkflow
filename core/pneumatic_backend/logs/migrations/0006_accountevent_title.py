# Generated by Django 2.2 on 2024-11-04 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('logs', '0005_auto_20241101_1729'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountevent',
            name='title',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
        migrations.RunSQL("""
            UPDATE logs_accountevent SET title=path WHERE title IS NULL
        """)
    ]