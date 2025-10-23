# Generated manually for renaming UserGroup duplicates before adding unique constraint

from django.db import migrations


def rename_usergroup_duplicates(apps, schema_editor):
    UserGroup = apps.get_model('accounts', 'UserGroup')
    duplicates_query = """
        SELECT 
            name, 
            account_id,
            array_agg(id ORDER BY id) as ids
        FROM accounts_usergroup 
        WHERE is_deleted = FALSE
        GROUP BY name, account_id 
        HAVING COUNT(*) > 1
    """
    
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute(duplicates_query)
        duplicates = cursor.fetchall()
        
        for name, account_id, ids in duplicates:
            ids_to_rename = ids[1:]
            if ids_to_rename:
                for i, group_id in enumerate(ids_to_rename, start=1):
                    new_name = generate_unique_name(
                        UserGroup, name, account_id, i
                    )
                    UserGroup.objects.filter(id=group_id).update(name=new_name)



def generate_unique_name(UserGroup, base_name, account_id, start_suffix=1):
    suffix = start_suffix
    max_name_length = 255
    
    while True:
        new_name = f"{base_name} {suffix}"
        if len(new_name) > max_name_length:
            available_length = max_name_length - len(f" {suffix}")
            truncated_base = base_name[:available_length]
            new_name = f"{truncated_base} {suffix}"
        exists = UserGroup.objects.filter(
            name=new_name,
            account_id=account_id,
            is_deleted=False
        ).exists()
        
        if not exists:
            return new_name
        suffix += 1
        if suffix > 1000:
            import time
            timestamp_suffix = int(time.time() * 1000) % 100000
            new_name = f"{base_name[:240]} {timestamp_suffix}"
            return new_name


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0133_account_bucket_is_public'),
    ]

    operations = [
        migrations.RunPython(
            rename_usergroup_duplicates,
            reverse_code=migrations.RunPython.noop
        ),
    ]
