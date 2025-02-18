from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('processes', '0222_auto_20241216_1426'),
    ]
    operations = [
        migrations.RunSQL("""
            INSERT INTO processes_templateowner (is_deleted, api_name, type, user_id, group_id, account_id, template_id)
            SELECT 
                FALSE AS is_deleted,
                'owner-' || substr(md5(random()::text), 0, 10) AS api_name,
                'user' AS type,
                ptto.user_id AS user_id,
                NULL AS group_id,
                au.account_id AS account_id,
                ptto.template_id
            FROM processes_template_template_owners ptto
            JOIN accounts_user au
                ON au.id = ptto.user_id
            LEFT JOIN processes_templateowner pto
                ON pto.template_id = ptto.template_id
                AND pto.user_id = ptto.user_id
            WHERE pto.id IS NULL
        """),
        migrations.RunSQL("DROP TRIGGER IF EXISTS workflow_ins on processes_template"),
        migrations.RunSQL("""
            INSERT INTO processes_workflow_owners (workflow_id, user_id)
            SELECT w.id, tto.user_id
            FROM processes_template t
            JOIN processes_workflow w ON t.id = w.template_id
            JOIN processes_template_template_owners tto ON t.id = tto.template_id;
        """),
    ]
