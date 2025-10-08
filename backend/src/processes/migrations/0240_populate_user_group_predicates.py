from django.db import migrations


class Migration(migrations.Migration):
    """ Fills the user field in predicate and predicatetemplate
        models based on the Value field, which contains user.id,
        for entries with Field_type = 'User' """
    dependencies = [
        ('processes', '0239_auto_20250704_1507'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            UPDATE processes_predicatetemplate AS ppt
            SET user_id = au.id
            FROM accounts_user au
            WHERE ppt.field_type = 'user'
              AND ppt.value ~ '^[0-9]+$' 
              AND au.id = CAST(ppt.value AS INTEGER) 
              AND au.is_deleted = false;
            """
        ),

        migrations.RunSQL(
            sql="""
            UPDATE processes_predicate AS pp
            SET user_id = au.id
            FROM accounts_user au
            WHERE pp.field_type = 'user'
              AND pp.value ~ '^[0-9]+$' 
              AND au.id = CAST(pp.value AS INTEGER) 
              AND au.is_deleted = false;
            """
        )
    ]
