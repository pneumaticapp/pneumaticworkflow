from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0112_data_migration_create_drafts_for_all'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                UPDATE processes_fieldtemplate ft
                  SET task_id = toutput.task_id FROM (
                    SELECT
                      id,
                      task_id
                    FROM processes_taskworkflowoutput
                    WHERE is_deleted IS FALSE
                  ) toutput 
                  WHERE ft.task_output_id = toutput.id AND
                  ft.task_id IS NULL
            """
        )
    ]
