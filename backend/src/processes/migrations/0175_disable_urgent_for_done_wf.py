from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('processes', '0174_systemworkflowkickoffdata'),
    ]

    operations = [
        migrations.RunSQL("""
            UPDATE processes_task
            SET is_urgent=FALSE FROM
            (
                SELECT pt.id
                FROM processes_task pt
                  INNER JOIN processes_workflow pw
                    ON pw.id = pt.workflow_id
                WHERE 
                  pw.is_deleted IS FALSE
                  AND pt.is_deleted is FALSE
                  AND pw.status = 1
                  AND pw.is_urgent IS TRUE
                  AND pt.is_urgent IS TRUE
            ) done_task
            WHERE processes_task.id = done_task.id """
        ),
        migrations.RunSQL("""
            UPDATE processes_workflow
            SET is_urgent=FALSE
            WHERE is_deleted IS FALSE
              AND is_urgent IS TRUE
              AND status = 1
        """)
    ]
