from django.db import migrations, models

from src.ai.crypto import decrypt_api_key, encrypt_api_key


def encrypt_existing_keys(apps, schema_editor):
    AIProviderConnection = apps.get_model('ai', 'AIProviderConnection')
    for connection in AIProviderConnection.objects.all().iterator():
        encrypted = encrypt_api_key(connection.api_key_encrypted)
        if encrypted != connection.api_key_encrypted:
            connection.api_key_encrypted = encrypted
            connection.save(update_fields=['api_key_encrypted'])


def decrypt_existing_keys(apps, schema_editor):
    AIProviderConnection = apps.get_model('ai', 'AIProviderConnection')
    for connection in AIProviderConnection.objects.all().iterator():
        decrypted = decrypt_api_key(connection.api_key_encrypted)
        if decrypted != connection.api_key_encrypted:
            connection.api_key_encrypted = decrypted
            connection.save(update_fields=['api_key_encrypted'])


class Migration(migrations.Migration):

    dependencies = [
        ('ai', '0004_auto_20260722_1257'),
    ]

    operations = [
        migrations.RenameField(
            model_name='aiproviderconnection',
            old_name='api_key',
            new_name='api_key_encrypted',
        ),
        migrations.AlterField(
            model_name='aiproviderconnection',
            name='api_key_encrypted',
            field=models.TextField(),
        ),
        migrations.RunPython(
            encrypt_existing_keys,
            decrypt_existing_keys,
        ),
    ]
