"""
Migration 0145: APIKey secure storage.

Changes OneToOneField to ForeignKey, adds prefix, key_hash, cache_token,
date_created, expires_at, last_used_at, is_active fields.
Migrates existing raw keys to hashed storage, then removes the raw key field.
"""

import hashlib

from django.conf import settings
from django.db import migrations, models
from django.utils.encoding import force_bytes
from django.utils import timezone


def _encrypt_token(token: str) -> str:
    """Replicate PneumaticToken.encrypt() without importing the class."""
    encrypted = hashlib.pbkdf2_hmac(
        'sha256',
        token.encode(),
        force_bytes(settings.SECRET_KEY),
        settings.AUTH_TOKEN_ITERATIONS,
    )
    return encrypted.hex()


# Rule bypass justification:
# The `_encrypt_token` function uses pbkdf2_hmac and settings.SECRET_KEY,
# which cannot be easily replicated in raw SQL. Therefore, RunPython is used here
# instead of migrations.RunSQL.
def migrate_api_keys_forward(apps, schema_editor):
    APIKey = apps.get_model('accounts', 'APIKey')
    batch = []
    for api_key in APIKey.objects.filter(
        key__isnull=False,
    ).exclude(key=''):
        raw_key = api_key.key
        api_key.key_hash = hashlib.sha256(
            raw_key.encode()
        ).hexdigest()
        api_key.prefix = raw_key[:16] if len(raw_key) >= 16 else raw_key
        api_key.cache_token = _encrypt_token(raw_key)
        api_key.date_created = timezone.now()
        batch.append(api_key)

    if batch:
        APIKey.objects.bulk_update(
            batch,
            fields=['key_hash', 'prefix', 'cache_token', 'date_created'],
            batch_size=1000,
        )


def migrate_api_keys_reverse(apps, schema_editor):
    """No-op: cannot restore raw keys from hashes."""
    pass


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

        # 2. Add new secure storage fields
        migrations.AddField(
            model_name='apikey',
            name='prefix',
            field=models.CharField(
                db_index=True,
                default='',
                max_length=16,
            ),
        ),
        migrations.AddField(
            model_name='apikey',
            name='key_hash',
            field=models.CharField(
                default='',
                max_length=128,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name='apikey',
            name='cache_token',
            field=models.CharField(
                blank=True,
                default='',
                help_text=(
                    'Encrypted token for cache invalidation on revoke'
                ),
                max_length=128,
            ),
        ),
        migrations.AddField(
            model_name='apikey',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, null=True),
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

        # 3. Make old 'key' field nullable for data migration
        migrations.AlterField(
            model_name='apikey',
            name='key',
            field=models.CharField(
                blank=True,
                max_length=200,
                null=True,
            ),
        ),

        # 4. Migrate existing raw keys to hashed storage
        migrations.RunPython(
            migrate_api_keys_forward,
            reverse_code=migrate_api_keys_reverse,
        ),

        # 5. Remove old raw key field
        migrations.RemoveField(
            model_name='apikey',
            name='key',
        ),
    ]
