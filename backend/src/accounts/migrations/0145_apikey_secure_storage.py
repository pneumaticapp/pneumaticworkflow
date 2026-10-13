"""
Migration 0145: APIKey secure storage.

Changes OneToOneField to ForeignKey, renames key→token,
adds date_created, expires_at, last_used_at, is_active fields.
"""

import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0144_auto_20260609_1910'),
    ]

    operations = [
        # 1. Convert OneToOneField to ForeignKey
        migrations.AlterField(
            model_name='apikey',
            name='user',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name='api_keys',
                to=settings.AUTH_USER_MODEL,
            ),
        ),

        # 2. Rename key → token (stores raw key)
        migrations.RenameField(
            model_name='apikey',
            old_name='key',
            new_name='token',
        ),

        # 3. Alter token field: max_length=64, db_index=True
        migrations.AlterField(
            model_name='apikey',
            name='token',
            field=models.CharField(
                max_length=64,
                db_index=True,
            ),
        ),

        # 4. Add new fields
        migrations.AddField(
            model_name='apikey',
            name='date_created',
            field=models.DateTimeField(
                auto_now_add=True,
                default=django.utils.timezone.now,
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='apikey',
            name='expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='apikey',
            name='last_used_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='apikey',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
